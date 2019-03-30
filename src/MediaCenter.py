#!/usr/bin/python
# encoding: utf-8
#
# Copyright (C) 2011 by Coolman & Swiss-MAD
# Copyright (C) 2018-2019 by dream-alpha
#
# In case of reuse of this source code please do not remove this copyright.
#
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	For more information on the GNU General Public License see:
#	<http://www.gnu.org/licenses/>.
#

import os
from __init__ import _
from time import time
from Components.config import config
from Components.ActionMap import HelpableActionMap
from Components.Pixmap import Pixmap
from Components.Label import Label
from enigma import iSubtitleType_ENUMS
from Screens.Screen import Screen
from Screens.AudioSelection import SUB_FORMATS, GST_SUB_FORMATS
from Screens.InfoBarGenerics import InfoBarSubtitleSupport
from Screens.InfoBar import InfoBar
from Screens.MessageBox import MessageBox
from Screens.HelpMenu import HelpableScreen
from Tools.ISO639 import LanguageCodes as langC
from Components.Language import language
from Tools.Notifications import AddPopup
from ServiceReference import ServiceReference
from DelayedFunction import DelayedFunction
from CutListUtils import secondsToPts, backupCutsFile
from InfoBarSupport import InfoBarSupport, InfoBarTimeshift
from Components.Sources.MVCCurrentService import MVCCurrentService
from ServiceCenter import ServiceCenter
from ServiceUtils import sidDVB
from RecordingUtils import isRecording, getRecording
from MovieInfoEPG import MovieInfoEPG
from MovieCover import MovieCover

class MVCMoviePlayerSummary(Screen, object):

	def __init__(self, session, parent):
		Screen.__init__(self, session, parent)
		self.skinName = "MVCMoviePlayerSummary"
		self["Service"] = MVCCurrentService(session.nav, parent)


class MediaCenter(Screen, HelpableScreen, MovieCover, InfoBarTimeshift, InfoBarSupport, object):

	ENABLE_RESUME_SUPPORT = True
	ALLOW_SUSPEND = True

	def __init__(self, session, service, cover):

		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		InfoBarTimeshift.__init__(self)
		InfoBarSupport.__init__(self)
		MovieCover.__init__(self)

		self.cover = cover
		self["cover"] = Pixmap()

		self.selected_subtitle = None
		self.execing = None

		self.skinName = "MVCMediaCenter"

		self.serviceHandler = ServiceCenter.getInstance()

		self["Service"] = MVCCurrentService(session.nav, self)

		self["actions"] = HelpableActionMap(
			self,
			"MVCPlayerActions",
			{
				"MVCEXIT": (self.leavePlayer, _("Stop playback"))
			},
			-1
		)

		self["MenuActions"].prio = 2
		if "TeletextActions" in self:
			self["TeletextActions"].prio = 2
			self["TeletextActions"].setEnabled(True)

		self["NumberActions"].prio = 2

		self["mvc_logo"] = Pixmap()
		self["end"] = Label(_("End"))
		self.skip = -1
		self.service = service
		self.allowPiP = True
		self.allowPiPSwap = False
		self.realSeekLength = None
		self.servicelist = InfoBar.instance.servicelist
		self.lastservice = self.session.nav.getCurrentlyPlayingServiceReference()
		if not self.lastservice:
			self.lastservice = InfoBar.instance.servicelist.servicelist.getCurrent()

		# Dialog Events
		self.onShown.append(self.__onShow)  # Don't use onFirstExecBegin() it will crash
		self.onClose.append(self.__onClose)

	def getCurrentEvent(self):
		return self.service and self.serviceHandler.info(self.service).getEvent()

	def infoMovie(self):
		evt = self.getCurrentEvent()
		if evt:
			self.session.open(MovieInfoEPG, evt, ServiceReference(self.service))

	def __onShow(self):
		self.evEOF()  # begin playback

	def __onClose(self):
		if self.lastservice:
			self.zapToService(self.lastservice)

	def evEOF(self):
		print("MVC-I: MediaCenter: evEOF")
		path = self.service and self.service.getPath()
		if os.path.exists(path):
			self.session.nav.playService(self.service)

			if self.service and self.service.type != sidDVB:
				self.realSeekLength = self.getSeekLength()

			DelayedFunction(50, self.setAudioTrack)
			DelayedFunction(50, self.setSubtitleState, True)

			self["mvc_logo"].show()
			if self.cover:
				if self.showCover(self.service.getPath()):
					self["mvc_logo"].hide()
		else:
			self.session.open(
				MessageBox,
				_("Movie file does not exist.") + "\n" + self.service.getPath(),
				MessageBox.TYPE_ERROR,
				10
			)

	### support functions for converters: MVCServicePosition and MVCRecordingPosition

	def getLength(self):
		length = 0
		if self.service.type == sidDVB:
			__len = self.serviceHandler.info(self.service).getLength()
			length = secondsToPts(__len + config.recording.margin_before.value * 60)
		else:
			# non-ts movies
			seek = self.getSeek()
			if seek is not None:
				__len = seek.getLength()
				#print("MVC: MediaCenter: getLength: seek.getLength(): %s" % __len)
				if not __len[0]:
					length = __len[1]
		return length

	def getRecordingPosition(self):
		position = 0
		path = self.service.getPath()
		if path:
			recording = getRecording(path, True)
			if recording:
				begin, _end, _service_ref = recording
				position = secondsToPts(time() - begin)
			else:
				position = self.getPosition()
		return position

	def getPosition(self):
		position = 0
		seek = self.getSeek()
		if seek is not None:
			pos = seek.getPlayPosition()
			#print("MVC: MediaCenter: getPosition: getPlayPosition(): %s" % pos)
			if not pos[0]:
				position = pos[1]

		if self.skip:
			position = 0
		if self.skip > 0:
			self.skip -= 1
