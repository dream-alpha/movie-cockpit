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
from SkinUtils import getSkinPath
from FileUtils import readFile
from Bookmarks import Bookmarks
from DelayedFunction import DelayedFunction
from FileCache import FileCache
from FileProgress import FileProgress

class FileCacheReload(FileProgress, Bookmarks, object):

	def __init__(self, session):
		#print("MVC: FileCacheReload: __init__")
		FileProgress.__init__(self, session)
		self.skinName = ["FileCacheReload"]
		self.skin = readFile(getSkinPath("FileCacheReload.xml"))
		self.setTitle(_("File cache reload") + " ...")
		self.execution_list = []
		self.onShow.append(self.onDialogShow)

	def onDialogShow(self):
		#print("MVC: FileCacheReload: onDialogShow")
		DelayedFunction(10, self.execFileCacheReload)

	def loadDatabaseDirs(self):
		file_dirs = self.getBookmarks()
		#print("MVC: FileCache: loadDatabaseDirs: loading directories: " + str(file_dirs))
		self.execution_list = FileCache.getInstance().getDirsLoadList(file_dirs)

	def doFileOp(self, entry):
		path, file_type = entry
		self.file_name = os.path.basename(path)
		self.status = _("Please wait") + " ..."
		self.updateProgress()
		FileCache.getInstance().addDatabaseFileType(path, file_type)
		DelayedFunction(10, self.nextFileOp)

	def execFileCacheReload(self):
		print("MVC-I: FileCacheReload: execFileCacheReload")
		self.status = _("Initializing") + " ..."
		self.updateProgress()
		FileCache.getInstance().clearDatabase()
		self.loadDatabaseDirs()
		self.total_files = len(self.execution_list)
		DelayedFunction(10, self.nextFileOp)
