#!/usr/bin/python
# coding=utf-8
#
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
from Components.config import config
import NavigationInstance
from timer import TimerEntry
from DelayTimer import DelayTimer
from Tasker import tasker
from CutList import CutList


class RecordingControl(CutList):

	def __init__(self):
		print("MVC-I: RecordingControl: __init__")
		CutList.__init__(self)
		# Register for recording events
		NavigationInstance.instance.RecordTimer.on_state_change.append(self.recordingEvent)
		# check for active recordings not yet in cache
		self.check4ActiveRecordings()
		if config.plugins.moviecockpit.timer_autoclean.value:
			NavigationInstance.instance.RecordTimer.cleanup()

	def recordingEvent(self, timer):
		from FileCacheLoad import FileCacheLoad
		TIMER_STATES = ["StateWaiting", "StatePrepared", "StateRunning", "StateEnded"]
		from FileCache import FileCache
		if timer and not timer.justplay:
			print("MVC-I: RecordingControl: recordingEvent: timer.Filename: %s, timer.state: %s"
				% (timer.Filename, (TIMER_STATES[timer.state] if timer.state in range(0, len(TIMER_STATES)) else timer.state)))

			if timer.state == TimerEntry.StatePrepared:
#				#print("MVC: RecordingControl: recordingEvent: timer.StatePrepared")
				pass

			elif timer.state == TimerEntry.StateRunning:
				#print("MVC: RecordingControl: recordingEvent: REC START for: " + timer.Filename)
				DelayTimer(250, FileCacheLoad.getInstance().loadDatabaseFile, timer.Filename)
				DelayTimer(500, self.reloadList, os.path.dirname(timer.Filename))
				if config.plugins.moviecockpit.cover_auto_download.value:
					DelayTimer(1000, self.autoCoverDownload, timer.Filename)

			elif timer.state == TimerEntry.StateEnded or timer.state == TimerEntry.StateWaiting:
				#print("MVC: RecordingControl: recordingEvent: REC END for: " + timer.Filename)
				FileCache.getInstance().update(timer.Filename, psize=os.path.getsize(timer.Filename))
				DelayTimer(500, self.reloadList, os.path.dirname(timer.Filename))
				# [Cutlist.Workaround] Initiate the Merge
				self.updateFromCuesheet(timer.Filename)
				if hasattr(timer, "move_recording_cmd"):
					#print("MVC: RecordingControl: recordingEvent: file had been moved while recording was in progress, moving left over files...")
					tasker.shellExecute(timer.move_recording_cmd)

	def autoCoverDownload(self, path):
		from MovieCoverDownload import MovieCoverDownload
		from FileCache import FileCache
		filedata = FileCache.getInstance().getFile(path)
		if filedata is not None:
			_directory, _filetype, path, _filename, _ext, name, _date, _length, _description, _extended_description, _service_reference, _size, _cuts, _tags = filedata
			MovieCoverDownload().getCover(path, name)

	def check4ActiveRecordings(self):
		from FileCacheLoad import FileCacheLoad
		from FileCache import FileCache
		#print("MVC: RecordingControl: check4ActiveRecordings")
		for timer in NavigationInstance.instance.RecordTimer.timer_list:
			# check if file is in cache
			if timer.Filename and timer.isRunning() and not timer.justplay:
				if not FileCache.getInstance().exists(timer.Filename):
					#print("MVC: RecordingControl: check4ActiveRecordings: loadDatabaseFile: " + timer.Filename)
					FileCacheLoad.getInstance().loadDatabaseFile(timer.Filename)

	def reloadList(self, path):
		#print("MVC: RecordingControl: reloadList")
		try:
			from MovieSelection import MovieSelection
			movie_selection = MovieSelection.getInstance()
			if movie_selection:
				#print("MVC: RecordingControl: reloadList: calling movie_selection.reloadList")
				movie_selection.reloadList(path)
				movie_selection.updateSpaceInfo()
		except Exception as e:
			print("MVC-E: RecordingControl: reloadList: movie_selection.reloadList exception: %s" % e)
