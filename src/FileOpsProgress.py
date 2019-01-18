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
from __init__ import _
from Components.config import config
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Button import Button
from Components.Slider import Slider
from enigma import eTimer
from FileOps import FileOps, FILE_OP_DELETE, FILE_OP_MOVE, FILE_OP_COPY
from SkinUtils import getSkinPath
from FileUtils import readFile

ACTIVITY_TIMER_DELAY = 1000


class FileOpsProgress(Screen, FileOps, object):

	def __init__(self, session, selection_list):
		print("MVC: FileOpsProgress: __init__")
		Screen.__init__(self, session)

		self.skinName = ["FileOpsProgress"]
		self.skin = readFile(getSkinPath("FileOpsProgress.xml"))

		self.setTitle(_("File operation(s) in progress..."))
		self["movies_slider"] = Slider(0, 100)
		self["movie_progress_slider"] = Slider(0, 100)
		self["status"] = Label("")
		self["movie_name"] = Label("")
		self["movie_op"] = Label("")

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("Close"))
		self["key_blue"] = Button(_("Hide"))

		self["key_red"].show()
		self["key_blue"].show()
		self["key_green"].hide()

		self["actions"] = ActionMap(
			["OkCancelActions", "ColorActions"],
			{"ok": self.exit, "cancel": self.cancel, "red": self.cancel, "green": self.exit, "blue": self.toggleHide}
		)

		self.selection_list = selection_list
		self.total_movies = 0
		self.current_movies = 0
		self.movie_progress = 0
		self.movie_name = ""
		self.status = ""
		self.request_cancel = False
		self.cancelled = False
		self.hidden = False

		self.activityTimer = eTimer()
		self.activityTimer_conn = self.activityTimer.timeout.connect(self.doActivityTimer)
		self.onShow.append(self.onDialogShow)

	def onDialogShow(self):
		print("MVC: FileOpsProgress: onDialogShow")
		self.execFileOpsProgress()

	def cancel(self):
		if self.hidden:
			print("MVC: FileOpsProgress: cancel: unhide")
			self.toggleHide()
		else:
			if self.cancelled or (self.current_movies > self.total_movies):
				print("MVC: FileOpsProgress: cancel: exit")
				self.exit()
			else:
				print("MVC: FileOpsProgress: cancel: trigger")
				self.request_cancel = True
				self["key_red"].hide()
				self["key_blue"].hide()
				self["key_green"].hide()
				self.status = _("Cancelling, please wait...")

	def exit(self):
		if self.hidden:
			print("MVC: FileOpsProgress: unhide: trigger")
			self.toggleHide()
		else:
			if self.cancelled or (self.current_movies > self.total_movies):
				print("MVC: FileOpsProgress: exit: close")
				self.close()

	def toggleHide(self):
		if self.hidden:
			self.hidden = False
			dimm = config.av.osd_alpha.value
		else:
			self.hidden = True
			dimm = 0

		f = open("/proc/stb/video/alpha", "w")
		f.write("%i" % dimm)
		f.close()

	def updateProgress(self):
		#print("MVC: FileOpsProgress: updateProgress: movie_name: %s, current_movies: %s, total_movies: %s, movie_progress: %s, status: %s" % (self.movie_name, self.current_movies, self.total_movies, self.movie_progress, self.status))
		op_messages = {FILE_OP_DELETE: _("Deleting"), FILE_OP_MOVE: _("Moving"), FILE_OP_COPY: _("Copying")}
		op_msg = op_messages[self.movie_op]
		current_movies = self.current_movies if self.current_movies <= self.total_movies else self.total_movies
		msg = op_msg + ": " + str(current_movies) + " " + _("of") + " " + str(self.total_movies) + " ..."
		self["movie_op"].setText(msg)
		self["movie_name"].setText(self.movie_name)
		self["movies_slider"].setValue(int(round(float(self.current_movies - 1) / float(self.total_movies) * 100)))
		self["movie_progress_slider"].setValue(self.movie_progress)
		self["status"].setText(self.status)

	def doActivityTimer(self):
		target_size = 0
		if self.target_path and os.path.exists(self.target_path):
			target_size = os.path.getsize(self.target_path)
		self.movie_progress = int(float(target_size) / float(self.source_size) * 100)
		#print("MVC: FileOpsProgress: doActivityTimer: self.target_path: %s, self.source_size: %s, target_size: %s, movie_progress: %s" % (self.target_path, self.source_size, target_size, self.movie_progress))
		self.updateProgress()
		self.activityTimer.start(ACTIVITY_TIMER_DELAY, True)

	def execFileOpCallback(self, op, path, _target_path, _file_type):
		print("MVC-I: FileOpsProgress: execFileOpCallback: op: %s, path: %s" % (op, path))
		self.activityTimer.stop()
		self.movie_progress = 100
		self.updateProgress()
		self.nextFileOp()

	def nextFileOp(self):
		print("MVC-I: FileOpsProgress: nextFileOp")
		self.current_movies += 1
		if self.request_cancel and (self.current_movies <= self.total_movies):
			self.current_movies -= 1
			if self.hidden:
				self.toggleHide()
			self["key_red"].hide()
			self["key_blue"].hide()
			self["key_green"].show()
			self.status = _("Cancelled")
			self.cancelled = True
			self.updateProgress()
		else:
			if self.selection_list:
				entry = self.selection_list.pop(0)
				op, file_type, path, target_path = entry
				if path and not path.endswith("..") and os.path.exists(path):
					self.movie_progress = 0
					self.movie_op = op
					self.movie_name = os.path.basename(path)
					self.source_size = os.path.getsize(path)
					self.target_path = os.path.join(target_path, os.path.basename(path)) if target_path else None
					self.status = _("Please wait...")
					self.updateProgress()
					self.activityTimer.start(ACTIVITY_TIMER_DELAY, True)
					self.execFileOp(op, path, target_path, file_type, self.execFileOpCallback)
				else:
					self.nextFileOp()
			else:
				print("MVC: FileOpsProgress: nextFileOp: done.")
				if self.hidden:
					self.toggleHide()
				self["key_red"].hide()
				self["key_blue"].hide()
				self["key_green"].show()
				self.status = _("Cancelled") if self.cancelled else _("Done")
				self.updateProgress()

	def execFileOpsProgress(self):
		print("MVC-I: FileOpsProgress: execFileOpsProgress")
		self.total_movies = len(self.selection_list)
		self.current_movies = 0
		self.nextFileOp()
