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
from Components.config import config
from DelayedFunction import DelayedFunction
from FileCache import FileCache, FILE_IDX_PATH, FILE_IDX_TYPE
from MediaTypes import extVideo
from FileOps import FileOps, FILE_OP_DELETE
from Bookmarks import Bookmarks

RC_TRASHCAN_CREATED = 0
RC_TRASHCAN_CREATE_DIR_FAILED = 1

instance = None


class Trashcan(FileOps, Bookmarks, object):

	def __init__(self):
		if config.MVC.trashcan_enable.value:
			self.__schedulePurge()
		config.MVC.disk_space_info.value = self.getMountPointsSpaceUsedPercent()

	@staticmethod
	def getInstance():
		global instance
		if instance is None:
			instance = Trashcan()
		return instance

	def __schedulePurge(self):
		if config.MVC.trashcan_enable.value and config.MVC.trashcan_clean.value:
			# recall function in 24 hours
			seconds = 24 * 60 * 60
			DelayedFunction(1000 * seconds, self.__schedulePurge)
			# execute trash cleaning
			DelayedFunction(5000, self.purgeTrashcan)
			print("MVC-I: Trashcan: scheduleCleanup: next trashcan cleanup in %s minutes" % (seconds / 60))

	def __createTrashcan(self):
		print("MVC-I: Trashcan: __createTrashcan")
		for bookmark in self.getBookmarks():
			path = bookmark + "/trashcan"
			if not FileCache.getInstance().exists(path):
				try:
					os.makedirs(path)
					FileCache.getInstance().makeDir(path)
					config.trashcan_enable.value = True
				except IOError as e:
					print("MVC-E: Trashcan: __createTrashcan: exception: %s" % e)
					config.MVC.trashcan_enable.value = False
					return RC_TRASHCAN_CREATE_DIR_FAILED
		return RC_TRASHCAN_CREATED

	def enableTrashcan(self):
		print("MVC-I: Trashcan: enable")
		rc = 0
		if not config.MVC.trashcan_enable.value:
			rc = self.__createTrashcan()
		return rc

	def purgeTrashcan(self, empty_trash=False, callback=None):
		import time
		print("MVC-I: Trashcan: purgeTrashcan: empty_trash: %s" % empty_trash)
		files = 0
		now = time.localtime()
		filelist = FileCache.getInstance().getFileList([self.getBookmarks()[0] + "/trashcan"])
		for afile in filelist:
			path = afile[FILE_IDX_PATH]
			file_type = afile[FILE_IDX_TYPE]
			# Only check media files
			_filename, ext = os.path.splitext(path)
			if ext in extVideo and os.path.exists(path):
				if empty_trash or now > time.localtime(os.stat(path).st_mtime + 24 * 60 * 60 * int(config.MVC.trashcan_retention.value)):
					#print("MVC: Trashcan: purgeTrashcan: path: " + path)
					self.execFileOp(FILE_OP_DELETE, path, None, file_type, callback)
					files += 1
		print("MVC-I: Trashcan: purgeTrashcan: deleted %s files" % files)
