#!/usr/bin/python
# encoding: utf-8
#
# Copyright (C) 2018 by dream-alpha
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
from DelayedFunction import DelayedFunction
from MovieCache import MovieCache, TYPE_ISDIR, FILE_IDX_PATH
from MediaTypes import extVideo
from FileOps import FileOps
from MountPoints import MountPoints
from Bookmarks import Bookmarks
from Tasker import mvcTasker

RC_TRASHCAN_CREATE_DIR_FAILED = 1

instance = None


class Trashcan(FileOps, MountPoints, Bookmarks, object):

	def __init__(self):
		if config.MVC.movie_trashcan_enable.value:
			self.__schedulePurge()
		config.MVC.disk_space_info.value = self.getMountPointsSpaceUsedPercent()

	@staticmethod
	def getInstance():
		global instance
		if instance is None:
			instance = Trashcan()
		return instance

	def __schedulePurge(self):
		if config.MVC.movie_trashcan_enable.value and config.MVC.movie_trashcan_clean.value:
			# Recall setup function in 24 hours
			seconds = 24 * 60 * 60
			DelayedFunction(1000 * seconds, self.__schedulePurge)
			# Execute trash cleaning
			DelayedFunction(5000, self.purgeTrashcan)
			print("MVC: Trashcan: scheduleCleanup: next trashcan cleanup in %s minutes" % (seconds / 60))

	def createTrashcan(self):
		import datetime
		print("MVC: Trashcan: createTrashcan")
		for bookmark in self.getBookmarks():
			path = bookmark + "/trashcan"
			if not os.path.exists(path):
				try:
					os.makedirs(path)
					MovieCache.getInstance().add(
						(path, TYPE_ISDIR, path, _(os.path.basename(path)), "", _(os.path.basename(path)),
						str(datetime.datetime.fromtimestamp(os.stat(path).st_mtime))[0:19], 0, "", "", "", 0, "", "")
					)
				except Exception:
					config.MVC.movie_trashcan_enable.value = False
					return RC_TRASHCAN_CREATE_DIR_FAILED
		return 0

	def enableTrashcan(self):
		print("MVC: Trashcan: enable")
		if not config.MVC.movie_trashcan_enable.value:
			self.createTrashcan()

	def purgeTrashcan(self, empty_trash=False, callback=None):
		import time
		print("MVC: Trashcan: purgeTrashcan: empty_trash: %s" % empty_trash)
		cmd = []
		now = time.localtime()
		trashcan_dirs = []
		for bookmark in self.getBookmarks():
			trashcan_dirs.append(bookmark + "/trashcan")
		print("MVC: Trashcan: purgeTrashcan: trashcan_dirs: %s" % trashcan_dirs)
		filelist = MovieCache.getInstance().getFileList(trashcan_dirs)
		for afile in filelist:
			path = afile[FILE_IDX_PATH]
			# Only check media files
			ext = os.path.splitext(path)[1]
			if ext in extVideo and os.path.exists(path):
				if empty_trash or now > time.localtime(os.stat(path).st_mtime + 24 * 60 * 60 * int(config.MVC.movie_trashcan_retention.value)):
					print("MVC: Trashcan: purgeTrashcan: path: " + path)
					cmd = self.execFileDelete(cmd, path, "file")
					print("MVC: Trashcan: purgeTrashcan: cmd: %s" % cmd)
					MovieCache.getInstance().delete(path)
		if cmd:
			association = []
			if callback is not None:
				association.append(callback)
			print("MVC: Trashcan: purgeTrashcan: deleting...")
			mvcTasker.shellExecute(cmd, association)
		else:
			print("MVC: Trashcan: purgeTrashcan: nothing to delete")
