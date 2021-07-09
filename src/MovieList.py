#!/usr/bin/python
# coding=utf-8
#
# Copyright (C) 2018-2021 by dream-alpha
#
# In case of reuse of this source code please do not remove this copyright.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# For more information on the GNU General Public License see:
# <http://www.gnu.org/licenses/>.


from Debug import logger
import os
from __init__ import _
from time import time
from datetime import datetime
from CutListUtils import ptsToSeconds, getCutListLast, unpackCutList
from SkinUtils import getSkinPath
from ServiceReference import ServiceReference
from Components.config import config
from Components.GUIComponent import GUIComponent
from Components.TemplatedMultiContentComponent import TemplatedMultiContentComponent
from Tools.LoadPixmap import LoadPixmap
from skin import parseColor  # , parseFont, parseSize
from enigma import eListbox, loadPNG
from Plugins.SystemPlugins.CacheCockpit.FileCache import FileCache, FILE_TYPE_FILE
from Plugins.SystemPlugins.CacheCockpit.FileCacheSQL import FILE_IDX_PATH, FILE_IDX_DIR
from RecordingUtils import isRecording
from FileUtils import readFile
from MovieListParseTemplate import parseTemplate
from ServiceCenter import Info
from FileOp import FILE_OP_COPY, FILE_OP_MOVE, FILE_OP_DELETE
from FileOpManager import FileOpManager
from MovieListUtils import getIndex4Path, createFileList, createDirList, createCustomList, sortList
from ConfigInit import sort_modes


class MovieList(TemplatedMultiContentComponent):

	COMPONENT_ID = ""
	default_template = readFile(getSkinPath("MovieListTemplate.py"))
	list_styles = {}

	GUI_WIDGET = eListbox
	selection_list = []
	lock_list = {}
	current_sort_mode = "0"

	def __init__(self, current_sort_mode):
		logger.debug("...")
		if not current_sort_mode:
			current_sort_mode = config.plugins.moviecockpit.list_sort.value
		MovieList.current_sort_mode = current_sort_mode
		self.file_list = []
		self.skinAttributes = None
		TemplatedMultiContentComponent.__init__(self)
		self.l.setBuildFunc(self.buildMovieListEntry)

		self.color = parseColor(config.plugins.moviecockpit.color.value).argb()
		self.color_sel = parseColor(config.plugins.moviecockpit.color_sel.value).argb()
		self.recording_color = parseColor(config.plugins.moviecockpit.recording_color.value).argb()
		self.recording_color_sel = parseColor(config.plugins.moviecockpit.recording_color_sel.value).argb()
		self.selection_color = parseColor(config.plugins.moviecockpit.selection_color.value).argb()
		self.selection_color_sel = parseColor(config.plugins.moviecockpit.selection_color_sel.value).argb()

		skin_path = getSkinPath("images/")
		self.pic_back = LoadPixmap(skin_path + "back.svg", cached=True)
		self.pic_directory = LoadPixmap(skin_path + "dir.svg", cached=True)
		self.pic_movie_default = LoadPixmap(skin_path + "movie_default.svg", cached=True)
		self.pic_movie_watching = LoadPixmap(skin_path + "movie_watching.svg", cached=True)
		self.pic_movie_finished = LoadPixmap(skin_path + "movie_finished.svg", cached=True)
		self.pic_movie_rec = LoadPixmap(skin_path + "movie_rec.svg", cached=True)
		self.pic_movie_cut = LoadPixmap(skin_path + "movie_cut.svg", cached=True)
		self.pic_bookmark = LoadPixmap(skin_path + "bookmark.svg", cached=True)
		self.pic_trashcan = LoadPixmap(skin_path + "trashcan.svg", cached=True)
		self.pic_progress_bar = LoadPixmap(skin_path + "progcl.svg", cached=True)
		self.pic_rec_progress_bar = LoadPixmap(skin_path + "rec_progcl.svg", cached=True)

		self.onSelectionChanged = []

	def postWidgetCreate(self, instance):
		instance.setWrapAround(True)
		instance.setContent(self.l)
		self.selectionChanged_conn = instance.selectionChanged.connect(self.selectionChanged)

	def preWidgetRemove(self, instance):
		instance.setContent(None)
		self.selectionChanged_conn = None

	def setListStyle(self, list_style):
		self.list_style = list_style
		config.plugins.moviecockpit.list_style.value = list_style
		config.plugins.moviecockpit.list_style.save()
		self.setTemplate(MovieList.list_styles[list_style][0])
		self.invalidateList()

	def toggleListStyle(self):
		index = self.list_style
		list_style = (index + 1) % len(MovieList.list_styles)
		self.setListStyle(list_style)

	def selectionChanged(self):
		logger.debug("...")
		for f in self.onSelectionChanged:
			try:
				f()
			except Exception as e:
				logger.error("f: %s, exception: %s", f, e)

