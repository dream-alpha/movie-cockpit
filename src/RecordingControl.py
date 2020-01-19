#!/usr/bin/python
# coding=utf-8
#
# Copyright (C) 2018-2020 by dream-alpha
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


import os
import time
from Components.config import config
import NavigationInstance
from timer import TimerEntry
from DelayTimer import DelayTimer
from CutList import mergeBackupCutList
from ParserMetaFile import ParserMetaFile
from FileCache import FileCache, FILE_IDX_NAME
from FileCacheLoad import FileCacheLoad
from MovieSelection import MovieSelection
from MovieCoverDownload import MovieCoverDownload


class RecordingControl():

	def __init__(self):
		print("MVC-I: RecordingControl: __init__")
		# Register for recording events
		NavigationInstance.instance.RecordTimer.on_state_change.append(self.recordingEvent)
		# check for active recordings not yet in cache
		self.check4ActiveRecordings()
		if config.plugins.moviecockpit.timer_autoclean.value:
			NavigationInstance.instance.RecordTimer.cleanup()

	def recordingEvent(self, timer):
		TIMER_STATES = ["StateWaiting", "StatePrepared", "StateRunning", "StateEnded"]
		if timer and not timer.justplay:
			print(
				"MVC-I: RecordingControl: recordingEvent: timer.Filename: %s, timer.state: %s"
				% (timer.Filename, (TIMER_STATES[timer.state] if timer.state in range(0, len(TIMER_STATES)) else timer.state))
			)

			if timer.state == TimerEntry.StatePrepared:
				#print("MVC: RecordingControl: recordingEvent: timer.StatePrepared")
				pass

			elif timer.state == TimerEntry.StateRunning:
				#print("MVC: RecordingControl: recordingEvent: REC START for: " + timer.Filename)
				ParserMetaFile(timer.Filename).updateXMeta({
					"recording_start_time": int(time.time()),
					"timer_start_time": timer.begin + config.recording.margin_before.value * 60,
					"timer_stop_time": timer.end - config.recording.margin_after.value * 60,
					"recording_margin_before": config.recording.margin_before.value * 60,
					"recording_margin_after": config.recording.margin_after.value * 60,
				})
				DelayTimer(250, FileCacheLoad.getInstance().loadDatabaseFile, timer.Filename)
				DelayTimer(500, self.reloadList, os.path.dirname(timer.Filename))
				if config.plugins.moviecockpit.cover_auto_download.value:
					DelayTimer(1000, self.autoCoverDownload, timer.Filename)

			elif timer.state == TimerEntry.StateEnded or timer.state == TimerEntry.StateWaiting:
				#print("MVC: RecordingControl: recordingEvent: REC END for: " + timer.Filename)
				if os.path.exists(timer.Filename):
					ParserMetaFile(timer.Filename).updateXMeta({"recording_stop_time": int(time.time())})
					FileCacheLoad.getInstance().reloadDatabaseFile(timer.Filename)
					mergeBackupCutList(timer.Filename + ".cuts")  # merge cutlists
				DelayTimer(500, self.reloadList, os.path.dirname(timer.Filename))

	def autoCoverDownload(self, path):
		filedata = FileCache.getInstance().getFile(path)
		if filedata is not None:
			MovieCoverDownload().getCover(path, filedata[FILE_IDX_NAME])

	def check4ActiveRecordings(self):
		#print("MVC: RecordingControl: check4ActiveRecordings")
		for timer in NavigationInstance.instance.RecordTimer.timer_list:
			# check if file is in cache
			if timer.Filename and timer.isRunning() and not timer.justplay:
				if not FileCache.getInstance().exists(timer.Filename):
					#print("MVC: RecordingControl: check4ActiveRecordings: loadDatabaseFile: " + timer.Filename)
					ParserMetaFile(timer.Filename).updateXMeta({
						"recording_start_time": int(time.time()),
						"timer_start_time": timer.begin + config.recording.margin_before.value * 60,
						"timer_stop_time": timer.end - config.recording.margin_after.value * 60,
						"recording_margin_before": config.recording.margin_before.value * 60,
						"recording_margin_after": config.recording.margin_after.value * 60
					})
					FileCacheLoad.getInstance().loadDatabaseFile(timer.Filename)

	def reloadList(self, path):
		#print("MVC: RecordingControl: reloadList")
		movie_selection = MovieSelection.getInstance()
		if movie_selection:
			#print("MVC: RecordingControl: reloadList: calling movie_selection.reloadList")
			movie_selection.reloadList(path)
			movie_selection.updateSpaceInfo()
