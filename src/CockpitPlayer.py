#!/usr/bin/python
# coding=utf-8
#
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
from Components.ActionMap import HelpableActionMap
from Screens.Screen import Screen
from Screens.InfoBar import InfoBar
from Screens.HelpMenu import HelpableScreen
from ServiceReference import ServiceReference
from DelayTimer import DelayTimer
from CutList import reloadCutList, backupCutList, updateCutList
from CutListUtils import secondsToPts
from InfoBarSupport import InfoBarSupport
from Components.Sources.MVCCurrentService import MVCCurrentService
from ServiceCenter import ServiceCenter
from RecordingUtils import isRecording
from MovieInfoEPG import MovieInfoEPG
from ServiceUtils import SID_DVB
from CockpitPlayerAudio import CockpitPlayerAudio
from CockpitPlayerSubtitles import CockpitPlayerSubtitles


class CockpitPlayerSummary(Screen):

	def __init__(self, session, parent):
		Screen.__init__(self, session, parent)
		self.skinName = "CockpitPlayerSummary"
		self["Service"] = MVCCurrentService(session.nav, parent)


class CockpitPlayer(Screen, HelpableScreen, InfoBarSupport, CockpitPlayerAudio, CockpitPlayerSubtitles):

	ENABLE_RESUME_SUPPORT = True
	ALLOW_SUSPEND = True

	def __init__(self, session, service):

		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		InfoBarSupport.__init__(self)
		CockpitPlayerAudio.__init__(self, session)
		CockpitPlayerSubtitles.__init__(self)

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

		self.onShown.append(self.__onShow)
		self.onClose.append(self.__onClose)

	def infoMovie(self):
		event = self.service and self.serviceHandler.info(self.service).getEvent()
		if event:
			self.session.open(MovieInfoEPG, event, ServiceReference(self.service))

	def __onShow(self):
		self.evEOF()  # begin playback

	def __onClose(self):
		logger.info("...")

	def evEOF(self):
		logger.info("...")
		self.session.nav.playService(self.service)

		if self.service and self.service.type != SID_DVB:
			self.realSeekLength = self.getSeekLength()

		DelayTimer(50, self.setAudioTrack)
		DelayTimer(50, self.setSubtitleState, True)

	def leavePlayer(self):
		logger.info("...")

		self.setSubtitleState(False)

		if self.service and self.service.type != SID_DVB:
			self.updateCutList(self.service)

		logger.debug("stopping service")
		self.session.nav.stopService()

		# always make a backup copy when recording and we stopped playback
		if self.service and self.service.type == SID_DVB:
			path = self.service.getPath()
			if isRecording(path):
				backupCutList(path + ".cuts")
			logger.debug("reload cuts: %s", path)
			logger.debug("cut_list before reload: %s", self.cut_list)
			cut_list = reloadCutList(path)
			logger.info("cut_list after reload: %s", cut_list)
		self.close()

	def showMovies(self):
		logger.info("...")

	def doEofInternal(self, playing):
		logger.info("playing: %s, self.execing: %s", playing, self.execing)
		if self.execing:
			timer = self.service and isRecording(self.service.getPath())
			if timer:
				self.session.nav.playService(self.service)
				self.doSeekRelative(secondsToPts(-1))
			else:
				self.is_closing = True
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
