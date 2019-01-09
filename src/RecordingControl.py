#!/usr/bin/python
# encoding: utf-8
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
#import datetime
from Components.config import config
import NavigationInstance
from timer import TimerEntry
from DelayedFunction import DelayedFunction
from Tasker import mvcTasker


class RecordingControl(object):
	def __init__(self):
		#print("MVC: RecordingControl: __init__")
		# Register for recording events
		NavigationInstance.instance.RecordTimer.on_state_change.append(self.recordingEvent)
		# check for active recordings not yet in cache
		self.check4ActiveRecordings()

	def recordingEvent(self, timer):
		TIMER_STATES = ["StateWaiting", "StatePrepared", "StateRunning", "StateEnded"]
		from MovieCache import MovieCache
		if timer and not timer.justplay:
			print("MVC-I: RecordingControl: recordingEvent: timer.Filename: %s, timer.state: %s"
				% (timer.Filename, (TIMER_STATES[timer.state] if timer.state in range(0, len(TIMER_STATES)) else timer.state)))

			if timer.state == TimerEntry.StatePrepared:
#				#print("MVC: RecordingControl: recordingEvent: timer.StatePrepared")
				pass

			elif timer.state == TimerEntry.StateRunning:
				#print("MVC: RecordingControl: recordingEvent: REC START for: " + timer.Filename)
				DelayedFunction(250, MovieCache.getInstance().loadDatabaseFile, timer.Filename)
				DelayedFunction(500, self.reloadList, os.path.dirname(timer.Filename))
				if config.MVC.cover_auto_download.value:
					DelayedFunction(1000, self.autoCoverDownload, timer.Filename)

			elif timer.state == TimerEntry.StateEnded or timer.state == TimerEntry.StateWaiting:
				#print("MVC: RecordingControl: recordingEvent: REC END for: " + timer.Filename)
				DelayedFunction(100, MovieCache.getInstance().updateSize, timer.Filename, os.path.getsize(timer.Filename))
				DelayedFunction(500, self.reloadList, os.path.dirname(timer.Filename))
				# [Cutlist.Workaround] Initiate the Merge
				DelayedFunction(500, self.mergeCutListAfterRecording, timer.Filename)
				if hasattr(timer, "move_recording_cmd"):
					#print("MVC: RecordingControl: recordingEvent: file had been moved while recording was in progress, moving left over files...")
					mvcTasker.shellExecute(timer.move_recording_cmd)

			if config.MVC.timer_autoclean.value:
				DelayedFunction(2000, self.timerCleanup)  # postpone to avoid crash in basic timer delete by user

	def autoCoverDownload(self, path):
		from MovieCoverDownload import MovieCoverDownload
		MovieCoverDownload().getCoverOfRecording(path)

	def check4ActiveRecordings(self):
		from MovieCache import MovieCache, FILE_IDX_PATH
		#print("MVC: RecordingControl: check4ActiveRecordings")
		for timer in NavigationInstance.instance.RecordTimer.timer_list:
			# check if file is in cache
			if timer.Filename and timer.isRunning() and not timer.justplay:
				afile = MovieCache.getInstance().getFile(timer.Filename)
				if not afile[FILE_IDX_PATH]:
					#print("MVC: RecordingControl: check4ActiveRecordings: loadDatabaseFile: " + timer.Filename)
					MovieCache.getInstance().loadDatabaseFile(timer.Filename)

	def mergeCutListAfterRecording(self, path):
		#print("MVC: RecordingControl: mergeCutListAfterRecording: %s" % path)
		from CutList import CutList
		CutList(path).updateFromCuesheet()

	def reloadList(self, path):
		#print("MVC: RecordingControl: reloadList")
		try:
			from MovieSelection import MovieSelection
			mvcSelection = MovieSelection.getInstance()
			if mvcSelection:
				#print("MVC: RecordingControl: reloadList: calling movie_selection.reloadList")
				mvcSelection.reloadList(path, update_disk_space_info=True)
		except Exception:
			print("MVC-E: RecordingControl: reloadList: movie_selection.reloadList exception")

	def timerCleanup(self):
		NavigationInstance.instance.RecordTimer.cleanup()
