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
from time import time
from CutListUtils import ptsToSeconds, getCutListLast, unpackCutList
from MediaTypes import extTS, extVideo
from SkinUtils import getSkinPath
from Components.config import config
from Components.GUIComponent import GUIComponent
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaBlend
from Tools.LoadPixmap import LoadPixmap
from skin import parseColor, parseFont, parseSize
from enigma import eListboxPythonMultiContent, eListbox, RT_HALIGN_LEFT, RT_HALIGN_CENTER, loadPNG
from FileCache import FileCache, FILE_TYPE_IS_FILE, FILE_TYPE_IS_DIR
from ServiceCenter import str2date
from RecordingUtils import isCutting, getRecording
from MountPoints import MountPoints


class MovieListGUI(GUIComponent, MountPoints, object):
	GUI_WIDGET = eListbox

	def __init__(self):
		#print("MVC: MovieListGUI: __init__")
		self.skinAttributes = None
		GUIComponent.__init__(self)

		self.MVCFont = parseFont("Regular;30", ((1, 1), (1, 1)))
		self.MVCSelectFont = parseFont("Regular;30", ((1, 1), (1, 1)))
		self.MVCDateFont = parseFont("Regular;28", ((1, 1), (1, 1)))

		self.MVCStartHPos = 10
		self.MVCSpacer = 10
		self.MVCMovieWidth = None
		self.MVCDateWidth = 230
		self.MVCBarSize = parseSize("90, 14", ((1, 1), (1, 1)))
		self.MVCIconSize = parseSize("45, 35", ((1, 1), (1, 1)))
		self.MVCRecIconSize = parseSize("230, 40", ((1, 1), (1, 1)))
		# MVCSelNumTxtWidth is equal to MVCIconSize.width()
		self.MVCPiconSize = parseSize("55, 35", ((1, 1), (1, 1)))

		self.BackColor = None
		self.BackColorHighlight = None
		self.DefaultColor = parseColor("#bababa").argb()
		self.DefaultColorHighlight = parseColor(config.MVC.color_highlight.value).argb()
		self.RecordingColor = parseColor(config.MVC.color_recording.value).argb()
		self.RecordingColorHighlight = parseColor(config.MVC.color_recording_highlight.value).argb()
		self.SelectionColor = parseColor(config.MVC.color_selected.value).argb()
		self.SelectionColorHighlight = parseColor(config.MVC.color_selected_highlight.value).argb()

		skin_path = getSkinPath("img/")
		self.pic_back = LoadPixmap(cached=True, path=skin_path + "back.svg")
		self.pic_directory = LoadPixmap(cached=True, path=skin_path + "dir.svg")
		self.pic_movie_default = LoadPixmap(cached=True, path=skin_path + "movie_default.svg")
		self.pic_movie_watching = LoadPixmap(cached=True, path=skin_path + "movie_watching.svg")
		self.pic_movie_finished = LoadPixmap(cached=True, path=skin_path + "movie_finished.svg")
		self.pic_movie_rec = LoadPixmap(cached=True, path=skin_path + "movie_rec.svg")
		self.pic_movie_cut = LoadPixmap(cached=True, path=skin_path + "movie_cut.svg")
		self.pic_e2bookmark = LoadPixmap(cached=True, path=skin_path + "e2bookmark.svg")
		self.pic_trashcan = LoadPixmap(cached=True, path=skin_path + "trashcan.svg")
		self.pic_progress_bar = LoadPixmap(cached=True, path=skin_path + "progcl.svg")
		self.pic_rec_progress_bar = LoadPixmap(cached=True, path=skin_path + "rec_progcl.svg")
		self.pic_recording = LoadPixmap(cached=True, path=skin_path + "recording.svg")
		self.pic_cutting = LoadPixmap(cached=True, path=skin_path + "cutting.svg")

	def applySkin(self, desktop, parent):
		attribs = []
		value_attributes = [
			"MVCSpacer", "MVCMovieWidth", "MVCDateWidth"
		]
		size_attributes = [
			"MVCBarSize", "MVCIconSize", "MVCRecIconSize", "MVCPiconSize"
		]
		font_attributes = [
			"MVCFont", "MVCSelectFont", "MVCDateFont"
		]
		color_attributes = [
			"DefaultColor", "BackColor", "BackColorHighlight", "DefaultColorHighlight", "RecordingColor", "SelectionColor", "SelectionColorHighlight"
		]

		if self.skinAttributes:
			for (attrib, value) in self.skinAttributes:
				if attrib in value_attributes:
					setattr(self, attrib, int(value))
				elif attrib in size_attributes:
					setattr(self, attrib, parseSize(value, ((1, 1), (1, 1))))
				elif attrib in font_attributes:
					setattr(self, attrib, parseFont(value, ((1, 1), (1, 1))))
				elif attrib in color_attributes:
					setattr(self, attrib, parseColor(value).argb())
				else:
					attribs.append((attrib, value))
		self.skinAttributes = attribs

		self.l.setFont(1, self.MVCFont)
		self.l.setFont(3, self.MVCSelectFont)
		self.l.setFont(4, self.MVCDateFont)

		#print("MVC: MovieListGUI: applySkin: attribs: " + str(attribs))
		return GUIComponent.applySkin(self, desktop, parent)

	def buildMovieListEntry(self, _directory, filetype, path, _filename, ext, name, date_string, length, _description, _extended_description, service_reference, _size, cuts, _tags):

		def yPos(ySize, yHeight):
			return (ySize - yHeight) / 2

		def getPiconPath(service_reference):
			piconpath = ""
			if config.MVC.movie_picons.value:
				metaref = service_reference
				pos = metaref.rfind(':')
				if pos != -1:
					metaref = metaref[:pos].rstrip(':').replace(':', '_')
				piconpath = config.MVC.movie_picons_path.value + "/" + metaref + '.png'
				#print("MVC: MovieListGUI: buildMovieListEntry: piconpath: " + piconpath)
			return piconpath

		def createProgress(progress, color, color_sel, recording):
			#print("MVC: MovieListGUI: buildMovieListEntry: createProgressBar: progress: %s, startHPos: %s" % (progress, self.startHPos))
			x = self.startHPos
			if config.MVC.movie_progress.value == "PB":
				y = yPos(self.l.getItemSize().height(), self.MVCBarSize.height())
				bar_pic = self.pic_rec_progress_bar if recording else self.pic_progress_bar
				self.res.append((eListboxPythonMultiContent.TYPE_PROGRESS_PIXMAP, x, y, self.MVCBarSize.width(), self.MVCBarSize.height(), progress, bar_pic, 1, color, color_sel, self.BackColor, None))
				self.startHPos = x + self.MVCBarSize.width() + self.MVCSpacer
			elif config.MVC.movie_progress.value == "P":
				y = yPos(self.l.getItemSize().height(), self.MVCFont.pointSize)
				self.res.append(MultiContentEntryText(pos=(x, y), size=(self.MVCBarSize.width(), self.l.getItemSize().height()), font=self.usedFont, flags=RT_HALIGN_CENTER, text="%d%%" % (progress), color=color, color_sel=color_sel))
				self.startHPos = x + self.MVCBarSize.width() + self.MVCSpacer

		def createTitle(title, filetype, color, color_sel):
			#print("MVC: MovieListGUI: buildMovieListEntry: createTitle: %s, startHPos: %s" % (title, self.startHPos))
			x = self.startHPos
			y = yPos(self.l.getItemSize().height(), self.MVCFont.pointSize)
			w = self.MVCMovieWidth
			if w is None:
				w = self.width - x - self.MVCDateWidth - self.MVCSpacer

			if filetype == FILE_TYPE_IS_FILE and (config.MVC.movie_progress.value == "PB" or config.MVC.movie_progress.value == "P"):
				w = w - self.MVCBarSize.width() - self.MVCSpacer

			self.res.append(MultiContentEntryText((x, y), (w, self.l.getItemSize().height()), font=self.usedFont, flags=RT_HALIGN_LEFT, text=title, color=color, color_sel=color_sel))
			self.startHPos = x + w + self.MVCSpacer

		def createIcon(pixmap):
			#print("MVC: MovieListGUI: buildMovieListEntry: createIcon: startHPos: %s" % self.startHPos)
			x = self.startHPos
			y = yPos(self.l.getItemSize().height(), self.MVCIconSize.height())

			self.res.append(MultiContentEntryPixmapAlphaBlend(pos=(x, y), size=(self.MVCIconSize.width(), self.MVCIconSize.height()), png=pixmap, **{}))
			self.startHPos = x + self.MVCIconSize.width() + self.MVCSpacer

		def createPicon(service_reference, ext):
			#print("MVC: MovieListGUI: buildMovieListEntry: createPicon: startHPos: %s" % self.startHPos)
			x = self.startHPos
			y = yPos(self.l.getItemSize().height(), self.MVCPiconSize.height())

			if ext in extTS:
				piconpath = getPiconPath(service_reference)
				self.res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, x, y, self.MVCPiconSize.width(), self.MVCPiconSize.height(), loadPNG(piconpath), None, None))
			self.startHPos = x + self.MVCPiconSize.width() + self.MVCSpacer

		def createDateText(date_text, color, color_sel, recording, cutting):
			#print("MVC: MovieListGUI: buildMovieListEntry: createDateText: %s, startHPos: %s" % (date_text, self.startHPos))
			x = self.startHPos
			y = yPos(self.l.getItemSize().height(), self.MVCDateFont.pointSize)

			halign = config.MVC.movie_date_text_alignment.value

			if recording or cutting:
				x = x + (self.MVCDateWidth - self.MVCRecIconSize.width()) / 2
				y = yPos(self.l.getItemSize().height(), self.MVCRecIconSize.height())
				icon = self.pic_recording if recording else self.pic_cutting
				self.res.append(MultiContentEntryPixmapAlphaBlend(pos=(x, y), size=(self.MVCRecIconSize.width(), self.MVCRecIconSize.height()), png=icon, **{}))
			else:
				self.res.append(MultiContentEntryText(pos=(x, y), size=(self.MVCDateWidth, self.l.getItemSize().height()), font=self.usedDateFont, text=date_text, color=color, color_sel=color_sel, flags=halign))
			self.startHPos = x + self.MVCDateWidth + self.MVCSpacer

		def getDateText(path, filetype, date_string):
			date_text = ""
			if filetype == FILE_TYPE_IS_FILE:
				date_text = str2date(date_string).strftime(config.MVC.movie_date_format.value)
				if config.MVC.movie_mountpoints.value:
					date_text = self.getMountPoint(path)
			else:
				if os.path.basename(path) == "trashcan":
					info_value = config.MVC.trashcan_info.value
				else:
					info_value = config.MVC.directories_info.value
				if info_value:
					if info_value == "D":
						if os.path.basename(path) == "..":
							date_text = _("up")
						elif os.path.basename(path) == "trashcan":
							date_text = _("trashcan")
						else:
							date_text = _("Directory")
					else:
						count, size = FileCache.getInstance().getCountSize(path)
						counttext = "%d" % count

						size /= (1024 * 1024 * 1024)  # GB
						sizetext = "%.0f GB" % size
						if size >= 1024:
							sizetext = "%.1f TB" % size / 1024

						#print("MVC: MovieListGUI: getValues: count: %s, size: %s" % (count, size))
						if info_value == "C":
							date_text = "(%s)" % counttext
						elif info_value == "S":
							date_text = "(%s)" % sizetext
						elif info_value == "CS":
							date_text = "(%s/%s)" % (counttext, sizetext)
			#print("MVC: MovieListGUI: getValues: count: %s, date_text: %s" % (count, date_text))
			return date_text

		def getProgress(recording, length, cuts):
			# All calculations are done in seconds
			#print("MVC: MovieListGUI: getProgress: path: %s" % path)

			# first get last and length
			if recording:
				begin, end, _service_ref = recording
				last = time() - begin
				length = end - begin
			else:
				# Get last position from cut file
				cut_list = unpackCutList(cuts)
				#print("MVC: MovieListGUI: getProgress: cut_list: " + str(cut_list))
				last = ptsToSeconds(getCutListLast(cut_list))
				#print("MVC: MovieListGUI: getProgress: last: " + str(last))

			# second calculate progress
			progress = 0
			if length > 0 and last > 0:
				if last > length:
					last = length
				progress = int(round(float(last) / float(length), 2) * 100)

			#print("MVC: MovieListGUI: getProgress: progress = %s, length = %s, recording = %s" % (progress, length, recording))
			return progress

		def getFileIcon(path, filetype, progress, recording, cutting):
			if filetype == FILE_TYPE_IS_FILE:
				pixmap = self.pic_movie_default
				if recording:
					pixmap = self.pic_movie_rec
				elif cutting:
					pixmap = self.pic_movie_cut
				else:
					movieWatching = False
					movieFinished = False
					if config.MVC.movie_progress.value:
						movieWatching = config.MVC.movie_progress.value and progress >= int(config.MVC.movie_watching_percent.value) and progress < int(config.MVC.movie_finished_percent.value)
						movieFinished = config.MVC.movie_progress.value and progress >= int(config.MVC.movie_finished_percent.value)
					if movieWatching:
						pixmap = self.pic_movie_watching
					elif movieFinished:
						pixmap = self.pic_movie_finished
			else:
				pixmap = self.pic_directory
				if os.path.basename(path) == "trashcan":
					pixmap = self.pic_trashcan
				elif os.path.basename(path) == "..":
					pixmap = self.pic_back
			return pixmap

		def getColor(path, filetype, recording, cutting):
			if path in self.selection_list:
				color = self.SelectionColor
				color_sel = self.SelectionColorHighlight
			else:
				if filetype == FILE_TYPE_IS_FILE:
					if recording or cutting:
						color = self.RecordingColor
						color_sel = self.RecordingColorHighlight
					else:
						color = self.DefaultColor
						color_sel = self.DefaultColorHighlight
				else:
					color = self.DefaultColorHighlight
					color_sel = self.DefaultColorHighlight
			return color, color_sel

		#print("MVC: MovieListGUI: buildMovieListEnty: itemSize.width(): %s, itemSize.height(): %s" % (self.l.getItemSize().width(), self.l.getItemSize().height()))
		self.res = [None]
		self.usedFont = 1
		self.usedSelectFont = 3
		self.usedDateFont = 4
		self.startHPos = self.MVCStartHPos
		self.width = self.l.getItemSize().width() - 10

		#print("MVC: MovieListGUI: buildMovieListEntry: let's start with startHPos: %s" % self.startHPos)
		if filetype == FILE_TYPE_IS_FILE and ext in extVideo:
			#print("MVC: MovieListGUI: buildMovieListEntry: adjusted startHPos: %s" % self.startHPos)
			recording = getRecording(path, True)
			cutting = isCutting(path)
			color, color_sel = getColor(path, FILE_TYPE_IS_FILE, recording, cutting)
			progress = getProgress(recording, length, cuts)

			if config.MVC.movie_icons.value:
				pixmap = getFileIcon(path, filetype, progress, recording, cutting)
				createIcon(pixmap)

			if config.MVC.movie_picons.value:
				createPicon(service_reference, ext)

			createTitle(name, filetype, color, color_sel)

			createProgress(progress, color, color_sel, recording)

			date_text = getDateText(path, filetype, date_string)
			createDateText(date_text, color, color_sel, recording, cutting)
		elif filetype == FILE_TYPE_IS_DIR:
			#print("MVC: MovieListGUI: buildMovieListEntry: ext: " + ext)
			recording = None
			cutting = None
			progress = 0

			color, color_sel = getColor(path, FILE_TYPE_IS_DIR, recording, cutting)

			if config.MVC.movie_icons.value:
				pixmap = getFileIcon(path, filetype, progress, recording, cutting)
				createIcon(pixmap)

			createTitle(_(name), filetype, color, color_sel)

			date_text = getDateText(path, filetype, date_string)
			createDateText(date_text, color, color_sel, False, False)
		else:
			#print("MVC: MovieListGUI: buildMovieListEntry: unknown ext: " + ext)
			pass
		#print("MVC: MovieListGUI: buildMovieListEntry: return")
		return self.res