### move functions

	def moveUp(self, n=1):
		for _i in range(int(n)):
			self.instance.moveSelection(self.instance.moveUp)

	def moveDown(self, n=1):
		for _i in range(int(n)):
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
		index = getIndex4Path(self.file_list, path)
		self.moveToIndex(index)

	def moveBouquetPlus(self):
		if config.plugins.moviecockpit.list_bouquet_keys.value == "":
			self.moveTop()
		elif config.plugins.moviecockpit.list_bouquet_keys.value == "Skip":
			self.moveUp(config.plugins.moviecockpit.list_skip_size.value)

	def moveBouquetMinus(self):
		if config.plugins.moviecockpit.list_bouquet_keys.value == "":
			self.moveEnd()
		elif config.plugins.moviecockpit.list_bouquet_keys.value == "Skip":
			self.moveDown(config.plugins.moviecockpit.list_skip_size.value)

### selection functions

	def getSelectionList(self):
		if not MovieList.selection_list:
			# if no selections were made, add the current cursor position
			path = self.getCurrentPath()
			if path and not path.endswith("..") and path not in MovieList.lock_list:
				self.selectPath(path)
				self.moveDown()
		selection_list = MovieList.selection_list[:]
		return selection_list

	def selectPath(self, path):
		logger.debug("path: %s", path)
		if not path.endswith("..") and path not in MovieList.selection_list:
			MovieList.selection_list.append(path)
			index = getIndex4Path(self.file_list, path)
			self.invalidateEntry(index)

	def unselectPath(self, path):
		logger.debug("path: %s", path)
		if path in MovieList.selection_list:
			MovieList.selection_list.remove(path)
			index = getIndex4Path(self.file_list, path)
			self.invalidateEntry(index)

	def selectAll(self):
		logger.debug("...")
		for afile in self.file_list:
			self.selectPath(afile[FILE_IDX_PATH])

	def unselectAll(self):
		logger.debug("...")
		selection_list = MovieList.selection_list[:]
		for path in selection_list:
			self.unselectPath(path)

	def toggleSelection(self):
		path = self.getCurrentPath()
		logger.debug("path: %s", path)
		logger.debug("selection_list: %s", MovieList.selection_list)
		if path in MovieList.selection_list and path not in MovieList.lock_list:
			self.unselectPath(path)
		else:
			self.selectPath(path)

### sort functions

	def updateSortMode(self):
		self.loadList(self.getCurrentDir(), self.getCurrentPath())

	def toggleSortMode(self):
		MovieList.current_sort_mode = str((int(MovieList.current_sort_mode) + 2) % len(sort_modes))
		self.updateSortMode()

	def toggleSortOrder(self):
		mode, order = sort_modes[MovieList.current_sort_mode][0]
		order = not order
		for sort_mode in sort_modes:
			if sort_modes[sort_mode][0] == (mode, order):
				MovieList.current_sort_mode = sort_mode
				break
		self.updateSortMode()

