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
from __init__ import _
from Bookmarks import Bookmarks
from DelayedFunction import DelayedFunction
from FileCacheLoad import FileCacheLoad
from FileProgress import FileProgress

class FileCacheLoadProgress(FileProgress, Bookmarks, object):

	def __init__(self, session, return_path):
		#print("MVC: FileCacheLoadProgress: __init__")
		FileProgress.__init__(self, session, return_path)
		self.skinName = "MVCFileCacheLoadProgress"
		self.setTitle(_("File cache reload") + " ...")
		self.execution_list = []
		self.onShow.append(self.onDialogShow)

	def onDialogShow(self):
		#print("MVC: FileCacheLoadProgress: onDialogShow")
		DelayedFunction(10, self.execFileCacheLoadProgress)

	def doFileOp(self, entry):
		path, filetype = entry
		self.file_name = os.path.basename(path)
		self.status = _("Please wait") + " ..."
		self.updateProgress()
		FileCacheLoad.getInstance().loadDatabaseFile(path, filetype)
		DelayedFunction(10, self.nextFileOp)

	def execFileCacheLoadProgress(self):
		print("MVC-I: FileCacheLoadProgress: execFileCacheLoadProgress")
		self.status = _("Initializing") + " ..."
		self.updateProgress()
		FileCacheLoad.getInstance().clearDatabase()
		self.execution_list = FileCacheLoad.getInstance().getDirsLoadList(self.getBookmarks())
		self.total_files = len(self.execution_list)
		DelayedFunction(10, self.nextFileOp)