#		#print("MVC: MediaCenter: getPosition: position: %s" % position)
		return position

	### Audio and Subtitles

	def setAudioTrack(self):
		self.skip = 10
		try:
			#print("MVC: MediaCenter: setAudioTrack: audio")
			if not config.MVC.autoaudio.value:
				return
			service = self.session.nav.getCurrentService()
			tracks = service and self.getServiceInterface("audioTracks")
			nTracks = tracks.getNumberOfTracks() if tracks else 0
			if not nTracks:
				return
			index = 0
			trackList = []
			for i in range(nTracks):
				audioInfo = tracks.getTrackInfo(i)
				lang = audioInfo.getLanguage()
				#print("MVC: MediaCenter: setAudioTrack: lang %s" % lang)
				desc = audioInfo.getDescription()
				#print("MVC: MediaCenter: setAudioTrack: desc %s" % desc)
#				audio_type = audioInfo.getType()
				track = index, lang, desc, type
				index += 1
				trackList += [track]
			seltrack = tracks.getCurrentTrack()
			# we need default selected language from image
			# to set the audio track if "config.MVC.autoaudio.value" are not set
			syslang = language.getLanguage()[:2]
			if config.MVC.autoaudio.value:
				audiolang = [config.MVC.audlang1.value, config.MVC.audlang2.value, config.MVC.audlang3.value]
			else:
				audiolang = syslang
			useAc3 = config.MVC.autoaudio_ac3.value	  # mvc has new value, in some images it gives different values for that
			if useAc3:
				matchedAc3 = self.tryAudioTrack(tracks, audiolang, trackList, seltrack, useAc3)
				if matchedAc3:
					return
				matchedMpeg = self.tryAudioTrack(tracks, audiolang, trackList, seltrack, False)
				if matchedMpeg:
					return
				tracks.selectTrack(0)  # fallback to track 1(0)
				return
			else:
				matchedMpeg = self.tryAudioTrack(tracks, audiolang, trackList, seltrack, False)
				if matchedMpeg:
					return
				matchedAc3 = self.tryAudioTrack(tracks, audiolang, trackList, seltrack, useAc3)
				if matchedAc3:
					return
				tracks.selectTrack(0)  # fallback to track 1(0)
			#print("MVC: MediaCenter: setAudioTrack: audio1")
		except Exception as e:
			print("MVC-E: MediaCenter: setAudioTrack: exception: %s" % e)

	def tryAudioTrack(self, tracks, audiolang, trackList, seltrack, useAc3):
		for entry in audiolang:
			entry = langC[entry][0]
			#print("MVC: MediaCenter: tryAudioTrack: audio2")
			for x in trackList:
				try:
					x1val = langC[x[1]][0]
				except Exception:
					x1val = x[1]
				#print(x1val)
				#print("entry %s" % entry)
				#print(x[0])
				#print("seltrack %s" % seltrack)
				#print(x[2])
				#print(x[3])
				if entry == x1val and seltrack == x[0]:
					if useAc3:
						#print("MVC: MediaCenter: tryAudioTrack: audio3")
						if x[3] == 1 or x[2].startswith('AC'):
							#print("MVC: MediaCenter: [MVCPlayer] audio track is current selected track: " + str(x))
							return True
					else:
						#print("MVC: MediaCenter: tryAudioTrack: audio4")
						#print("MVC: MediaCenter: tryAudioTrack: currently selected track: " + str(x))
						return True
				elif entry == x1val and seltrack != x[0]:
					if useAc3:
						#print("MVC: MediaCenter: tryAudioTrack: audio5")
						if x[3] == 1 or x[2].startswith('AC'):
							#print("MVC: MediaCenter: tryAudioTrack: match: " + str(x))
							tracks.selectTrack(x[0])
							return True
					else:
						#print("MVC: MediaCenter: tryAudioTrack: audio6")
						#print("MVC: MediaCenter: tryAudioTrack: match: " + str(x))
						tracks.selectTrack(x[0])
						return True
		return False

	def trySubEnable(self, slist, match):
		for e in slist:
			#print("MVC: MediaCenter: trySubEnable: e: %s" % e)
			#print("MVC: MediaCenter: trySubEnable: match %s" % (langC[match][0]))
			if langC[match][0] == e[2]:
				#print("MVC: MediaCenter: trySubEnable: match: %s" % e)
				if self.selected_subtitle != e[0]:
					self.subtitles_enabled = False
					self.selected_subtitle = e[0]
					self.subtitles_enabled = True
					return True
			else:
				#print("MVC: MediaCenter: trySubEnable: nomatch")
				pass
		return False

	def setSubtitleState(self, enabled):
		try:
			if not config.MVC.autosubs.value or not enabled:
				return

			subs = self.getCurrentServiceSubtitle() if isinstance(self, InfoBarSubtitleSupport) else None
			n = (subs.getNumberOfSubtitleTracks() if subs else 0)
			if n == 0:
				return

			self.sub_format_dict = {}
			self.gstsub_format_dict = {}
			for index, (short, _text, rank) in sorted(SUB_FORMATS.items(), key=lambda x: x[1][2]):
				if rank > 0:
					self.sub_format_dict[index] = short
			for index, (short, _text, rank) in sorted(GST_SUB_FORMATS.items(), key=lambda x: x[1][2]):
				if rank > 0:
					self.gstsub_format_dict[index] = short
			lt = []
			l = []
			for index in range(n):
				info = subs.getSubtitleTrackInfo(index)
				languages = info.getLanguage().split('/')
				#print("MVC: MediaCenter: setSubtitleState: lang %s" % languages)
				iType = info.getType()
				#print("MVC: MediaCenter: setSubtitleState: type %s" % iType)
				if iType == iSubtitleType_ENUMS.GST:
					iType = info.getGstSubtype()