### list functions

	def getCurrentPath(self):
		path = ""
		current_selection = self.l.getCurrentSelection()
		if current_selection:
			path = current_selection[FILE_IDX_PATH]
		return path

	def getCurrentDir(self):
		directory = ""
		current_selection = self.l.getCurrentSelection()
		if current_selection:
			directory = current_selection[FILE_IDX_DIR]
		return directory

	def getCurrentIndex(self):
		return self.instance.getCurrentIndex()

	def getCurrentSelection(self):
		return self.l.getCurrentSelection()

	def invalidateList(self):
		self.l.invalidate()

	def invalidateEntry(self, i):
		self.l.invalidateEntry(i)

	def loadList(self, adir=None, return_path=None):
		logger.info("adir: %s", adir)
		if adir is None:
			adir = self.getCurrentDir()
		logger.info("return_path: %s", return_path)
		if return_path is None:
			return_path = self.getCurrentPath()
		MovieList.lock_list = FileOpManager.getInstance().getLockList()
		MovieList.selection_list = []
		file_list = createFileList(adir)
		if config.plugins.moviecockpit.directories_show.value:
			file_list += createDirList(adir)
		custom_list = createCustomList(adir)
		self.file_list = custom_list + sortList(file_list, MovieList.current_sort_mode)
		self.l.setList(self.file_list)
		self.moveToPath(return_path)

### skin functions

	def applySkin(self, desktop, parent):
# 		attribs = []
# 		value_attributes = [
# 		]
# 		size_attributes = [
# 		]
# 		font_attributes = [
# 		]
# 		color_attributes = [
# 		]
#
# 		if self.skinAttributes:
# 			for (attrib, value) in self.skinAttributes:
# 				if attrib in value_attributes:
# 					setattr(self, attrib, int(value))
# 				elif attrib in size_attributes:
# 					setattr(self, attrib, parseSize(value, ((1, 1), (1, 1))))
# 				elif attrib in font_attributes:
# 					setattr(self, attrib, parseFont(value, ((1, 1), (1, 1))))
# 				elif attrib in color_attributes:
# 					setattr(self, attrib, parseColor(value).argb())
# 				else:
# 					attribs.append((attrib, value))
# 		self.skinAttributes = attribs

		MovieList.list_styles, template_attributes = parseTemplate(MovieList.default_template)
		self.setListStyle(config.plugins.moviecockpit.list_style.value)

		logger.debug("self.skinAttributes: %s", str(self.skinAttributes))
		GUIComponent.applySkin(self, desktop, parent)

		template_attributes["width"] = self.l.getItemSize().width() - 15
		self.applyTemplate(additional_locals=template_attributes)

