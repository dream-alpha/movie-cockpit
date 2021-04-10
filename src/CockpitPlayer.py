#!/usr/bin/python
# coding=utf-8
#
# Copyright (C) 2011 by Coolman & Swiss-MAD
# Copyright (C) 2018-2021 by dream-alpha
#
# In case of reuse of this source code please do not remove this copyright.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# For more information on the GNU General Public License see:
# <http://www.gnu.org/licenses/>.


from Debug import logger
from __init__ import _
from Components.config import config
from Components.ActionMap import HelpableActionMap
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
from DelayTimer import DelayTimer
from CutList import reloadCutList, backupCutList, updateCutList
from InfoBarSupport import InfoBarSupport
from Components.Sources.MVCCurrentService import MVCCurrentService
from ServiceCenter import ServiceCenter
from RecordingUtils import isRecording
from MovieInfoEPG import MovieInfoEPG
from ServiceUtils import SID_DVB


class CockpitPlayerSummary(Screen):

	def __init__(self, session, parent):
		Screen.__init__(self, session, parent)
		self.skinName = "CockpitPlayerSummary"
		self["Service"] = MVCCurrentService(session.nav, parent)


class CockpitPlayer(Screen, HelpableScreen, InfoBarSupport):

	ENABLE_RESUME_SUPPORT = True
	ALLOW_SUSPEND = True

	def __init__(self, session, service):

		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		InfoBarSupport.__init__(self)

		self.selected_subtitle = None
		self.execing = None

		self.skinName = "CockpitPlayer"

		self.serviceHandler = ServiceCenter.getInstance()

		self["Service"] = MVCCurrentService(session.nav, self)

		self["actions"] = HelpableActionMap(
			self,
			"CockpitActions",
			{
				"STOP":		(self.leavePlayer,	_("Stop playback")),
				"EXIT":		(self.leavePlayer,	_("Stop playback")),
				"CHANNELUP":	(self.skipForward,	_("Skip forward")),
				"CHANNELDOWN":	(self.skipBackward,	_("Skip backward")),
			},
			-2
		)

		self["NumberActions"].prio = 2

		self.service = service
		self.allowPiP = True
		self.allowPiPSwap = False
		self.realSeekLength = None
		self.servicelist = InfoBar.instance.servicelist
		self.last_service = self.session.nav.getCurrentlyPlayingServiceReference()
		if not self.last_service:
			self.last_service = InfoBar.instance.servicelist.servicelist.getCurrent()

		self.onShown.append(self.__onShow)
		self.onClose.append(self.__onClose)

	def infoMovie(self):
		event = self.service and self.serviceHandler.info(self.service).getEvent()
		if event:
			self.session.open(MovieInfoEPG, event, ServiceReference(self.service))

	def __onShow(self):
		self.evEOF()  # begin playback

	def __onClose(self):
		if self.last_service:
			self.zapToService(self.last_service)

	def evEOF(self):
		logger.info("...")
		self.session.nav.playService(self.service)

		if self.service and self.service.type != SID_DVB:
			self.realSeekLength = self.getSeekLength()

		DelayTimer(50, self.setAudioTrack)
		DelayTimer(50, self.setSubtitleState, True)

	### Audio and Subtitles

	def setAudioTrack(self):
		try:
			logger.debug("audio")
			if not config.plugins.moviecockpit.autoaudio.value:
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
				logger.debug("lang %s", lang)
				desc = audioInfo.getDescription()
				logger.debug("desc %s", desc)
