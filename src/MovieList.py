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
from enigma import eServiceReference
from Components.config import config
from enigma import eListboxPythonMultiContent, gFont
from MovieListGUI import MovieListGUI
from FileCache import FileCache,\
	FILE_TYPE_IS_DIR, FILE_IDX_DATE, FILE_IDX_NAME, FILE_IDX_PATH, FILE_IDX_EXT, FILE_IDX_TYPE, FILE_IDX_DIR
from MediaTypes import plyDVB, plyM2TS, plyDVD, sidDVB, sidDVD, sidM2TS
from datetime import datetime


class MovieList(MovieListGUI, object):

	def __init__(self, sort_mode):
		#print("MVC: MovieList: __init__")
		self.sort_mode = sort_mode
		self.list = []
		self.selection_list = []

		MovieListGUI.__init__(self)

		self.l = eListboxPythonMultiContent()
		self.l.setFont(0, gFont("Regular", 22))
		self.l.setFont(1, self.MVCFont)
		self.l.setFont(2, gFont("Regular", 20))
		self.l.setFont(3, self.MVCSelectFont)
		self.l.setFont(4, self.MVCDateFont)
		self.l.setBuildFunc(self.buildMovieListEntry)

		self.onSelectionChanged = []
		self.l.setList(self.getList())

	def selectionChanged(self):
		#print("MVC: MovieList: selectionChanged")
		for f in self.onSelectionChanged:
			try:
				f()
			except Exception as e:
				print("MVC-E: MovieList: selectionChanged: exception: %s" % e)

	def getCurrentPath(self):
		l = self.l.getCurrentSelection()
		return l and l[FILE_IDX_PATH]

	def getCurrentDir(self):
		l = self.l.getCurrentSelection()
		return l and l[FILE_IDX_DIR]

	def getCurrentIndex(self):
		return self.instance.getCurrentIndex()

	def postWidgetCreate(self, instance):
		instance.setWrapAround(True)
		instance.setContent(self.l)
		self.selectionChanged_conn = instance.selectionChanged.connect(self.selectionChanged)

	def preWidgetRemove(self, instance):
		instance.setContent(None)
		self.selectionChanged_conn = None

	def getList(self):
		return self.list

	def __len__(self):
		return len(self.getList())

	def getSelectionList(self, including_current):
		if not self.selection_list and including_current:
			# if no selections made, select the current cursor position
			single = self.l.getCurrentSelection()
			if single:
				self.selection_list.append(single[FILE_IDX_PATH])
		return self.selection_list

	def unselectAll(self):
		#print("MVC: MovieList: unselectAll")
		self.selection_list = []
		self.invalidateList()

	def selectPath(self, path):
		#print("MVC: MovieList: selectPath: path: %s" % path)
		self.selection_list.append(path)
		self.invalidatePath(path)

	def unselectPath(self, path):
		#print("MVC: MovieList: unselectPath: path: %s" % path)
		if path in self.selection_list:
			self.selection_list.remove(path)
			self.invalidatePath(path)

	def selectAll(self):
		#print("MVC: MovieList: selectAll")
		for entry in self.list:
			self.selectPath(entry[FILE_IDX_PATH])

	def invalidateCurrent(self):
		self.l.invalidateEntry(self.getCurrentIndex())

	def invalidatePath(self, path):
		for i, entry in enumerate(self.list):
			if entry and entry[FILE_IDX_PATH] == path:
				self.l.invalidateEntry(i)
				break

	def invalidateList(self):
		self.selection_list = []
		self.l.invalidate()

	def moveUp(self):
		self.instance.moveSelection(self.instance.moveUp)

	def moveDown(self):
		self.instance.moveSelection(self.instance.moveDown)

	def pageUp(self):
		self.instance.moveSelection(self.instance.pageUp)

	def pageDown(self):
		self.instance.moveSelection(self.instance.pageDown)

	def moveTop(self):
		self.instance.moveSelection(self.instance.moveTop)

	def moveEnd(self):
		self.instance.moveSelection(self.instance.moveEnd)

	def moveToIndex(self, index):
		self.instance.moveSelectionTo(index)

	def moveToPath(self, path):
		index = 0
		for i, entry in enumerate(self.list):
			if entry and entry[FILE_IDX_PATH] == path:
				index = i
				break
		self.moveToIndex(index)

	def getEntry4Index(self, index):
		return self.list[index]

	def getEntry4Path(self, path):
		list_entry = None
		for entry in self.list:
			if entry and entry[FILE_IDX_PATH] == path:
				list_entry = entry
				break
		return list_entry

	def getIndex4Path(self, path):
		index = -1
		for i, entry in enumerate(self.list):
			if entry and entry[FILE_IDX_PATH] == path:
				index = i
				break
		return index

	def getService4Path(self, path):
		service = None
		for entry in self.list:
			if entry and entry[FILE_IDX_PATH] == path:
				service = self.getService(path, entry[FILE_IDX_NAME], entry[FILE_IDX_EXT])
				break
		return service

	def getService(self, path, name="", ext=None):
		if ext in plyDVB:
			service = eServiceReference(sidDVB, 0, path)
		elif ext in plyDVD:
			service = eServiceReference(sidDVD, 0, path)
		elif ext in plyM2TS:
			service = eServiceReference(sidM2TS, 0, path)
		else:
			ENIGMA_SERVICE_ID = 0
			DEFAULT_VIDEO_PID = 0x44
			DEFAULT_AUDIO_PID = 0x45
			service = eServiceReference(ENIGMA_SERVICE_ID, 0, path)
			service.setData(0, DEFAULT_VIDEO_PID)
			service.setData(1, DEFAULT_AUDIO_PID)
		service.setName(name)
		#print("MVC: MovieList: getService: service valid = %s for %s" % (service.valid(), path))
		return service

	def createFileList(self, path):
		file_list = FileCache.getInstance().getFileList([path], config.MVC.directories_show.value)
		return file_list

	def createCustomList(self, path):
		#print("MVC: MovieList: createCustomList: path: %s" % path)
		custom_list = []
		if path not in self.getBookmarks():
			custom_list.append(FileCache.getInstance().getFile(os.path.join(path, "..")))
		else:  # path is a bookmark
			if config.MVC.trashcan_enable.value and config.MVC.trashcan_show.value:
				custom_list.append(FileCache.getInstance().getFile(path + "/trashcan"))
		#print("MVC: MovieList: createCustomList: custom_list: " + str(custom_list))
		return custom_list

	def sortList(self, sort_list):

		def date2ms(date_string):
			return int(datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S").strftime('%s')) * 1000

		filetype_list = [] if config.MVC.directories_ontop.value else [FILE_TYPE_IS_DIR]
		# This will find all unsortable items
		tmp_list = [i for i in sort_list if i and i[FILE_IDX_TYPE] in filetype_list or i[FILE_IDX_NAME] == ".."]
		# Extract list items to be sorted
		sort_list = [i for i in sort_list if i and i[FILE_IDX_TYPE] not in filetype_list and i[FILE_IDX_NAME] != ".."]
		# Always sort via extension and sorttitle
		tmp_list.sort(key=lambda x: (x[FILE_IDX_TYPE], x[FILE_IDX_NAME].lower()))

		mode, order = self.sort_mode

		if mode == "D": # Date sort
			if not order:
				sort_list.sort(key=lambda x: (x[FILE_IDX_DATE], x[FILE_IDX_NAME].lower()), reverse=True)
			else:
				sort_list.sort(key=lambda x: (x[FILE_IDX_DATE], x[FILE_IDX_NAME].lower()))

		elif mode == "A": # Alpha sort
			if not order:
				sort_list.sort(key=lambda x: (x[FILE_IDX_NAME].lower(), -date2ms(x[FILE_IDX_DATE])))
			else:
				sort_list.sort(key=lambda x: (x[FILE_IDX_NAME].lower(), x[FILE_IDX_DATE]), reverse=True)

		return tmp_list + sort_list

	def reloadList(self, path, sort_mode):
		#print("MVC: MovieList: reloadList: path: %s" % path)
		self.sort_mode = sort_mode
		self.unselectAll()
		file_list = self.createFileList(path)
		custom_list = self.createCustomList(path)
		self.list = custom_list + self.sortList(file_list)
		self.l.setList(self.list)

	def getDirList(self):
		return FileCache.getInstance().getDirList(self.getBookmarks()[0]).sort()