### list build function

	def buildMovieListEntry(self, _directory, file_type, path, _file_name, _ext, name, event_start_time, _recording_start_time, _recording_stop_time, length, description, _extended_description, service_reference, _size, cuts, tags):

		def isCutting(path):
			logger.debug("isCutting: path: %s", path)
			file_name, _ext = os.path.splitext(path)
			return file_name.endswith("_") and not os.path.exists(file_name + ".eit")

		def getPicon(service_reference):
			pos = service_reference.rfind(':')
			if pos != -1:
				service_reference = service_reference[:pos].rstrip(':').replace(':', '_')
			picon_path = os.path.join(config.plugins.moviecockpit.movie_picons_path.value, service_reference + '.png')
			logger.debug("picon_path: %s", picon_path)
			return loadPNG(picon_path)

		def getDateText(path, file_type, date):
			logger.debug("path: %s, file_type: %s, date: %s", path, file_type, date)
			count = 0
			date_text = ""
			if path in MovieList.lock_list:
				file_op = MovieList.lock_list[path]
				if file_op == FILE_OP_COPY:
					date_text = _("COPYING")
				elif file_op == FILE_OP_MOVE:
					date_text = _("MOVING")
				elif file_op == FILE_OP_DELETE:
					date_text = _("DELETING")
			else:
				if file_type == FILE_TYPE_FILE:
					if config.plugins.moviecockpit.movie_mount_points.value:
						words = path.split("/")
						if len(words) > 3 and words[1] == "media":
							date_text = words[2]
					else:
						date_text = datetime.fromtimestamp(date).strftime(config.plugins.moviecockpit.movie_date_format.value)
				else:
					if os.path.basename(path) == "trashcan":
						info_value = config.plugins.moviecockpit.trashcan_info.value
					else:
						info_value = config.plugins.moviecockpit.directories_info.value
					if os.path.basename(path) == "..":
						date_text = _("up")
					else:
						if info_value == "D":
							if os.path.basename(path) == "trashcan":
								date_text = _("trashcan")
							else:
								date_text = _("directory")
						else:
							count, size = FileCache.getInstance().getCountSize(path)
							counttext = "%d" % count

							size /= (1024 * 1024 * 1024)  # GB
							sizetext = "%.0f GB" % size
							if size >= 1024:
								sizetext = "%.1f TB" % (size / 1024)

							if info_value == "C":
								date_text = "(%s)" % counttext
							elif info_value == "S":
								date_text = "(%s)" % sizetext
							elif info_value == "CS":
								date_text = "(%s/%s)" % (counttext, sizetext)
			logger.debug("count: %s, date_text: %s", count, date_text)
			return date_text

		def getProgress(recording, path, length, cuts):
			logger.debug("path: %s", path)

			if recording:
				info = Info(path)
				last = time() - info.getEventStartTime()
				length = info.getLength()
			else:
				# get last position from cut file
				cut_list = unpackCutList(cuts)
				logger.debug("cut_list: %s", str(cut_list))
				last = ptsToSeconds(getCutListLast(cut_list))
				logger.debug("last: %s", str(last))

			progress = 0
			if length > 0 and last > 0:
				if last > length:
					last = length
				progress = int(round(float(last) / float(length), 2) * 100)

			logger.debug("progress: %s, path: %s, length: %s, recording: %s", progress, path, length, recording)
			return progress

		def getFileIcon(path, file_type, progress, recording, cutting):
			pixmap = None
			if file_type == FILE_TYPE_FILE:
				pixmap = self.pic_movie_default
				if recording:
					pixmap = self.pic_movie_rec
				elif cutting:
					pixmap = self.pic_movie_cut
				else:
					if progress >= int(config.plugins.moviecockpit.movie_finished_percent.value):
						pixmap = self.pic_movie_finished
					elif progress >= int(config.plugins.moviecockpit.movie_watching_percent.value):
						pixmap = self.pic_movie_watching
			else:
				pixmap = self.pic_directory
				if os.path.basename(path) == "trashcan":
					pixmap = self.pic_trashcan
				elif os.path.basename(path) == "..":
					pixmap = self.pic_back
			return pixmap

		def getColor(path, file_type, recording, cutting):
			if path in MovieList.selection_list or path in MovieList.lock_list:
				color = self.selection_color
				color_sel = self.selection_color_sel
			else:
				if file_type == FILE_TYPE_FILE:
					if recording or cutting:
						color = self.recording_color
						color_sel = self.recording_color_sel
					else:
						color = self.color
						color_sel = self.color_sel
				else:
					color = self.color_sel
					color_sel = self.color_sel
			return color, color_sel

		logger.debug("list_style: %s", MovieList.list_styles[self.list_style][0])

		service = ServiceReference(service_reference)
		service_name = service.getServiceName() if service is not None else ""
		recording = isRecording(path)
		cutting = isCutting(path)
		color, color_sel = getColor(path, file_type, recording, cutting)
		progress = getProgress(recording, path, length, cuts) if file_type == FILE_TYPE_FILE else -1
		progress_string = str(progress) + "%" if progress >= 0 else ""
		progress_bar = self.pic_rec_progress_bar if recording else self.pic_progress_bar
		length_string = str(length / 60) + " " + _("min") if file_type == FILE_TYPE_FILE else ""
		picon = getPicon(service_reference) if file_type == FILE_TYPE_FILE else None
		name = _(name) if name == "trashcan" else name

		res = [
			None,
			name,								#  1: name
			tags,								#  2: tags
			service_name,							#  3: service name
			description,							#  4: short description
			getDateText(path, file_type, event_start_time),			#  5: event start time
			length_string,							#  6: length
			color,								#  7: color
			color_sel,							#  8: color_sel
			progress,							#  9: progress percent (-1 = don't show)
			progress_string,						# 10: progress (xx%)
			progress_bar,							# 11: progress bar png
			getFileIcon(path, file_type, progress, recording, cutting),	# 12: status icon png
			picon,								# 13: picon png
		]

		logger.debug("self.res: %s", str(res))
		return res