#					codec = self.gstsub_format_dict[iType] if iType in self.gstsub_format_dict else '?'
#				else:
#					codec = self.sub_format_dict[iType] if iType in self.sub_format_dict else '?'
#				#print("MVC: MediaCenter: setSubtitleState: codec %s")
				lt.append((index, (iType == 1 and "DVB" or iType == 2 and "TTX" or "???"), languages))
			if lt:
				#print("MVC: MediaCenter: setSubtitleState: " + str(lt))
				for e in lt:
					l.append((e[0], e[1], e[2][0] in langC and langC[e[2][0]][0] or e[2][0]))
					if l:
						#print("MVC: MediaCenter: setSubtitleState: " + str(l))
						for sublang in [config.MVC.sublang1.value, config.MVC.sublang2.value, config.MVC.sublang3.value]:
							if self.trySubEnable(l, sublang):
								break
		except Exception as e:
			print("MVC-E: MediaCenter: setSubtitleState: exception: %s" % e)

	def leavePlayer(self, reopen=True):
		print("MVC-I: MediaCenter: leavePlayer: %s" % reopen)

		self.setSubtitleState(False)

		if self.service and self.service.type != sidDVB:
			self.updateServiceCutList(self.service)

		if not reopen:
			#print("MVC: MediaCenter: leavePlayer: closed due to EOF")
			if config.MVC.record_eof_zap.value == "1":
				AddPopup(
					_("Zap to live TV of recording"),
					MessageBox.TYPE_INFO,
					3,
					"MVCCloseAllAndZap"
				)

		#print("MVC: MediaCenter: leavePlayer: stopping service")
		self.session.nav.stopService()

		# [Cutlist.Workaround]
		# Always make a backup-copy when recording is running and we stopped the playback
		if self.service and self.service.type == sidDVB:
			path = self.service.getPath()
			if isRecording(path):
				backupCutsFile(path + ".cuts")

			#print("MVC: MediaCenter: leavePlayer: update cuts: " + self.service.getPath())
			#print("MVC: MediaCenter: leavePlayer: cut_list before update: " + str(self.cut_list))
			cut_list = self.reloadCutListFromFile(self.service.getPath())
			print("MVC-I: MediaCenter: leavePlayer: cut_list after  reload: " + str(cut_list))

		self.close(reopen)

	### functions for InfoBarGenerics.py
	# InfoBarShowMovies
	def showMovies(self):
		#print("MVC: MediaCenter: showMovies")
		return

	def doEofInternal(self, playing):
		print("MVC-I: MediaCenter: doEofInternal: playing: %s, self.execing: %s" % (playing, self.execing))
		self.is_closing = True

		if not self.execing:
			return

		timer = self.service and isRecording(self.service.getPath())
		if timer:
			if int(config.MVC.record_eof_zap.value) < 2:
				self.lastservice = timer.service_ref.ref
				print("MVC-I: MediaCenter: doEofInternal: self.lastservice: %s" % (self.lastservice.toString() if self.lastservice else None))
				self.leavePlayer(reopen=False)

		else:
			if self.service.type != sidDVB:
				self.updateServiceCutList(self.service)

	def updateServiceCutList(self, service):
		print("MVC-I: MediaCenter: updateCutList")
		if self.getSeekPlayPosition() == 0:
			if self.realSeekLength:
				self.updateCutList(service.getPath(), self.realSeekLength, self.realSeekLength)
			else:
				self.updateCutList(service.getPath(), self.getSeekLength(), self.getSeekLength())
		else:
			self.updateCutList(service.getPath(), self.getSeekPlayPosition(), self.getSeekLength())
		#print("MVC: MediaCenter: updateCutList: pos: " + str(self.getSeekPlayPosition()) + ", length: " + str(self.getSeekLength()))


	def createSummary(self):
		return MVCMoviePlayerSummary
