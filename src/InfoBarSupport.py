#!/usr/bin/python
# coding=utf-8
#
# Copyright (C) 2011 by betonme
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
from time import time
from Components.config import config
from Components.ActionMap import HelpableActionMap
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from enigma import eTimer, iPlayableService
from Screens.InfoBarGenerics import InfoBarExtensions, InfoBarSeek, InfoBarMenu, InfoBarShowMovies, InfoBarAudioSelection, InfoBarSimpleEventView, \
	InfoBarPVRState, InfoBarCueSheetSupport, InfoBarSubtitleSupport, InfoBarTeletextPlugin, InfoBarServiceErrorPopupSupport, InfoBarPlugins, InfoBarNumberZap, \
	InfoBarPiP, InfoBarEPG, InfoBarShowHide, InfoBarNotifications, InfoBarServiceNotifications, Notifications
from Screens.MessageBox import MessageBox
from CutListUtils import secondsToPts, ptsToSeconds, removeFirstMarks, getCutListLast
from CutList import readCutList, writeCutList
from ServiceCenter import ServiceCenter
from ServiceUtils import SID_DVB
from RecordingUtils import isRecording


class InfoBarSupport(
	InfoBarBase, InfoBarNotifications, InfoBarSeek, InfoBarShowHide, InfoBarMenu, InfoBarShowMovies, InfoBarAudioSelection,
	InfoBarSimpleEventView, InfoBarServiceNotifications, InfoBarPVRState, InfoBarCueSheetSupport, InfoBarSubtitleSupport, InfoBarTeletextPlugin,
	InfoBarServiceErrorPopupSupport, InfoBarExtensions, InfoBarPlugins, InfoBarNumberZap, InfoBarPiP, InfoBarEPG):

	ENABLE_RESUME_SUPPORT = True

	def __init__(self):
		self.allowPiP = True
		self.allowPiPSwap = False

		for x in InfoBarShowHide, InfoBarMenu, InfoBarBase, InfoBarSeek, InfoBarShowMovies, InfoBarAudioSelection, InfoBarSimpleEventView,\
			InfoBarServiceNotifications, InfoBarPVRState, InfoBarSubtitleSupport, InfoBarTeletextPlugin, InfoBarServiceErrorPopupSupport,\
			InfoBarExtensions, InfoBarNotifications, InfoBarPlugins, InfoBarNumberZap, InfoBarPiP, InfoBarEPG:
			x.__init__(self)

		self["CueSheetActions"] = HelpableActionMap(
			self,
			"InfobarCueSheetActions",
			{
				"jumpPreviousMark": (self.jumpPreviousMark, _("Jump to previous marked position")),
				"jumpNextMark": (self.jumpNextMark, _("Jump to next marked position")),
				"toggleMark": (self.toggleMark, _("Toggle cut mark at current position"))
			},
			prio=1
		)

		self.cut_list = []
		self.is_closing = False
		self.resume_point = 0

		self.__event_tracker = ServiceEventTracker(
			screen=self,
			eventmap={
				iPlayableService.evStart: self.__serviceStarted,
			}
		)

		self.event_start = 0
		self.skip_first = True
		self.skip_forward = True
		self.skip_index = 0
		self.skip_distance_long = [5 * 60, 60, 10]
		self.skip_distance_short = [60, 10]
		self.skip_distance = self.skip_distance_long
		self.reset_skip_timer = eTimer()
		self.reset_skip_timer_conn = self.reset_skip_timer.timeout.connect(self.resetSkipTimer)

		self.serviceHandler = ServiceCenter.getInstance()

		self.service_started = False

	### support functions for converters: MVCServicePosition and MVCRecordingPosition

	def getLength(self):
		length = 0
		if self.service.type == SID_DVB:
			__len = self.serviceHandler.info(self.service).getLength()
			event_start_time = self.serviceHandler.info(self.service).getEventStartTime()
			recording_start_time = self.serviceHandler.info(self.service).getRecordingStartTime()
			if event_start_time > recording_start_time:
				__len += event_start_time - recording_start_time
			length = secondsToPts(__len)
		else:
			# non-ts movies
			seek = self.getSeek()
			if seek is not None:
				__len = seek.getLength()
				logger.debug("seek.getLength(): %s", __len)
				if not __len[0]:
					length = __len[1]
		logger.info("length: %ss", ptsToSeconds(length))
		return length

	def getRecordingPosition(self):
		position = 0
		path = self.service.getPath()
		recording = isRecording(path)
		if recording:
			begin = self.serviceHandler.info(self.service).getRecordingStartTime()
			now = time()
			position = secondsToPts(now - begin)
		else:
			position = self.getPosition()
		return position

	def getPosition(self):
		position = 0
		seek = self.getSeek()
		if seek and self.service_started:
			pos = seek.getPlayPosition()
			if not pos[0]:
				position = pos[1]
		logger.info("position: %ss", ptsToSeconds(position))
		return position

	### Intelligent skip functions

	def resetSkipTimer(self):
		self.skip_distance = self.skip_distance_long
		self.skip_index = 0
		self.skip_forward = True

	def setSkipDistance(self):
		if self.skip_first and config.plugins.moviecockpit.movie_start_position.value == "event_start":
			self.skip_first = False
			logger.debug("position: %s, event_start: %s", self.getPosition(), self.event_start)
			if abs(self.getPosition() - self.event_start) <= secondsToPts(60):
				self.skip_distance = self.skip_distance_short
			else:
				self.skip_distance = self.skip_distance_long

	def skipForward(self):
		logger.info("...")
		self.reset_skip_timer.start(10000, True)
		self.setSkipDistance()
		if not self.skip_forward:
			self.skip_index = len(self.skip_distance) - 1 if self.skip_index >= len(self.skip_distance) - 1 else self.skip_index + 1
			self.skip_forward = True
		self.doSeekRelative(secondsToPts(self.skip_distance[self.skip_index]))
		if self.skip_distance == self.skip_distance_long and self.skip_index == 0:
			self.skip_index = 1

	def skipBackward(self):
		logger.info("...")
		self.reset_skip_timer.start(10000, True)
		self.setSkipDistance()
		if self.skip_forward:
			self.skip_index = len(self.skip_distance) - 1 if self.skip_index >= len(self.skip_distance) - 1 else self.skip_index + 1
			self.skip_forward = False
		self.doSeekRelative(secondsToPts(-self.skip_distance[self.skip_index]))

	### Override from InfoBarGenerics.py

	def zapToService(self, service):
		logger.info("service: %s", service.toString() if service else None)
		if service is not None:
			self.servicelist.setCurrentSelection(service) #select the service in servicelist
			self.servicelist.zap()
			self.session.nav.playService(service)

	# InfoBarCueSheetSupport

	def getCutList(self):
		return self.cut_list

	def downloadCuesheet(self):
		logger.debug("self.service: %s", self.service.getPath() if self.service else None)
		self.cut_list = readCutList(self.service.getPath())
		logger.debug("cut_list: %s", self.cut_list)

	def uploadCuesheet(self):
		logger.debug("self.service: %s", self.service.getPath() if self.service else None)
		logger.debug("cut_list: %s", self.cut_list)
		writeCutList(self.service.getPath(), self.cut_list)

	def __serviceStarted(self):
		logger.info("self.is_closing: %s", self.is_closing)
		if not self.is_closing:
			self.service_started = True
			self.event_start = self.getEventStart()
			self.downloadCuesheet()
			if config.plugins.moviecockpit.movie_ignore_first_marks.value:
				self.cut_list = removeFirstMarks(self.cut_list)
			if config.plugins.moviecockpit.movie_resume_at_last_pos.value:
				self.resume_point = getCutListLast(self.cut_list)
				if self.resume_point > 0:
					seconds = ptsToSeconds(self.resume_point)
					logger.debug("resume_point: %s", seconds)
					Notifications.AddNotificationWithCallback(
						self.playLastCallback,
						MessageBox,
						_("Do you want to resume this playback?")
						+ "\n"
						+ _("Resume position at") + " "
						+ "%d:%02d:%02d" % (seconds / 3600, seconds % 3600 / 60, seconds % 60),
						timeout=10,
						type=MessageBox.TYPE_YESNO,
						default=False,
					)
				else:
					self.playLastCallback(False)
			else:
				self.playLastCallback(False)

	def playLastCallback(self, answer):
		if answer:
			self.doSeek(self.resume_point)
		else:
			if config.plugins.moviecockpit.movie_start_position.value == "first_mark":
				self.jumpToFirstMark()
			if config.plugins.moviecockpit.movie_start_position.value == "event_start":
				resume_point = self.event_start
				logger.debug("resume_point: %s", resume_point)
				if resume_point > 0:
					self.jumpTo(resume_point)
			if config.plugins.moviecockpit.movie_start_position.value == "beginning":
				self.jumpTo(0)

	def jumpToFirstMark(self):
		first_mark = 0
		current_pos = self.cueGetCurrentPosition() or 0
		# Increase current_pos by 2 seconds to make sure we get the correct mark
		current_pos = current_pos + secondsToPts(2)
		# increase recording margin to make sure we get the correct mark
		margin = secondsToPts(config.recording.margin_before.value * 60) * 2 or secondsToPts(20 * 60)
		middle = (self.getSeekLength() or secondsToPts(90 * 60)) / 2

		for (pts, what) in self.cut_list:
			if what == self.CUT_TYPE_MARK:
				if max(current_pos, margin, middle) < pts < first_mark:
					if first_mark and pts < first_mark:
						first_mark = pts
		if first_mark:
			self.jumpTo(first_mark)

	def jumpNextMark(self):
		if not self.jumpPreviousNextMark(lambda x: x - secondsToPts(1)):
			# there is no further mark
			self.doSeekEOF()
		else:
			if config.usage.show_infobar_on_skip.value:
				# InfoBarSeek
				self.showAfterSeek()

	def jumpTo(self, pos):
		self.doSeek(pos)

	def getEventStart(self):
		event_start_time = self.serviceHandler.info(self.service).getEventStartTime()
		recording_start_time = self.serviceHandler.info(self.service).getRecordingStartTime()
		event_start = event_start_time - recording_start_time
		logger.info("event_start: %ds", event_start)
		return secondsToPts(event_start)

	# InfoBarSeek
	# Seekbar workaround
	def seekFwdManual(self):
		InfoBarSeek.seekFwdManual(self)

	# Seekbar workaround
	def seekBackManual(self):
		InfoBarSeek.seekBackManual(self)

	def doSeekRelative(self, pts):
		if self.getSeekLength() < self.getSeekPlayPosition() + pts:
			# Relative jump is behind the movie length
			self.doSeekEOF()
		else:
			InfoBarSeek.doSeekRelative(self, pts)

	def doSeek(self, pts):
		length = self.getSeekLength()
		if length and length < pts:
			# PTS is behind the movie length
			self.doSeekEOF()
		else:
			# call base class function
			InfoBarSeek.doSeek(self, pts)
			if pts and config.usage.show_infobar_on_skip.value:
				self.showAfterSeek()

	def getSeekPlayPosition(self):
		logger.debug("...")
		try:
			# InfoBarCueSheetSupport
			return self.cueGetCurrentPosition() or 0
		except Exception as e:
			logger.error("exception: %s", e)
		return 0

	def getSeekLength(self):
		logger.debug("...")
		length = 0
		try:
			# call private InfoBarCueSheetSupport function
			seek = InfoBarCueSheetSupport._InfoBarCueSheetSupport__getSeekable(self)
		except Exception as e:
			logger.error("exception: %s", e)
		if seek is not None:
			__len = seek.getLength()
			if not __len[0]:
				length = __len[1]
		return length

	def doSeekEOF(self):
		# stop 2 seconds before eof
		play = self.getSeekPlayPosition()
		end  = self.getSeekLength() - secondsToPts(2)
		if play < end:
			InfoBarSeek.doSeek(self, end)
		# if player is in pause mode do not call eof
		elif self.seekstate != self.SEEK_STATE_PAUSE:
			InfoBarSeek._InfoBarSeek__evEOF(self)
