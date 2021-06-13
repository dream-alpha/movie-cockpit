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
from time import time
from Components.config import config
from Components.ActionMap import HelpableActionMap
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from enigma import eTimer, iPlayableService
from Screens.InfoBarGenerics import InfoBarSeek, InfoBarMenu, InfoBarShowMovies, InfoBarAudioSelection, \
	InfoBarPVRState, InfoBarCueSheetSupport, InfoBarPlugins, InfoBarNumberZap, \
	InfoBarExtensions, InfoBarShowHide, InfoBarNotifications, Notifications
from Screens.MessageBox import MessageBox
from CutListUtils import secondsToPts, ptsToSeconds, removeFirstMarks, getCutListLast
from CutList import readCutList, writeCutList, updateCutList
from ServiceCenter import ServiceCenter
from ServiceUtils import SID_DVB
from RecordingUtils import isRecording
from CockpitPlayerAudio import CockpitPlayerAudio
from CockpitPlayerSubtitles import CockpitPlayerSubtitles


class InfoBarSupport(
	InfoBarBase, InfoBarNotifications, InfoBarSeek, InfoBarShowHide, InfoBarMenu, InfoBarShowMovies, InfoBarAudioSelection,
	InfoBarExtensions, InfoBarPVRState, InfoBarCueSheetSupport,
	InfoBarPlugins, InfoBarNumberZap, CockpitPlayerAudio, CockpitPlayerSubtitles):

	ENABLE_RESUME_SUPPORT = True

	def __init__(self, session):
		self.allowPiP = False
		self.allowPiPSwap = False

		InfoBarShowHide.__init__(self)
		InfoBarMenu.__init__(self)
		InfoBarBase.__init__(self)
		InfoBarSeek.__init__(self)
		InfoBarShowMovies.__init__(self)
		InfoBarAudioSelection.__init__(self)
		InfoBarExtensions.__init__(self)
		InfoBarPVRState.__init__(self)
		InfoBarNotifications.__init__(self)
		InfoBarPlugins.__init__(self)
		InfoBarNumberZap.__init__(self)
		CockpitPlayerAudio.__init__(self, session)
		CockpitPlayerSubtitles.__init__(self)

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

		self.__event_tracker = ServiceEventTracker(
			screen=self,
			eventmap={
				iPlayableService.evStart: self.__serviceStarted,
			}
		)

		self.service_started = False
		self.cut_list = []
		self.is_closing = False
		self.resume_point = 0
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

	### support functions for converters: MVCServicePosition and MVCRecordingPosition

	def getLength(self):
		length = 0
		if self.service.type == SID_DVB:
			_len = self.serviceHandler.info(self.service).getLength()
			event_start_time = self.serviceHandler.info(self.service).getEventStartTime()
			recording_start_time = self.serviceHandler.info(self.service).getRecordingStartTime()
			if event_start_time > recording_start_time:
				_len += event_start_time - recording_start_time
			length = secondsToPts(_len)
		else:
			length = self.getSeekLength()
		logger.info("length: %ss (%s)", ptsToSeconds(length), length)
		return length

	def getSeekLength(self):
		length = 0
		seek = self.getSeek()
		if seek is not None:
			_len = seek.getLength()
			logger.debug("seek.getLength(): %s", _len)
			if not _len[0]:
				length = _len[1]
		logger.info("length: %ss (%s)", ptsToSeconds(length), length)
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
			if not pos[0] and pos[1] > 0:
				position = pos[1]
		logger.info("position: %ss (%s)", ptsToSeconds(position), position)
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

	# InfoBarCueSheetSupport

	def getCutList(self):
		logger.info("cut_list: %s", self.cut_list)
		return self.cut_list

	def downloadCuesheet(self):
		logger.debug("self.service: %s", self.service.getPath() if self.service else None)
		self.cut_list = readCutList(self.service.getPath())
		logger.debug("cut_list: %s", self.cut_list)

	def uploadCuesheet(self):
		logger.debug("self.service: %s", self.service.getPath() if self.service else None)
		logger.debug("cut_list: %s", self.cut_list)
		writeCutList(self.service.getPath(), self.cut_list)

	def updateCutList(self, service):
		logger.info("...")
		if self.getPosition() == 0:
			updateCutList(service.getPath(), self.getSeekLength(), self.getSeekLength())
		else:
			updateCutList(service.getPath(), self.getPosition(), self.getSeekLength())
		logger.debug("pos: %s, length: %s", str(self.getPosition()), str(self.getSeekLength()))

	def __serviceStarted(self):
		logger.info("self.is_closing: %s", self.is_closing)
		if not self.is_closing:
			self.service_started = True
			self.setAudioTrack()
			self.setSubtitleState(True)
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
		logger.info("answer: %s", answer)
		if answer:
			self.doSeek(self.resume_point)
		else:
			if config.plugins.moviecockpit.movie_start_position.value == "first_mark":
				self.jumpToFirstMark()
			if config.plugins.moviecockpit.movie_start_position.value == "event_start":
				self.doSeek(self.event_start)
			if config.plugins.moviecockpit.movie_start_position.value == "beginning":
				self.doSeek(0)

	def jumpToFirstMark(self):
		logger.info("...")
		first_mark = None
		current_pos = self.getPosition() + secondsToPts(2)
		margin = secondsToPts(config.recording.margin_before.value * 60) * 2 or secondsToPts(20 * 60)
		middle = (self.getSeekLength() or secondsToPts(90 * 60)) / 2
		for (pts, what) in self.cut_list:
			if what == self.CUT_TYPE_MARK:
				if current_pos < pts < min(margin, middle):
					if first_mark is None or pts < first_mark:
						first_mark = pts
		logger.debug("first_mark: %s", first_mark)
		if first_mark is not None:
			self.doSeek(first_mark)

	def jumpNextMark(self):
		logger.info("...")
		if not self.jumpPreviousNextMark(lambda x: x - secondsToPts(1)):
			self.doSeekEOF()
		else:
			if config.usage.show_infobar_on_skip.value:
				self.showAfterSeek()

	def getEventStart(self):
		event_start_time = self.serviceHandler.info(self.service).getEventStartTime()
		recording_start_time = self.serviceHandler.info(self.service).getRecordingStartTime()
		event_start = event_start_time - recording_start_time
		if event_start < 0:
			event_start = 0
		logger.info("event_start: %ds", event_start)
		return secondsToPts(event_start)

	# InfoBarSeek

	def doSeek(self, pts):
		logger.info("pts: %s", pts)
		length = self.getSeekLength()
		if length and length < pts:
			# PTS is behind the movie length
			self.doSeekEOF()
		else:
			InfoBarSeek.doSeek(self, pts)
			if pts and config.usage.show_infobar_on_skip.value:
				self.showAfterSeek()

	def doSeekEOF(self):
		logger.info("...")
		position = self.getPosition()
		end  = self.getSeekLength() - secondsToPts(1)
		logger.debug("position: %s, end: %s", position, end)
		if position < end:
			InfoBarSeek.doSeek(self, end)
		elif self.seekstate != self.SEEK_STATE_PAUSE:
			InfoBarSeek._InfoBarSeek__evEOF(self)