# 			audio_type = audioInfo.getType()
				track = index, lang, desc, type
				index += 1
				trackList += [track]
			seltrack = tracks.getCurrentTrack()
			# we need default selected language from image
			# to set the audio track if "config.plugins.moviecockpit.autoaudio.value" are not set
			syslang = language.getLanguage()[:2]
			if config.plugins.moviecockpit.autoaudio.value:
				audiolang = [config.plugins.moviecockpit.audlang1.value, config.plugins.moviecockpit.audlang2.value, config.plugins.moviecockpit.audlang3.value]
			else:
				audiolang = syslang
			useAc3 = config.plugins.moviecockpit.autoaudio_ac3.value
			if useAc3:
				matchedAc3 = self.tryAudioTrack(tracks, audiolang, trackList, seltrack, useAc3)
				if matchedAc3:
					return
				matchedMpeg = self.tryAudioTrack(tracks, audiolang, trackList, seltrack, False)
				if matchedMpeg:
					return
				tracks.selectTrack(0)  # fallback to track 1(0)
			else:
				matchedMpeg = self.tryAudioTrack(tracks, audiolang, trackList, seltrack, False)
				if matchedMpeg:
					return
				matchedAc3 = self.tryAudioTrack(tracks, audiolang, trackList, seltrack, useAc3)
				if matchedAc3:
					return
				tracks.selectTrack(0)  # fallback to track 1(0)
			logger.debug("audio1")
		except Exception as e:
			logger.error("exception: %s", e)

	def tryAudioTrack(self, tracks, audiolang, trackList, seltrack, useAc3):
		for entry in audiolang:
			entry = langC[entry][0]
			logger.debug("audio2")
			for x in trackList:
				try:
					x1val = langC[x[1]][0]
				except Exception:
					x1val = x[1]
				logger.debug(x1val)
				logger.debug("entry %s", entry)
				logger.debug(x[0])
				logger.debug("seltrack %s", seltrack)
				logger.debug(x[2])
				logger.debug(x[3])
				if entry == x1val and seltrack == x[0]:
					if useAc3:
						logger.debug("audio3")
						if x[3] == 1 or x[2].startswith('AC'):
							logger.debug("audio track is current selected track: %s", str(x))
							return True
					else:
						logger.debug("audio4")
						logger.debug("currently selected track: %s", str(x))
						return True
				elif entry == x1val and seltrack != x[0]:
					if useAc3:
						logger.debug("audio5")
						if x[3] == 1 or x[2].startswith('AC'):
							logger.debug("match: %s", str(x))
							tracks.selectTrack(x[0])
							return True
					else:
						logger.debug("audio6")
						logger.debug("match: %s", str(x))
						tracks.selectTrack(x[0])
						return True
		return False

	def trySubEnable(self, slist, match):
		for e in slist:
			logger.debug("e: %s", e)
			logger.debug("match %s", langC[match][0])
			if langC[match][0] == e[2]:
				logger.debug("match: %s", e)
				if self.selected_subtitle != e[0]:
					self.subtitles_enabled = False
					self.selected_subtitle = e[0]
					self.subtitles_enabled = True
					return True
			else:
				logger.debug("no match")
		return False

	def setSubtitleState(self, enabled):
		try:
			if not config.plugins.moviecockpit.autosubs.value or not enabled:
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
			alist = []
			for index in range(n):
				info = subs.getSubtitleTrackInfo(index)
				languages = info.getLanguage().split('/')
				logger.debug("lang %s", languages)
				iType = info.getType()
				logger.debug("type %s", iType)
				if iType == iSubtitleType_ENUMS.GST:
					iType = info.getGstSubtype()
# 				codec = self.gstsub_format_dict[iType] if iType in self.gstsub_format_dict else '?'
# 			else:
# 				codec = self.sub_format_dict[iType] if iType in self.sub_format_dict else '?'
# 			logger.debug("codec %s", codec)
				lt.append((index, (iType == 1 and "DVB" or iType == 2 and "TTX" or "???"), languages))
			if lt:
				logger.debug("%s", str(lt))
				for e in lt:
					alist.append((e[0], e[1], e[2][0] in langC and langC[e[2][0]][0] or e[2][0]))
					if alist:
						logger.debug("%s", str(alist))
						for sublang in [config.plugins.moviecockpit.sublang1.value, config.plugins.moviecockpit.sublang2.value, config.plugins.moviecockpit.sublang3.value]:
							if self.trySubEnable(alist, sublang):
								break
		except Exception as e:
			logger.error("exception: %s", e)

	def leavePlayer(self, reopen=True):
		logger.info("reopen: %s", reopen)

		self.setSubtitleState(False)

		if self.service and self.service.type != SID_DVB:
			self.updateCutList(self.service)

		if not reopen:
			logger.debug("closed due to EOF")
			if config.plugins.moviecockpit.record_eof_zap.value == "1":
				AddPopup(
					_("Zap to live TV of recording"),
					MessageBox.TYPE_INFO,
					3,
					"CloseAllAndZap"
				)

		logger.debug("stopping service")
		self.session.nav.stopService()

		# Always make a backup copy when recording is running and we stopped the playback
		if self.service and self.service.type == SID_DVB:
			path = self.service.getPath()
			if isRecording(path):
				backupCutList(path + ".cuts")

			logger.debug("reload cuts: %s", path)
			logger.debug("cut_list before reload: %s", self.cut_list)
			cut_list = reloadCutList(path)
			logger.info("cut_list after reload: %s", cut_list)
		self.close(reopen)

	### functions for InfoBarGenerics.py
	# InfoBarShowMovies
	def showMovies(self):
		logger.info("...")

	def doEofInternal(self, playing):
		logger.info("playing: %s, self.execing: %s", playing, self.execing)
		self.is_closing = True

		if not self.execing:
			return

		timer = self.service and isRecording(self.service.getPath())
		if timer:
			if int(config.plugins.moviecockpit.record_eof_zap.value) < 2:
				self.last_service = timer.service_ref.ref
				logger.info("self.last_service: %s", self.last_service.toString() if self.last_service else None)
				self.leavePlayer(reopen=False)

		else:
			if self.service.type != SID_DVB:
				self.updateCutList(self.service)

	def updateCutList(self, service):
		logger.info("...")
		if self.getSeekPlayPosition() == 0:
			if self.realSeekLength:
				updateCutList(service.getPath(), self.realSeekLength, self.realSeekLength)
			else:
				updateCutList(service.getPath(), self.getSeekLength(), self.getSeekLength())
		else:
			updateCutList(service.getPath(), self.getSeekPlayPosition(), self.getSeekLength())
		logger.debug("pos: %s, length: %s", str(self.getSeekPlayPosition()), str(self.getSeekLength()))

	def createSummary(self):
		return CockpitPlayerSummary
