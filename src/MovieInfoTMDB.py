#!/usr/bin/python
# encoding: utf-8
#
# Copyright (C) 2018 dream-alpha
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
import shutil
from __init__ import _
from Components.ActionMap import HelpableActionMap
from Components.MenuList import MenuList
from Components.Button import Button
from Components.Label import Label
from Components.ProgressBar import ProgressBar
from Components.ScrollLabel import ScrollLabel
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.config import config
from Components.Pixmap import Pixmap
from enigma import eTimer
from Tools.Directories import fileExists
from FileUtils import readFile
from SkinUtils import getSkinPath
from Bookmarks import Bookmarks
from MovieCoverDownload import MovieCoverDownload
from MovieCover import MovieCover
from MovieTMDB import SELECTION_ID, SELECTION_TYPE, INFO_COVER_URL

PAGE_DETAILS = 0   # details
PAGE_SELECTION = 1 # selection list
TEMP_COVER_PATH = "/tmp/preview_cover.jpg"
TEMP_INFO_PATH = "/tmp/preview_info.txt"


class MovieInfoTMDB(Screen, MovieCover, MovieCoverDownload, Bookmarks, object):
	skin = readFile(getSkinPath("MovieInfoTMDB.xml"))

	def __init__(self, session, path, name):
		print("MVC: MovieInfoTMDB: __init__: path: %s, name: %s" % (path, name))
		Screen.__init__(self, session)
		MovieCover.__init__(self)
		MovieCoverDownload.__init__(self, session)
		self.name = name
		self.search_name = self.getMovieNameWithoutPhrases(name)
		self.movielist = None
		self.path = path
		self.page = PAGE_DETAILS
		self.selection = None
		self.cover_path = MovieCover.getCoverPath(path, self.getBookmarks())
		self.coverTimer = eTimer()
		self.coverTimer_conn = self.coverTimer.timeout.connect(self.showCoverDelayed)

		self["previewlist"] = MenuList([])
		self["movie_name"] = Label("")
		self["contenttxt"] = ScrollLabel()
		self["runtime"] = Label(_("Runtime") + ":")
		self["runtimetxt"] = Label("")
		self["genre"] = Label(_("Genre") + ":")
		self["genretxt"] = Label("")
		self["country"] = Label(_("Production Countries") + ":")
		self["countrytxt"] = Label("")
		self["release"] = Label(_("Release Date") + ":")
		self["releasetxt"] = Label("")
		self["rating"] = Label(_("Vote") + ":")
		self["ratingtxt"] = Label("")
		self["stars"] = ProgressBar()
		self["starsbg"] = Pixmap()
		self["stars"].hide()
		self["starsbg"].hide()
		self.ratingstars = -1

		self.info_path = self.getInfoPath(self.path)
		self.info = self.loadInfo(self.info_path)

		self.onLayoutFinish.append(self.layoutFinished)
		self["actions"] = HelpableActionMap(
			self,
			"MovieInfoTMDB",
			{
				"MVCEXIT": (self.exit, _("exit")),
				"MVCUp": (self.pageUp, _("cursor page up")),
				"MVCDown": (self.pageDown, _("cursor page down")),
				"MVCOK": (self.ok, _("select cover")),
				"MVCGreen": (self.save, _("save temporary cover")),
				"MVCYellow": (self.getThisCover, ("get cover")),
				"MVCBlue": (self.getAllCovers, ("get all covers")),
				"MVCRed": (self.deleteThisCover, ("delete cover"))
			},
			-1
		)

		self["key_red"] = Button(_("Delete cover"))
		self["key_green"] = Button(_("Save cover"))
		self["key_blue"] = Button(_("Get covers"))
		self["key_yellow"] = Button(_("Get cover"))

		self["previewlist"].onSelectionChanged.append(self.selectionChanged)

	def layoutFinished(self):
		self.setTitle(_("Movie Information TMDb"))
		self.switchPage()

	def selectionChanged(self):
		print("MVC: MovieInfoTMDB: selectionChanged")
		if self.page == PAGE_SELECTION:
			self.deleteCover(TEMP_COVER_PATH)
			self.selection = self["previewlist"].l.getCurrentSelection()
			print("MVC: MovieInfoTMDB: selectionChanged: selection: " + str(self.selection))
			if self.selection:
				self.info = self.getTMDBInfo(self.selection[SELECTION_ID], self.selection[SELECTION_TYPE], config.MVC.cover_language.value)
				self.downloadCover(self.info[INFO_COVER_URL], TEMP_COVER_PATH)
				self.switchPage()

	def getThisCover(self):
		print("MVC: MovieInfoTMDB: getThisCover: search_name: %s" % self.search_name)
		self.cover_path = TEMP_COVER_PATH
		self.info_path = TEMP_INFO_PATH
		self.deleteCover(self.cover_path)
		self.deleteInfo(self.info_path)
		self.page = PAGE_DETAILS
		self.info = None
		self.movielist = self.getMovieList(self.search_name)
		if self.movielist:
			print("MVC: MovieInfoTMDB: getThisCover: len(self.movielist): %s", len(self.movielist))
			self["previewlist"].setList(self.movielist)
			if len(self.movielist) > 1:
				self.page = PAGE_SELECTION
			self.selection = self["previewlist"].l.getCurrentSelection()
			print("MVC: MovieInfoTMDB: getThisCover: selection: " + str(self.selection))
			if self.selection:
				print("MVC: MovieInfoTMDB: getThisCover: selection")
				self.info = self.getTMDBInfo(self.selection[SELECTION_ID], self.selection[SELECTION_TYPE], config.MVC.cover_language.value)
				self.saveInfo(self.info_path, self.info)
				self.downloadCover(self.info[INFO_COVER_URL], self.cover_path)
		else:
			print("MVC: MovieInfoTMDB: getThisCover: no movielist available")
		self.switchPage()

	def switchPage(self):
		print("MVC: MovieInfoTMDB: switchPage: " + str(self.page))
		if self.page == PAGE_SELECTION:
			self["movie_name"].setText(_("Search results for") + ": " + self.search_name)
			self["previewlist"].show()
			self["contenttxt"].hide()
			self["key_yellow"].hide()
			self["key_green"].hide()
			self["key_blue"].hide()
			self["key_red"].hide()
		else:
			self["previewlist"].hide()
			self["contenttxt"].show()
			self["key_yellow"].show()
			self["key_green"].show()
			self["key_blue"].show()
			self["key_red"].show()

		if self.info:
			print("MVC: MovieInfoTMDB: switchPage: info available")
			self["movie_name"].setText(self.name)
			content, runtime, genres, countries, release, vote, _cover_url = self.info
			self["contenttxt"].setText(content)
			if runtime != "":
				self["runtimetxt"].setText(runtime + " " + _("Minutes"))
			else:
				self["runtimetxt"].setText(runtime)
			self["genretxt"].setText(genres)
			self["countrytxt"].setText(countries)
			self["releasetxt"].setText(release)
			if vote:
				self["ratingtxt"].setText(vote.replace('\n', '') + " / 10")
				self.ratingstars = int(10 * round(float(vote.replace(',', '.')), 1))
				if self.ratingstars > 0:
					self["starsbg"].show()
					self["stars"].show()
					self["stars"].setValue(self.ratingstars)
				else:
					self["starsbg"].show()
					self["stars"].hide()
			else:
				self["ratingtxt"].setText("0 / 10")
				self["starsbg"].show()
				self["stars"].hide()
		else:
			print("MVC: MovieInfoTMDB: switchPage: no info available")
			self["movie_name"].setText(_("Search results for") + ": " + self.search_name)
			self["contenttxt"].setText(_("Nothing was found"))
			self["contenttxt"].show()
		self.coverTimer.start(int(config.MVC.movie_description_delay.value), True)

	def save(self):
		print("MVC: MovieInfoTMDB: save: self.path: %s" % self.path)
		if self.page == PAGE_DETAILS and self.path:
			self.cover_path = MovieCover.getCoverPath(self.path, self.getBookmarks())
			self.info_path = self.getInfoPath(self.path)
			if fileExists(self.cover_path):
				self.session.openWithCallback(
					self.saveCallback,
					MessageBox,
					_("Cover/TMDB Info exists")
					+ "\n"
					+ _("Do you want to replace the existing cover/TMDB info?"),
					MessageBox.TYPE_YESNO
				)
			else:
				self.saveTempData(self.cover_path, self.info_path)

	def saveCallback(self, answer):
		if answer:
			self.saveTempData(self.cover_path, self.info_path)

	def saveTempData(self, cover_path, info_path):
		print("MVC: MovieInfoTMDB: saveTempData: cover_path: %s, info_path: %s" % (cover_path, info_path))
		if fileExists(TEMP_COVER_PATH) and fileExists(TEMP_INFO_PATH):
			try:
				shutil.copy2(TEMP_COVER_PATH, cover_path)
				shutil.copy2(TEMP_INFO_PATH, info_path)
				self.showMsg(failed=False)
			except Exception as e:
				print('MVC: MovieInfoTMDB: saveTempData: exception failure:\n', str(e))
				self.showMsg(failed=True)
		else:
			self.showMsg(failed=True)

	def showMsg(self, askno=False, failed=False):
		if not askno:
			if not failed:
				msg = _("Cover/TMDB info saved successfully")
			else:
				msg = _("Saving Cover/TMDB info failed")
			self.session.open(
				MessageBox,
				msg,
				MessageBox.TYPE_INFO,
				5
			)

	def deleteThisCover(self):
		print("MVC: MovieInfoTMDB: deleteThisCover")
		cover_path = MovieCover.getCoverPath(self.path, self.getBookmarks())
		self.deleteCover(cover_path)
		info_path = self.getInfoPath(self.path)
		self.deleteInfo(info_path)
		self.session.open(
			MessageBox,
			_("Cover/TMDB Info deleted successfully"),
			MessageBox.TYPE_INFO,
			5
		)

	def deleteCover(self, cover_path):
		try:
			os.remove(cover_path)
		except Exception as e:
			print("MVC: MovieInfoTMDB: deleteCover: exception:\n" + str(e))

	def ok(self):
		if self.page == PAGE_SELECTION:
			self.page = PAGE_DETAILS
			self.switchPage()

	def pageUp(self):
		if self.page == PAGE_DETAILS:
			self["contenttxt"].pageUp()
		if self.page == PAGE_SELECTION:
			self["previewlist"].up()

	def pageDown(self):
		if self.page == PAGE_DETAILS:
			self["contenttxt"].pageDown()
		if self.page == PAGE_SELECTION:
			self["previewlist"].down()

	def showCoverDelayed(self):
		print("MVC: MovieInfoTMDB: ShowCover")
		self.showCover(self.cover_path, getSkinPath("img/tmdb.svg"))

	def exit(self):
		print("MVC: MovieInfoTMDB: exit")
		if self.movielist:
			if self.page == PAGE_DETAILS and len(self.movielist) > 1:
				self["movie_name"].setText(_("Search results for") + ": " + self.name)
				self.page = PAGE_SELECTION
				self.switchPage()
				return

		self["previewlist"].onSelectionChanged = []
		self.close()

	def getAllCovers(self):
		print("MVC: MovieInfoTMDB: getAllCovers")
		self.getCovers()
