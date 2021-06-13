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
from Screens.HelpMenu import HelpableScreen
from ServiceReference import ServiceReference
from CutList import reloadCutList, backupCutList
from CutListUtils import secondsToPts
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

		self.service = service
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		InfoBarSupport.__init__(self, session)

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
				"INFOS":	(self.infoMovie, 	_("EPG Info")),
			},
			-2
		)

		self["NumberActions"].prio = 2
		self.onShown.append(self.__onShow)

	def createSummary(self):
		return CockpitPlayerSummary

	def infoMovie(self):
		event = self.serviceHandler.info(self.service).getEvent()
		if event:
			self.session.open(MovieInfoEPG, event, ServiceReference(self.service))

	def __onShow(self):
		logger.info("...")
		self.session.nav.playService(self.service)

	def leavePlayer(self):
		logger.info("...")

		self.setSubtitleState(False)

		if self.service.type != SID_DVB:
			self.updateCutList(self.service)

		logger.debug("stopping service")
		self.session.nav.stopService()

		# always make a backup copy when recording and we stopped playback
		if self.service.type == SID_DVB:
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
			timer = isRecording(self.service.getPath())
			if timer:
				self.session.nav.playService(self.service)
				self.doSeekRelative(secondsToPts(-1))
			else:
				self.is_closing = True
				if self.service.type != SID_DVB:
					self.updateCutList(self.service)
