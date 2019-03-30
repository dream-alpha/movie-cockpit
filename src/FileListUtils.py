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
from datetime import datetime
from Components.config import config
from FileCache import FileCache, FILE_TYPE_DIR, FILE_IDX_TYPE, FILE_IDX_DIR, FILE_IDX_NAME, FILE_IDX_DATE, FILE_IDX_PATH, FILE_IDX_EXT
from Bookmarks import Bookmarks
from ServiceUtils import getService
from ConfigInit import sort_modes

class FileListUtils(Bookmarks, object):

	def getEntry4Index(self, filelist, index):
		return filelist[index]

	def getEntry4Path(self, filelist, path):
		list_entry = None
		for entry in filelist:
			if entry and entry[FILE_IDX_PATH] == path:
				list_entry = entry
				break
		return list_entry

	def getIndex4Path(self, filelist, path):
		index = -1
		for i, entry in enumerate(filelist):
			if entry and entry[FILE_IDX_PATH] == path:
				index = i
				break
		return index

	def loadedDirs(self, filelist):
		loaded_dirs = []
		for afile in filelist:
			adir = afile[FILE_IDX_DIR]
			if adir not in loaded_dirs:
				loaded_dirs.append(adir)
		return loaded_dirs

	def getService4Path(self, filelist, path):
		service = None
		for entry in filelist:
			if entry and entry[FILE_IDX_PATH] == path:
				service = getService(path, entry[FILE_IDX_NAME], entry[FILE_IDX_EXT])
				break
		return service

	def createFileList(self, path):
		filelist = []
		if path:
			filelist = FileCache.getInstance().getFileList([path])
		return filelist

	def createDirList(self, path):
		filelist = []
		if path:
			filelist = FileCache.getInstance().getDirList([path])
		return filelist

	def createCustomList(self, path):
		#print("MVC: MovieSelection: createCustomList: path: %s" % path)
		filelist = []
		if path:
			if path not in self.getBookmarks():
				filelist.append(FileCache.getInstance().getFile(os.path.join(path, "..")))
			else:  # path is a bookmark
				if config.MVC.trashcan_enable.value and config.MVC.trashcan_show.value:
					filelist.append(FileCache.getInstance().getFile(path + "/trashcan"))
		#print("MVC: MovieSelection: createCustomList: filelist: " + str(filelist))
		return filelist

	def sortList(self, filelist, sort_mode):

		def date2ms(date_string):
			return int(datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S").strftime('%s')) * 1000

		filetype_list = [] if config.MVC.directories_ontop.value else [FILE_TYPE_DIR]
		# This will find all unsortable items
		tmp_list = [i for i in filelist if i and i[FILE_IDX_TYPE] in filetype_list or i[FILE_IDX_NAME] == ".."]
		# Extract list items to be sorted
		filelist = [i for i in filelist if i and i[FILE_IDX_TYPE] not in filetype_list and i[FILE_IDX_NAME] != ".."]
		# Always sort via extension and sorttitle
		tmp_list.sort(key=lambda x: (x[FILE_IDX_TYPE], x[FILE_IDX_NAME].lower()))

		mode, order = sort_modes[sort_mode][0]

		if mode == "date":
			if not order:
				filelist.sort(key=lambda x: (x[FILE_IDX_DATE], x[FILE_IDX_NAME].lower()), reverse=True)
			else:
				filelist.sort(key=lambda x: (x[FILE_IDX_DATE], x[FILE_IDX_NAME].lower()))

		elif mode == "alpha":
			if not order:
				filelist.sort(key=lambda x: (x[FILE_IDX_NAME].lower(), -date2ms(x[FILE_IDX_DATE])))
			else:
				filelist.sort(key=lambda x: (x[FILE_IDX_NAME].lower(), x[FILE_IDX_DATE]), reverse=True)

		return tmp_list + filelist
