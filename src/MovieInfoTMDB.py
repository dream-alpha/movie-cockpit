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
from FileUtils import deleteFile
from SkinUtils import getSkinPath
from MovieCoverDownload import MovieCoverDownload
from MovieTMDB import SELECTION_ID, SELECTION_TYPE, INFO_COVER_URL, INFO_BACKDROP_URL
from MovieCoverDownloadProgress import MovieCoverDownloadProgress

PAGE_DETAILS = 0   # details
PAGE_SELECTION = 1 # selection list
TEMP_COVER_PATH = "/tmp/preview_cover.jpg"
TEMP_BACKDROP_PATH = "/tmp/preview_cover.backdrop.jpg"
TEMP_INFO_PATH = "/tmp/preview_info.txt"


class MovieInfoTMDB(Screen, MovieCoverDownload):

	def __init__(self, session, path, name):
		#print("MVC: MovieInfoTMDB: __init__: path: %s, name: %s" % (path, name))
		Screen.__init__(self, session)
		MovieCoverDownload.__init__(self)
		self.skinName = "MVCMovieInfoTMDB"
		self["cover"] = Pixmap()
		self.name = name
		self.search_name = self.getMovieNameWithoutPhrases(name)
		self.movielist = None
		self.path = path
		self.selection = None
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

		self.onLayoutFinish.append(self.layoutFinished)
		self["actions"] = HelpableActionMap(
			self,
			"MovieInfoTMDB",
			{
				"MVCEXIT":	(self.exit,		_("Exit")),
				"MVCUP":	(self.pageUp,		_("Cursor page up")),
				"MVCDOWN":	(self.pageDown,		_("Cursor page down")),
				"MVCOK":	(self.ok,		_("Select cover")),
				"MVCGREEN":	(self.save,		_("Save cover")),
				"MVCYELLOW":	(self.getThisCover,	_("Get cover")),
				"MVCBLUE":	(self.getAllCovers,	_("Get covers")),
				"MVCRED":	(self.deleteThisCover,	_("Delete cover"))
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
		self.cover_path, self.backdrop_path = self.getCoverPath(self.path)
		self.info_path = self.getInfoPath(self.path)
		self.info = self.loadInfo(self.info_path)
		self.page = PAGE_DETAILS
		self.switchPage()

	def selectionChanged(self):
		#print("MVC: MovieInfoTMDB: selectionChanged")
		if self.page == PAGE_SELECTION:
			self.getInfoAndCoverForCurrentSelection(TEMP_INFO_PATH, TEMP_COVER_PATH)
			self.switchPage()

	def getInfoAndCoverForCurrentSelection(self, info_path, cover_path):
		deleteFile(TEMP_COVER_PATH)
		deleteFile(TEMP_INFO_PATH)
		self.info = None
		self.selection = self["previewlist"].l.getCurrentSelection()
		#print("MVC: MovieInfoTMDB: getInfoAndCoverForCurrentSelection: selection: " + str(self.selection))
		if self.selection:
			self.info = self.getTMDBInfo(self.selection[SELECTION_ID], self.selection[SELECTION_TYPE], config.plugins.moviecockpit.cover_language.value)
			self.saveInfo(info_path, self.info)
			self.downloadCover(self.info[INFO_COVER_URL], cover_path, self.info[INFO_BACKDROP_URL])

	def getThisCover(self):
		#print("MVC: MovieInfoTMDB: getThisCover: search_name: %s" % self.search_name)
		self.page = PAGE_DETAILS
		self.cover_path = TEMP_COVER_PATH
		self.backdrop_path = TEMP_BACKDROP_PATH
		self.info_path = TEMP_INFO_PATH
		deleteFile(TEMP_COVER_PATH)
		deleteFile(TEMP_BACKDROP_PATH)
		deleteFile(TEMP_INFO_PATH)
		self.info = None

		self.search_names = [self.search_name]
		for split_char in [":", "-"]:
			search_names = self.search_name.split(split_char)
			if len(search_names) > 1:
				self.search_names += search_names
		#print("MVC: MovieInfoTMDB: getThisCover: self.search_names: %s" % self.search_names)
		for search_name in self.search_names:
			self.movielist = self.getMovieList(search_name)
			if self.movielist:
				#print("MVC: MovieInfoTMDB: getThisCover: len(self.movielist): %s", len(self.movielist))
				self["previewlist"].setList(self.movielist)
				if len(self.movielist) > 1:
					self.page = PAGE_SELECTION
				self.getInfoAndCoverForCurrentSelection(self.info_path, self.cover_path)
				break
			else:
				#print("MVC: MovieInfoTMDB: getThisCover: no movielist available for: %s" % search_name)
				pass
		self.switchPage()

	def switchPage(self):
		#print("MVC: MovieInfoTMDB: switchPage: " + str(self.page))
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
			#print("MVC: MovieInfoTMDB: switchPage: info available")
			self["movie_name"].setText(self.name)
			#print("MVC: MovieInfoTMDB: switchPage: self.info: %s" % str(self.info))
			content, runtime, genres, countries, release, vote, _cover_url, _backdrop_url = self.info
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
			#print("MVC: MovieInfoTMDB: switchPage: no info available")
			self["movie_name"].setText(_("Search results for") + ": " + self.search_name)
			self["contenttxt"].setText(_("No cover found"))
			self["contenttxt"].show()
		self.coverTimer.start(int(config.plugins.moviecockpit.movie_description_delay.value), True)

	def save(self):
		#print("MVC: MovieInfoTMDB: save: self.path: %s" % self.path)
		if self.page == PAGE_DETAILS and self.path:
			self.info_path = self.getInfoPath(self.path)
			self.cover_path, self.backdrop_path = self.getCoverPath(self.path)
			if fileExists(self.cover_path):
				self.session.openWithCallback(
					self.saveCallback,
					MessageBox,
					_("Cover/TMDB Info already exists") + "\n" + _("Do you want to replace the existing cover/TMDB info?"),
					MessageBox.TYPE_YESNO
				)
			else:
				self.saveTempData(self.cover_path, self.backdrop_path, self.info_path)

	def saveCallback(self, answer):
		if answer:
			self.saveTempData(self.cover_path, self.backdrop_path, self.info_path)

	def saveTempData(self, cover_path, backdrop_path, info_path):
		#print("MVC: MovieInfoTMDB: saveTempData: cover_path: %s, backdrop_path: %s, info_path: %s" % (cover_path, backdrop_path, info_path))
		if fileExists(TEMP_COVER_PATH) and fileExists(TEMP_INFO_PATH):
			try:
				shutil.copy2(TEMP_COVER_PATH, cover_path)
				if fileExists(TEMP_BACKDROP_PATH):
					shutil.copy2(TEMP_BACKDROP_PATH, backdrop_path)
				shutil.copy2(TEMP_INFO_PATH, info_path)
				self.showMsg(failed=False)
			except Exception as e:
				print('MVC-E: MovieInfoTMDB: saveTempData: exception failure: %s' % e)
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
		#print("MVC: MovieInfoTMDB: deleteThisCover")
		deleteFile(TEMP_COVER_PATH)
		deleteFile(self.cover_path)
		self.cover_path = TEMP_COVER_PATH
		deleteFile(TEMP_BACKDROP_PATH)
		deleteFile(self.backdrop_path)
		self.back_drop_path = TEMP_BACKDROP_PATH
		deleteFile(TEMP_INFO_PATH)
		deleteFile(self.info_path)
		self.info_path = TEMP_INFO_PATH
		self.info = None
		self.session.openWithCallback(
			self.deleteThisCoverCallback,
			MessageBox,
			_("Cover/TMDB Info deleted successfully"),
			MessageBox.TYPE_INFO,
			5
		)

	def deleteThisCoverCallback(self, _answer):
		self.switchPage()

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
		#print("MVC: MovieInfoTMDB: ShowCover: self.cover_path: %s" % self.cover_path)
		self.showCover(self["cover"], self.cover_path, getSkinPath("images/tmdb.svg"))

	def exit(self):
		#print("MVC: MovieInfoTMDB: exit")
		if self.movielist:
			#print("MVC: MovieInfoTMDB: exit: movielist")
			if self.page == PAGE_DETAILS and len(self.movielist) > 1:
				#print("MVC: MovieInfoTMDB: exit: PAGE_DETAILS")
				self["movie_name"].setText(_("Search results for") + ": " + self.name)
				self.page = PAGE_SELECTION
				self.switchPage()
				return

		#print("MVC: MovieInfoTMDB: exit: before close")
		self["previewlist"].onSelectionChanged = []
		self.close()

	def getAllCovers(self):
		#print("MVC: MovieInfoTMDB: getAllCovers")
		self.session.openWithCallback(self.getAllCoversCallback, MovieCoverDownloadProgress)

	def getAllCoversCallback(self):
		self.movielist = None
		self.layoutFinished()
