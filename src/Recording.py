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
import os
import time
from enigma import quitMainloop
from Components.config import config
import NavigationInstance
from timer import TimerEntry
from DelayTimer import DelayTimer
from CutList import mergeBackupCutList
from ParserMetaFile import ParserMetaFile
from Plugins.SystemPlugins.CacheCockpit.FileCache import FileCache, FILE_TYPE_FILE
from Plugins.SystemPlugins.CacheCockpit.FileCacheSQL import FILE_IDX_NAME
from MovieCockpit import MovieCockpit
from MovieCoverDownload import MovieCoverDownload
from FileOpManager import FileOpManager
import Screens.Standby
from RecordTimer import AFTEREVENT
from FileOp import FILE_OP_MOVE


class Recording():

	def __init__(self):
		logger.info("...")
		self.after_events = []
		# Register for recording events
		NavigationInstance.instance.RecordTimer.on_state_change.append(self.recordingEvent)
		# check for active recordings not yet in cache
		self.check4ActiveRecordings()
		if config.plugins.moviecockpit.timer_autoclean.value:
			NavigationInstance.instance.RecordTimer.cleanup()

	def parseMetaFile(self, timer):
		ParserMetaFile(timer.Filename).updateXMeta({
			"recording_start_time": int(time.time()),
			"timer_start_time": int(timer.begin + config.recording.margin_before.value * 60),
			"timer_stop_time": int(timer.end - config.recording.margin_after.value * 60),
			"recording_margin_before": config.recording.margin_before.value * 60,
			"recording_margin_after": config.recording.margin_after.value * 60,
		})

	def recordingEvent(self, timer):
		TIMER_STATES = ["StateWaiting", "StatePrepared", "StateRunning", "StateEnded"]
		if timer and not timer.justplay and not hasattr(timer, "timeshift"):
			logger.debug(
				"timer.Filename: %s, timer.state: %s",
				timer.Filename, (TIMER_STATES[timer.state] if timer.state in range(0, len(TIMER_STATES)) else timer.state)
			)

			if timer.state == TimerEntry.StateRunning:
				logger.debug("REC START for: %s, afterEvent: %s", timer.Filename, timer.afterEvent)
				if Screens.Standby.inStandby and config.misc.standbyCounter.value == 1 and config.plugins.moviecockpit.archive_enable.value:
					config.misc.isNextRecordTimerAfterEventActionAuto.value = False
					config.misc.isNextRecordTimerAfterEventActionAuto.save()
					self.after_events.append(timer.afterEvent)
					timer.afterEvent1 = timer.afterEvent
					timer.afterEvent = AFTEREVENT.NONE
				self.parseMetaFile(timer)
				DelayTimer(250, FileCache.getInstance().loadDatabaseFile, timer.Filename)
				DelayTimer(500, self.loadList)
				if config.plugins.moviecockpit.cover_auto_download.value:
					DelayTimer(1000, self.autoCoverDownload, timer.Filename)

			elif timer.state == TimerEntry.StateEnded or timer.state == TimerEntry.StateWaiting:
				logger.debug("REC END for: %s, afterEvent: %s", timer.Filename, timer.afterEvent)
				if os.path.exists(timer.Filename):
					ParserMetaFile(timer.Filename).updateXMeta({"recording_stop_time": int(time.time())})
					mergeBackupCutList(timer.Filename + ".cuts")
					FileCache.getInstance().reloadDatabaseFile(timer.Filename)
					if Screens.Standby.inStandby and config.misc.standbyCounter.value == 1 and config.plugins.moviecockpit.archive_enable.value:
						FileOpManager.getInstance().addJob(FILE_OP_MOVE, timer.Filename, config.plugins.moviecockpit.archive_target_dir.value, FILE_TYPE_FILE, self.handleAfterEvent)
					if hasattr(timer, "afterEvent1"):
						timer.afterEvent = timer.afterEvent1
				DelayTimer(500, self.loadList)

	def handleAfterEvent(self, _file_op, _path, _target_dir, _file_type, _error):
		logger.debug("...")
		jobs = len(FileOpManager.getInstance().getPendingJobs())
		if jobs <= 1:
			do_shutdown = False
			for after_event in self.after_events:
				if after_event in [AFTEREVENT.AUTO, AFTEREVENT.DEEPSTANDBY]:
					do_shutdown = True
					break
			if do_shutdown:
				recordings = NavigationInstance.instance.getRecordings()
				if not recordings:
					rec_time = NavigationInstance.instance.RecordTimer.getNextRecordingTime()
					if rec_time > 0 and (rec_time - time.time()) < 360:
						logger.info("another recording starts in %s seconds, do not shut down yet", rec_time - time.time())
					else:
						logger.info("no starting recordings in the next 360 seconds, so we can shutdown")
						quitMainloop(8)
		else:
			logger.info("%d jobs still running", jobs)

	def autoCoverDownload(self, path):
		file_data = FileCache.getInstance().getFile(path)
		if file_data is not None:
			MovieCoverDownload().getCover(path, file_data[FILE_IDX_NAME])

	def check4ActiveRecordings(self):
		logger.debug("...")
		for timer in NavigationInstance.instance.RecordTimer.timer_list:
			# check if file is in cache
			if timer.Filename and timer.isRunning() and not timer.justplay:
				if not FileCache.getInstance().exists(timer.Filename):
					logger.debug("loadDatabaseFile: %s", timer.Filename)
					self.parseMetaFile(timer)
					FileCache.getInstance().loadDatabaseFile(timer.Filename)

	def loadList(self, adir=None):
		logger.debug("adir: %s", adir)
		moviecockpit = MovieCockpit.getInstance()
		if moviecockpit:
			logger.debug("calling moviecockpit.loadList")
			moviecockpit.movie_list.loadList(adir)
