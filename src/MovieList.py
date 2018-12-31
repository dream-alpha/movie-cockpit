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
from ServiceCenter import ServiceCenter
from MovieListGUI import MovieListGUI
from MovieCache import MovieCache,\
	TYPE_ISDIR, TYPE_ISLINK,\
	FILE_IDX_DATE, FILE_IDX_NAME, FILE_IDX_PATH, FILE_IDX_DESCRIPTION, FILE_IDX_LENGTH, FILE_IDX_EXT, FILE_IDX_TYPE, FILE_IDX_DIR
from MediaTypes import extVideo, plyDVB, plyM2TS, plyDVD, sidDVB, sidDVD, sidM2TS
from datetime import datetime

virAll = frozenset([TYPE_ISDIR, TYPE_ISLINK])
virToE = frozenset([])

class MovieList(MovieListGUI, object):

	def __init__(self, sort_mode):
		#print("MVC: MovieList: __init__")

		self.sort_mode = sort_mode
		self.list = []
		self.selection_list = []

		self.highlights_move = []
		self.highlights_delete = []
		self.highlights_copy = []

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
				print("MVC-E: MovieList: selectionChanged: exception:\n" + str(e))
				pass

	def getCurrentPath(self):
		l = self.l.getCurrentSelection()
		return l and l[FILE_IDX_PATH]

	def getCurrentDir(self):
		l = self.l.getCurrentSelection()
		return l and l[FILE_IDX_DIR]

	def getCurrentIndex(self):
		return self.instance.getCurrentIndex()

	def getCurrentEvent(self):
		l = self.l.getCurrentSelection()
		service = self.getPlayerService(l[FILE_IDX_PATH], "", l[FILE_IDX_EXT])
		#print("MVC: MovieList: getCurrentEvent: service: %s" % (service.getPath() if service else None))
		return ServiceCenter.getInstance().info(service).getEvent()

	def postWidgetCreate(self, instance):
		instance.setWrapAround(True)
		instance.setContent(self.l)
		self.selectionChanged_conn = instance.selectionChanged.connect(self.selectionChanged)

	def preWidgetRemove(self, instance):
		instance.setContent(None)
		self.selectionChanged_conn = None

	def removeService(self, path):
		for l in self.list:
			if l[FILE_IDX_PATH] == path:
				self.list.remove(l)
				break
		self.l.setList(self.list)

	def removeServiceOfType(self, path, filetype):
		for l in self.list:
			if l[FILE_IDX_PATH] == path and l[FILE_IDX_TYPE] == filetype:
				self.list.remove(l)
				break
		self.l.setList(self.list)

	def __len__(self):
		return len(self.getList())

	def getSelectionList(self, including_current):
		if not self.selection_list and including_current:
			# if no selections made, select the current cursor position
			single = self.l.getCurrentSelection()
			if single:
				self.selection_list.append(single[FILE_IDX_PATH])
		return self.selection_list

	def resetSelectionList(self):
		#print("MVC: MovieList: resetSelectionList")
		self.selection_list = []
		self.invalidateList()

	def selectService(self, path):
		#print("MVC: MovieList: selectService: path: %s" % path)
		self.selection_list.append(path)
		self.invalidateService(path)

	def unselectService(self, path):
		#print("MVC: MovieList: unselectService: path: %s" % path)
		if path in self.selection_list:
			self.selection_list.remove(path)
			self.invalidateService(path)

	def selectSelectionList(self):
		#print("MVC: MovieList: selectSelectionList")
		for movie in self.list:
			self.selectService(movie[FILE_IDX_PATH])

	def invalidateCurrent(self):
		self.l.invalidateEntry(self.getCurrentIndex())

	def invalidateService(self, path):
		index = self.getIndexOfService(path)
		if index >= 0:
			self.l.invalidateEntry(index)  # force redraw of the item

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
		index = self.getIndexOfService(path)
		if index >= 0:
			self.instance.moveSelectionTo(index)
		else:
			self.moveTop()

	def currentSelIsPlayable(self):
		return self.getExtOfIndex(self.getCurrentIndex()) in extVideo

	def currentSelIsDirectory(self):
		return self.getTypeOfIndex(self.getCurrentIndex()) == TYPE_ISDIR

	def currentSelIsVirtual(self):
		return self.getTypeOfIndex(self.getCurrentIndex()) in virAll

	def indexIsDirectory(self, index):
		return self.getTypeOfIndex(index) == TYPE_ISDIR

	def indexIsPlayable(self, index):
		return self.getExtOfIndex(index) in extVideo

	def getCurrentSelDescription(self):
		return self.getListEntry(self.getCurrentIndex())[FILE_IDX_DESCRIPTION]

	def getList(self):
		return self.list

	def getListEntry(self, index):
		return self.list[index]

	def getTypeOfIndex(self, index):
		return self.list[index][FILE_IDX_TYPE]

	def getTypeOfPath(self, path):
		file_type = None
		for entry in self.list:
			if entry[FILE_IDX_PATH] == path:
				file_type = entry[FILE_IDX_TYPE]
				break
		return file_type

	def getExtOfIndex(self, index):
		return self.list[index][FILE_IDX_EXT]

	def serviceBusy(self, path):
		return path in self.highlights_move or path in self.highlights_delete or path in self.highlights_copy

	def serviceMoving(self, path):
		return path and path in self.highlights_move

	def serviceDeleting(self, path):
		return path and path in self.highlights_delete

	def serviceCopying(self, path):
		return path and path in self.highlights_copy

	def getNameOfService(self, path):
		name = ""
		for entry in self.list:
			if path and entry[FILE_IDX_PATH] == path:
				name = entry[FILE_IDX_NAME]
				break
		return name

	def getLengthOfService(self, path):
		length = 0
		for entry in self.list:
			if path and entry[FILE_IDX_PATH] == path:
				length = entry[FILE_IDX_LENGTH]
				break
		return length

	def getIndexOfService(self, path):
		index = -1
		for i, entry in enumerate(self.list):
			if path and entry[FILE_IDX_PATH] == path:
				index = i
				break
		return index

	def getServiceOfPath(self, path):
		name = ""
		ext = ""
		for entry in self.list:
			if path and entry[FILE_IDX_PATH] == path:
				name = entry[FILE_IDX_NAME]
				ext = entry[FILE_IDX_EXT]
				break
		return self.getPlayerService(path, name, ext)

	def getServiceOfIndex(self, index):
		#print("MVC: MovieList: getServiceOfIndex: index: %s" % index)
		path = self.list[index][FILE_IDX_PATH]
		name = self.list[index][FILE_IDX_NAME]
		ext = self.list[index][FILE_IDX_EXT]
		return self.getPlayerService(path, name, ext)

	def getPathOfIndex(self, index):
		return self.list[index] and self.list[index][FILE_IDX_PATH]

	def getPlayerService(self, path, name="", ext=None):
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
		#print("MVC: MovieCache: getPlayerService: service valid = %s for %s" % (service.valid(), path))
		return service

	def createFileList(self, path):
		filelist = MovieCache.getInstance().getFileList([path], config.MVC.directories_show.value)
		return filelist

	def createCustomList(self, path):
		#print("MVC: MovieList: createCustomList: path: %s" % path)
		path = os.path.realpath(path)
		customlist = []

		if path not in self.getBookmarks():
			customlist.append(MovieCache.getInstance().getFile(os.path.join(path, "..")))

		if path in self.getBookmarks():
			path = self.getBookmarks()[0]
			if config.MVC.movie_trashcan_enable.value and config.MVC.movie_trashcan_show.value:
				customlist.append(MovieCache.getInstance().getFile(self.getBookmark(path) + "/trashcan"))

		#print("MVC: MovieList: createCustomList: customlist: " + str(customlist))
		return customlist

	def sortList(self, sortlist):

		def date2ms(date_string):
			return int(datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S").strftime('%s')) * 1000

		virToD = virToE if config.MVC.directories_ontop.value else virAll
		# This will find all unsortable items
		tmplist = [i for i in sortlist if i[FILE_IDX_TYPE] in virToD or i[FILE_IDX_NAME] == ".."]
		# Extract list items to be sorted
		sortlist = [i for i in sortlist if i[FILE_IDX_TYPE] not in virToD and i[FILE_IDX_NAME] != ".."]
		# Always sort via extension and sorttitle
		tmplist.sort(key=lambda x: (x[FILE_IDX_TYPE], x[FILE_IDX_NAME].lower()))

		mode, order = self.sort_mode

		if mode == "D": # Date sort
			if not order:
				sortlist.sort(key=lambda x: (x[FILE_IDX_DATE], x[FILE_IDX_NAME].lower()), reverse=True)
			else:
				sortlist.sort(key=lambda x: (x[FILE_IDX_DATE], x[FILE_IDX_NAME].lower()))

		elif mode == "A": # Alpha sort
			if not order:
				sortlist.sort(key=lambda x: (x[FILE_IDX_NAME].lower(), -date2ms(x[FILE_IDX_DATE])))
			else:
				sortlist.sort(key=lambda x: (x[FILE_IDX_NAME].lower(), x[FILE_IDX_DATE]), reverse=True)

		self.list = tmplist + sortlist
		self.l.setList(self.list)

	def reloadList(self, path, sort_mode):
		#print("MVC: MovieList: reloadList: path: %s" % path)
		self.sort_mode = sort_mode
		self.resetSelectionList()
		filelist = self.createFileList(path)
		customlist = self.createCustomList(path)
		self.sortList(customlist + filelist)

	def reloadListWithoutCache(self, path):
		# reload files and directories for current path without using cache
		MovieCache.getInstance().reloadDatabase()
		self.reloadList(path, self.sort_mode)

	def getNextSelectedService(self, selection_list):
		#print("MVC: MovieSelection: getNextSelectedService: selected_list: %s" % selection_list)
		# calc lowest selected index
		indexes = []
		for path in selection_list:
			#print("MVC: MovieSelection: getNextSelectedService: %s" % path)
			indexes.append(self.getIndexOfService(path))
		#print("MVC: MovieSelection: getNextSelectedService: indexes: %s" % indexes)
		indexes.sort()
		lowest_index = indexes[0]

		next_path = self.list[0][FILE_IDX_PATH]  # first service in list
		for i in range(lowest_index, len(self.list)):
			path = self.list[i][FILE_IDX_PATH]
			if path not in selection_list:
				next_path = path
				break
		#print("MVC: MovieSelection: getNextSelectedService: next_path: %s" % next_path)
		return next_path

	def bqtListFolders(self):
		return MovieCache.getInstance().getDirList(self.getBookmarks()[0]).sort()
