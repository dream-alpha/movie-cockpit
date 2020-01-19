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
from __init__ import _
from enigma import eTimer
from FileOps import FileOps
from FileProgress import FileProgress
from FileOps import FILE_OP_DELETE, FILE_OP_MOVE, FILE_OP_COPY

ACTIVITY_TIMER_DELAY = 1000


class FileOpsProgress(FileProgress, FileOps):

	def __init__(self, session, csel, selection_list, return_path):
		#print("MVC: FileOpsProgress: __init__")
		FileProgress.__init__(self, session, return_path)
		FileOps.__init__(self)
		self.csel = csel
		self.skinName = "MVCFileOpsProgress"
		self.setTitle(_("File operation(s)") + " ...")
		self.execution_list = selection_list
		self.activityTimer = eTimer()
		self.activityTimer_conn = self.activityTimer.timeout.connect(self.doActivityTimer)
		self.onShow.append(self.onDialogShow)

	def onDialogShow(self):
		#print("MVC: FileOpsProgress: onDialogShow")
		self.execFileOpsProgress()

	def reloadList(self, path):
		print("MVC-I: FileOpsProgress: reloadList: path: %s" % path)
		self.csel.reloadList(path)

	def doActivityTimer(self):
		target_size = 0
		if self.target_path and os.path.exists(self.target_path):
			target_size = os.path.getsize(self.target_path)
		if self.source_size == 0:
			self.file_progress = 100
		else:
			self.file_progress = int(float(target_size) / float(self.source_size) * 100)
		#print("MVC: FileOpsProgress: doActivityTimer: self.target_path: %s, self.source_size: %s, target_size: %s, file_progress: %s" % (self.target_path, self.source_size, target_size, self.file_progress))
		self.updateProgress()
		self.activityTimer.start(ACTIVITY_TIMER_DELAY, True)

	def updateProgress(self):
		#print("MVC: FileOpsProgress: updateProgress: file_name: %s, current_files: %s, total_files: %s, file_progress: %s, status: %s" % (self.file_name, self.current_files, self.total_files, self.file_progress, self.status))
		op_messages = {FILE_OP_DELETE: _("Deleting"), FILE_OP_MOVE: _("Moving"), FILE_OP_COPY: _("Copying")}
		op_msg = op_messages[self.file_op]
		current_files = self.current_files if self.current_files <= self.total_files else self.total_files
		msg = op_msg + ": " + str(current_files) + " " + _("of") + " " + str(self.total_files) + " ..."
		self["operation"].setText(msg)
		self["name"].setText(self.file_name)
		self["slider1"].setValue(int(round(float(self.current_files - 1) / float(self.total_files) * 100)))
		self["slider2"].setValue(self.file_progress)
		self["status"].setText(self.status)

	def doFileOp(self, entry):
		op, path, target_path, filetype = entry
		if path and not path.endswith("..") and os.path.exists(path):
			#print("MVC: FileOpsProgress: doFileOp: path: %s" % path)
			self.movie_progress = 0
			self.file_op = op
			self.file_name = os.path.basename(path)
			self.source_size = os.path.getsize(path)
			self.target_path = os.path.join(target_path, os.path.basename(path)) if target_path else None
			self.status = _("Please wait") + " ..."
			self.updateProgress()
			self.activityTimer.start(ACTIVITY_TIMER_DELAY, True)
			self.execFileOp(op, path, target_path, filetype)
		else:
			self.nextFileOp()

	def execFileOpCallback(self, op, path, _target_path, _filetype):
		print("MVC-I: FileOpsProgress: execFileOpCallback: op: %s, path: %s" % (op, path))
		self.activityTimer.stop()
		self.file_progress = 100
		self.updateProgress()
		self.nextFileOp()

	def execFileOpsProgress(self):
		print("MVC-I: FileOpsProgress: execFileOpsProgress")
		self.total_files = len(self.execution_list)
		self.current_files = 0
		self.nextFileOp()
