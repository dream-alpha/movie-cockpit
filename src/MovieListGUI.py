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
from MovieCache import MovieCache, TYPE_ISLINK, str2date
from MediaTypes import extTS, extVideo
from Bookmarks import Bookmarks
from SkinUtils import getSkinPath
from Components.config import config
from Components.GUIComponent import GUIComponent
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaBlend
from Tools.LoadPixmap import LoadPixmap
from skin import parseColor, parseFont, parseSize
from enigma import eListboxPythonMultiContent, eListbox, RT_HALIGN_LEFT, RT_HALIGN_CENTER, loadPNG
from RecordingUtils import isCutting, getRecording
from MovieCache import TYPE_ISDIR, TYPE_ISFILE


class MovieListGUI(GUIComponent, Bookmarks, object):
	GUI_WIDGET = eListbox

	def __init__(self):
		#print("MVC: MovieListGUI: __init__")
		self.skinAttributes = None
		GUIComponent.__init__(self)
		self.initSkin()

	def initSkin(self):
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

		self.DefaultColor = parseColor("#bababa").argb()
		self.TitleColor = parseColor("#bababa").argb()
		self.DateColor = parseColor("#bababa").argb()
		self.BackColor = None
		self.BackColorSel = None
		self.FrontColorSel = parseColor(config.MVC.color_highlight.value).argb()
		self.RecordingColor = parseColor(config.MVC.color_recording.value).argb()

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
		self.pic_trashcan_full = LoadPixmap(cached=True, path=skin_path + "trashcan_full.svg")
		self.pic_link = LoadPixmap(cached=True, path=skin_path + "link.svg")
		self.pic_col_dir = LoadPixmap(cached=True, path=skin_path + "coldir.svg")
		self.pic_progress_bar = LoadPixmap(cached=True, path=skin_path + "progcl.svg")
		self.pic_rec_progress_bar = LoadPixmap(cached=True, path=skin_path + "rec_progcl.svg")
		self.pic_recording = LoadPixmap(cached=True, path=skin_path + "recording.svg")

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
			"TitleColor", "DateColor", "DefaultColor", "BackColor", "BackColorSel", "FrontColorSel", "RecordingColor"
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

		def createProgressBar(progress, color, recording):
			#print("MVC: MovieListGUI: buildMovieListEntry: createProgressBar: progress: %s, startHPos: %s" % (progress, self.startHPos))
			x = self.startHPos
			y = yPos(self.l.getItemSize().height(), self.MVCBarSize.height())

			bar_pic = self.pic_progress_bar
			if recording:
				bar_pic = self.pic_rec_progress_bar
				color = self.DefaultColor

			self.res.append((eListboxPythonMultiContent.TYPE_PROGRESS_PIXMAP, x, y, self.MVCBarSize.width(), self.MVCBarSize.height(), progress, bar_pic, 1, color, self.FrontColorSel, self.BackColor, None))
			self.startHPos = x + self.MVCBarSize.width() + self.MVCSpacer

		def createProgressValue(progress, color):
			#print("MVC: MovieListGUI: buildMovieListEntry: createProgressValue: progress: %s, startHPos: %s" % (progress, self.startHPos))
			x = self.startHPos
			y = yPos(self.l.getItemSize().height(), self.MVCFont.pointSize)

			self.res.append(MultiContentEntryText(pos=(x, y), size=(self.MVCBarSize.width(), self.l.getItemSize().height()), font=self.usedFont, flags=RT_HALIGN_CENTER, text="%d%%" % (progress), color=color, color_sel=self.FrontColorSel))
			self.startHPos = x + self.MVCBarSize.width() + self.MVCSpacer

		def createTitle(title, ext, color):
			#print("MVC: MovieListGUI: buildMovieListEntry: createTitle: %s, startHPos: %s" % (title, self.startHPos))
			x = self.startHPos
			y = yPos(self.l.getItemSize().height(), self.MVCFont.pointSize)
			w = self.MVCMovieWidth
			if w is None:
				w = self.width - x - self.MVCDateWidth - self.MVCSpacer

			if ext in extVideo and (config.MVC.movie_progress.value == "PB" or config.MVC.movie_progress.value == "P"):
				w = w - self.MVCBarSize.width() - self.MVCSpacer

			self.res.append(MultiContentEntryText((x, y), (w, self.l.getItemSize().height()), font=self.usedFont, flags=RT_HALIGN_LEFT, text=title, color=color, color_sel=self.FrontColorSel))
			self.startHPos = x + w + self.MVCSpacer

		def createIcon(pixmap):
			#print("MVC: MovieListGUI: buildMovieListEntry: createIcon: startHPos: %s" % self.startHPos)
			x = self.startHPos
			y = yPos(self.l.getItemSize().height(), self.MVCIconSize.height())

			self.res.append(MultiContentEntryPixmapAlphaBlend(pos=(x, y), size=(self.MVCIconSize.width(), self.MVCIconSize.height()), png=pixmap, **{}))
			self.startHPos = x + self.MVCIconSize.width() + self.MVCSpacer

		def createSelNum(path):
			#print("MVC: MovieListGUI: buildMovieListEntry: createSelNum: startHPos: %s" % self.startHPos)
			selnumtxt = None
			if path in self.selection_list:
				selnumtxt = "*"
				x = self.startHPos
				y = yPos(self.l.getItemSize().height(), self.MVCSelectFont.pointSize)

				self.res.append(MultiContentEntryText(pos=(x, y), size=(self.MVCIconSize.width(), self.l.getItemSize().height()), font=self.usedSelectFont, flags=RT_HALIGN_CENTER, text=selnumtxt))
				self.startHPos = x + self.MVCIconSize.width() + self.MVCSpacer
			return selnumtxt

		def createPicon(service_reference, ext):
			#print("MVC: MovieListGUI: buildMovieListEntry: createPicon: startHPos: %s" % self.startHPos)
			x = self.startHPos
			y = yPos(self.l.getItemSize().height(), self.MVCPiconSize.height())

			if ext in extTS:
				piconpath = getPiconPath(service_reference)
				self.res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, x, y, self.MVCPiconSize.width(), self.MVCPiconSize.height(), loadPNG(piconpath), None, None))
			self.startHPos = x + self.MVCPiconSize.width() + self.MVCSpacer

		def createDateText(datetext, color, recording):
			#print("MVC: MovieListGUI: buildMovieListEntry: createDateText: %s, startHPos: %s" % (datetext, self.startHPos))
			x = self.startHPos
			y = yPos(self.l.getItemSize().height(), self.MVCDateFont.pointSize)

			halign = config.MVC.datetext_alignment.value

			if recording:
				x = x + (self.MVCDateWidth - self.MVCRecIconSize.width()) / 2
				y = yPos(self.l.getItemSize().height(), self.MVCRecIconSize.height())

				self.res.append(MultiContentEntryPixmapAlphaBlend(pos=(x, y), size=(self.MVCRecIconSize.width(), self.MVCRecIconSize.height()), png=self.pic_recording, **{}))
			else:
				self.res.append(MultiContentEntryText(pos=(x, y), size=(self.MVCDateWidth, self.l.getItemSize().height()), font=self.usedDateFont, text=datetext, color=color, color_sel=self.FrontColorSel, flags=halign))
			self.startHPos = x + self.MVCDateWidth + self.MVCSpacer

		def getDateText(path, info_value, filetype):
			datetext = ""
			count, size = MovieCache.getInstance().getCountSize(path)
			counttext = "%d" % count

			size /= (1024 * 1024 * 1024)  # GB
			sizetext = "%.0f GB" % size
			if size >= 1024:
				sizetext = "%.1f TB" % size / 1024

			#print("MVC: MovieListGUI: getValues: count: %s, size: %s" % (count, size))
			if info_value == "C":
				datetext = "(%s)" % counttext

			if info_value == "S":
				datetext = "(%s)" % sizetext

			if info_value == "CS":
					datetext = "(%s/%s)" % (counttext, sizetext)

			if info_value == "D":
				if os.path.basename(path) == "trashcan":
					datetext = _("trashcan")
				elif config.MVC.directories_ontop.value:
					datetext = _("Collection")
				elif filetype == TYPE_ISLINK:
					datetext = _("Link")
				else:
					datetext = _("Directory")

			#print("MVC: MovieListGUI: getValues: datetext: %s" % (datetext))
			return count, datetext

		def getDirValues(path, filetype):
			datetext = ""
			pixmap = self.pic_directory

			if filetype == TYPE_ISDIR and os.path.basename(path) == "..":
				pixmap = self.pic_back
				if config.MVC.directories_info.value == "D":
					datetext = _("up")

			elif filetype == TYPE_ISDIR and os.path.basename(path) == "trashcan":
				if config.MVC.movie_trashcan_enable.value:
					count, datetext = getDateText(path, config.MVC.movie_trashcan_info.value, filetype)
					if count > 0:
						pixmap = self.pic_trashcan_full
					else:
						pixmap = self.pic_trashcan

			elif filetype == TYPE_ISDIR:
				pixmap = self.pic_directory

				if config.MVC.directories_ontop.value:
					pixmap = self.pic_col_dir

				if config.MVC.link_icons.value and filetype == TYPE_ISLINK:
					pixmap = self.pic_link

				_count, datetext = getDateText(path, config.MVC.directories_info.value, filetype)

			return datetext, pixmap

		def getFileValues(path, date_string, length, cuts):

			def getMountPoint(path):
				mountpoint = ""
				for l in file("/etc/fstab"):
					if l.startswith("/"):
						l = l.split()
						if path.startswith(l[1]):
							mountpoint = l[1]
							break
				return mountpoint

			def getFileIcon(ext):
				pixmap = self.pic_movie_default

				movieWatching = False
				movieFinished = False
				if config.MVC.movie_progress.value:
					movieWatching = config.MVC.movie_progress.value and progress >= int(config.MVC.movie_watching_percent.value) and progress < int(config.MVC.movie_finished_percent.value)
					movieFinished = config.MVC.movie_progress.value and progress >= int(config.MVC.movie_finished_percent.value)

				# video
				if ext in extVideo:
					if movieWatching:
						pixmap = self.pic_movie_watching
					elif movieFinished:
						pixmap = self.pic_movie_finished
					else:
						pixmap = self.pic_movie_default
				return pixmap

			def getProgress(recording, length, cuts):
				# All calculations are done in seconds
				#print("MVC: MovieListGUI: getProgress: path: %s" % path

				# first get last and length
				if recording:
					begin, end, _service_ref = recording
					last = time() - begin
					length = end - begin
				else:
					# Get last position from cut file
					#print("MVC: MovieListGUI: getProgress: cut_list: " + str(cut_list))
					last = ptsToSeconds(getCutListLast(unpackCutList(cuts)))
					#print("MVC: MovieListGUI: getProgress: last: " + str(last))

				# second calculate progress
				progress = 0
				if length > 0 and last > 0:
					if last > length:
						last = length
					progress = int(round(float(last) / float(length), 2) * 100)

				#print("MVC: MovieListGUI: getProgress: progress = %s, length = %s, recording = %s" % (progress, length, recording))
				return progress

			pixmap = self.pic_movie_default

			recording = getRecording(path, True)
			progress = getProgress(recording, length, cuts)

			# Check for recording only if date is within the last day
			if recording:
				datetext = "--- REC ---"
				pixmap = self.pic_movie_rec
				color = self.RecordingColor

			elif isCutting(path):
				datetext = "--- CUT ---"
				pixmap = self.pic_movie_cut
				color = self.RecordingColor

			elif config.MVC.movie_mountpoints.value:
				datetext = getMountPoint(path)
				color = self.DefaultColor

			else:
				# Media file
				color = self.DefaultColor
				datetext = str2date(date_string).strftime(config.MVC.movie_date_format.value)
				if config.MVC.movie_icons.value:
					pixmap = getFileIcon(ext)

			return datetext, pixmap, color, progress, recording

		#print("MVC: MovieListGUI: buildMovieListEnty: itemSize.width(): %s, itemSize.height(): %s" % (self.l.getItemSize().width(), self.l.getItemSize().height()))
		progress = 0
		pixmap = None
		color = None
		datetext = None
		self.res = [None]
		self.usedFont = 1
		self.usedSelectFont = 3
		self.usedDateFont = 4
		self.startHPos = self.MVCStartHPos
		self.width = self.l.getItemSize().width() - 10

		#print("MVC: MovieListGUI: buildMovieListEntry: let's start with startHPos: %s" % self.startHPos)
		if filetype == TYPE_ISFILE and ext in extVideo:
			#print("MVC: MovieListGUI: buildMovieListEntry: adjusted startHPos: %s" % self.startHPos)
			datetext, pixmap, color, progress, recording = getFileValues(path, date_string, length, cuts)

			selnumtxt = createSelNum(path)
			if not selnumtxt and config.MVC.movie_icons.value:
				createIcon(pixmap)

			if config.MVC.movie_picons.value:
				createPicon(service_reference, ext)

			createTitle(name, ext, color)

			if config.MVC.movie_progress.value == "PB":
				createProgressBar(progress, color, recording)

			if config.MVC.movie_progress.value == "P":
				createProgressValue(progress, color)

			if config.MVC.movie_date_format.value:
				createDateText(datetext, color, recording)
		elif filetype in [TYPE_ISDIR, TYPE_ISLINK]:
			#print("MVC: MovieListGUI: buildMovieListEntry: ext: " + ext)
			datetext, pixmap = getDirValues(path, filetype)

			if config.MVC.movie_icons.value:
				createIcon(pixmap)

			createTitle(_(name), ext, self.FrontColorSel)
			createDateText(datetext, self.FrontColorSel, False)
		else:
			#print("MVC: MovieListGUI: buildMovieListEntry: unknown ext: " + ext)
			pass
		#print("MVC: MovieListGUI: buildMovieListEntry: return")
		return self.res
