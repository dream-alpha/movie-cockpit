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
from FileCache import FileCache, FILE_TYPE_FILE, FILE_IDX_PATH, FILE_IDX_DIR
from RecordingUtils import isCutting, isRecording
from MountPoints import getMountPoint
from FileUtils import readFile
from MovieListParseTemplate import parseTemplate
from ServiceCenter import Info


class MovieList(TemplatedMultiContentComponent):

	COMPONENT_ID = ""
	default_template = readFile(getSkinPath("MovieListTemplate.py"))
	list_styles = {}

	GUI_WIDGET = eListbox
	selection_list = []

	def __init__(self):
		#print("MVC: MovieList: __init__")
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

	def getListStyle(self):
		return self.list_style

	def setListStyle(self, list_style):
		self.list_style = list_style
		self.setTemplate(MovieList.list_styles[list_style][0])
		self.invalidateList()

	def selectionChanged(self):
		#print("MVC: MovieList: selectionChanged")
		for f in self.onSelectionChanged:
			try:
				f()
			except Exception as e:
				print("MVC-E: MovieList: selectionChanged: f: %s, exception: %s" % (f, e))

	def moveUp(self):
		self.instance.moveSelection(self.instance.moveUp)
		return self.getCurrentPath()

	def moveDown(self):
		self.instance.moveSelection(self.instance.moveDown)
		return self.getCurrentPath()

	def pageUp(self):
		self.instance.moveSelection(self.instance.pageUp)
		return self.getCurrentPath()

	def pageDown(self):
		self.instance.moveSelection(self.instance.pageDown)
		return self.getCurrentPath()

	def moveTop(self):
		self.instance.moveSelection(self.instance.moveTop)
		return self.getCurrentPath()

	def moveEnd(self):
		self.instance.moveSelection(self.instance.moveEnd)
		return self.getCurrentPath()

	def moveToIndex(self, index):
		self.instance.moveSelectionTo(index)
		return self.getCurrentPath()

	def setList(self, filelist):
		self.l.setList(filelist)

	def getCurrent(self):
		return self.l.getCurrentSelection()

	def getCurrentPath(self):
		return self.l.getCurrentSelection()[FILE_IDX_PATH]

	def getCurrentDir(self):
		return self.l.getCurrentSelection()[FILE_IDX_DIR]

	def getCurrentIndex(self):
		return self.instance.getCurrentIndex()

	def getCurrentSelection(self):
		return self.l.getCurrentSelection()

	def invalidate(self):
		self.l.invalidate()

	def invalidateList(self):
		self.invalidate()

	def invalidateEntry(self, i):
		self.l.invalidateEntry(i)

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

		#print("MVC: MovieList: applySkin: self.skinAttributes: " + str(self.skinAttributes))
		GUIComponent.applySkin(self, desktop, parent)

		template_attributes["width"] = self.l.getItemSize().width() - 15
		self.applyTemplate(additional_locals=template_attributes)

	def buildMovieListEntry(self, _directory, filetype, path, _filename, _ext, name, event_start_time, _recording_start_time, _recording_stop_time, length, description, _extended_description, service_reference, _size, cuts, tags):

		def getPicon(service_reference):
			pos = service_reference.rfind(':')
			if pos != -1:
				service_reference = service_reference[:pos].rstrip(':').replace(':', '_')
			picon_path = os.path.join(config.plugins.moviecockpit.movie_picons_path.value, service_reference + '.png')
			#print("MVC: MovieList: buildMovieListEntry: picon_path: " + picon_path)
			return loadPNG(picon_path)

		def getDateText(path, filetype, date):
			#print("MVC: MovieList: getDateText: path: %s, filetype: %s, date: %s" % (path, filetype, date))
			count = 0
			date_text = ""
			if filetype == FILE_TYPE_FILE:
				date_text = datetime.fromtimestamp(date).strftime(config.plugins.moviecockpit.movie_date_format.value)
				if config.plugins.moviecockpit.movie_mountpoints.value:
					date_text = getMountPoint(path)
			else:
				if os.path.basename(path) == "trashcan":
					info_value = config.plugins.moviecockpit.trashcan_info.value
				else:
					info_value = config.plugins.moviecockpit.directories_info.value
				if os.path.basename(path) == "..":
					date_text = _("up")
				else:
					if info_value:
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
								sizetext = "%.1f TB" % size / 1024

							if info_value == "C":
								date_text = "(%s)" % counttext
							elif info_value == "S":
								date_text = "(%s)" % sizetext
							elif info_value == "CS":
								date_text = "(%s/%s)" % (counttext, sizetext)
			#print("MVC: MovieList: getValues: count: %s, date_text: %s" % (count, date_text))
			return date_text

		def getProgress(recording, path, length, cuts):
			# All calculations are done in seconds
			#print("MVC: MovieList: getProgress: path: %s" % path)

			# first get last and length
			if recording:
				info = Info(path)
				last = time() - info.getEventStartTime()
				length = info.getLength()
			else:
				# Get last position from cut file
				cut_list = unpackCutList(cuts)
				#print("MVC: MovieList: getProgress: cut_list: " + str(cut_list))
				last = ptsToSeconds(getCutListLast(cut_list))
				#print("MVC: MovieList: getProgress: last: " + str(last))

			# second calculate progress
			progress = 0
			if length > 0 and last > 0:
				if last > length:
					last = length
				progress = int(round(float(last) / float(length), 2) * 100)

			#print("MVC: MovieList: getProgress: progress: %s, path: %s, length: %s, recording: %s" % (progress, path, length, recording))
			return progress

		def getFileIcon(path, filetype, progress, recording, cutting):
			pixmap = None
			if filetype == FILE_TYPE_FILE:
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

		def getColor(path, filetype, recording, cutting):
			if path in MovieList.selection_list:
				color = self.selection_color
				color_sel = self.selection_color_sel
			else:
				if filetype == FILE_TYPE_FILE:
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

		#print("MVC: MovieList: buildMovieListEntry: list_style: %s" % MovieList.list_styles[self.list_style][0])

		service = ServiceReference(service_reference)
		service_name = service.getServiceName() if service is not None else ""
		recording = isRecording(path)
		cutting = isCutting(path)
		color, color_sel = getColor(path, filetype, recording, cutting)
		progress = getProgress(recording, path, length, cuts) if filetype == FILE_TYPE_FILE else -1
		progress_string = str(progress) + "%" if progress >= 0 else ""
		progress_bar = self.pic_rec_progress_bar if recording else self.pic_progress_bar
		length_string = str(length / 60) + " " + _("min") if filetype == FILE_TYPE_FILE else ""
		picon = getPicon(service_reference) if filetype == FILE_TYPE_FILE else None
		name = _(name) if name == "trashcan" else name

		res = [
			None,
			name,								#  1: name
			tags,								#  2: tags
			service_name,							#  3: service name
			description,							#  4: short description
			getDateText(path, filetype, event_start_time),			#  5: event start time
			length_string,							#  6: length
			color,								#  7: color
			color_sel,							#  8: color_sel
			progress,							#  9: progress percent (-1 = don't show)
			progress_string,						# 10: progress (xx%)
			progress_bar,							# 11: progress bar png
			getFileIcon(path, filetype, progress, recording, cutting),	# 12: status icon png
			picon,								# 13: picon png
		]

		#print("MVC: MovieList: buildMovieListEntry: self.res: " + str(res))
		return res
