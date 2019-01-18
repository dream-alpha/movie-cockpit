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
import re
from __init__ import _
from Screens.MessageBox import MessageBox
from Tools.BoundFunction import boundFunction
from Components.config import config
from Bookmarks import Bookmarks
from MovieCache import MovieCache, FILE_IDX_FILENAME, FILE_IDX_EXT, FILE_IDX_NAME, FILE_IDX_PATH
from MediaTypes import plyAll
from MovieTMDB import MovieTMDB, SELECTION_ID, SELECTION_TYPE, SELECTION_URL, INFO_COVER_URL
from MovieCover import MovieCover
from FileUtils import deleteFile

substitutelist = [(".", " "), ("_", " "), ("1080p", ""), ("720p", ""), ("x264", ""), ("h264", ""), ("1080i", ""), ("AC3", "")]


class MovieCoverDownload(MovieTMDB, MovieCover, Bookmarks, object):
	def __init__(self, session=None):
		MovieCover.__init__(self)
		self.cover_size = config.MVC.cover_size.value
		self.session = session
		self.tried = 0
		self.cover_found = 0

	def __removeCutNumbers(self, path):
		if path[-4:-3] == "_" and path[-3:].isdigit():
			path = path[:-4]
		return path

	def getMovieNameWithoutPhrases(self, moviename=""):
		# Remove phrases which are encapsulated in [*] or (*) from the movietitle
		moviename = re.sub(r'\[.*\]', "", moviename)
		moviename = re.sub(r'\(.*\)', "", moviename)
		moviename = re.sub(r' S\d\dE\d\d .*', "", moviename)
		for (phrase, sub) in substitutelist:
			moviename = moviename.replace(phrase, sub)
		return moviename

	def downloadCover(self, cover_url, cover_path):
		#print("MVC: MovieCoverDownload: downloadCover: cover_path: %s" % cover_path)
		cover_found = 0
		if cover_url is not None:
			if config.MVC.cover_replace_existing.value and os.path.isfile(cover_path):
				deleteFile(cover_path)
			if not os.path.isfile(cover_path):
				try:
					#print("MVC: MovieCoverDownload: downloadCover: url: %s, cover_path: %s" % (cover_url, cover_path))
					os.system("wget -O \"" + cover_path + "\" " + cover_url)
					cover_found = 1
				except Exception as e:
					print('MVC-E: MovieCoverDownload: downloadCover: exception failure:\n', str(e))
		else:
			#print("MVC: MovieCoverDownload: downloadCover: cover_url is None")
			pass
		return cover_found

	def getCover4SplitTitles(self, path, _filename, titles):
		#print("MVC: MovieCoverDownload: getCover4SplitTitles: path: %s, titles: %s" % (path, titles))
		cover_found = 0
		for title in titles:
			title = self.getMovieNameWithoutPhrases(title)
			#print("MVC: MovieCoverDownload: getCover4SplitTitles: %s" % title)
			self.movielist = self.getMovieList(title)
			if self.movielist:
				selection = self.movielist[0]
				if selection[SELECTION_URL]:
					self.info = self.getTMDBInfo(selection[SELECTION_ID], selection[SELECTION_TYPE], config.MVC.cover_language.value)
					if self.info:
						cover_path = self.getCoverPath(path)
						cover_url = self.info[INFO_COVER_URL]
						cover_found = self.downloadCover(cover_url, cover_path)
						info_path = self.getInfoPath(path)
						self.saveInfo(info_path, self.info)
						break
			else:
				#print("MVC: MovieCoverDownload: getCover4SplitTitles: nothing found")
				pass

		#print("MVC: MovieCoverDownload: getCover4SplitTitles: cover_found: %s" % cover_found)
		return cover_found

	def getCoverTitle(self, title, path, filename, ext):
		#print("MVC: MovieCoverDownload: getCoverTitle: path: %s, filename: %s" % (path, filename))
		cover_found = 0
		if ext in plyAll:
			title = self.__removeCutNumbers(title)
			title = title.replace("_", ":")
			cover_found = self.getCover4SplitTitles(path, filename, [title])
			if cover_found == 0:
				for sep in [":", " - "]:
					titles = title.split(sep)
					if len(titles) > 1:
						cover_found = self.getCover4SplitTitles(path, filename, titles)
						if cover_found > 0:
							break
		#print("MVC: MovieCoverDownload: getCoverTitle: cover_found: %s" % cover_found)
		return cover_found

	def nextMovieInLine(self):
		if self.filelist:
			afile = self.filelist.pop(0)
			filename = afile[FILE_IDX_FILENAME]
			path = afile[FILE_IDX_PATH]
			ext = afile[FILE_IDX_EXT]
			name = afile[FILE_IDX_NAME]
			if self.session:
				msg = _("Downloading cover") + " (" + str(self.tried) + " " + "of" + " " + str(self.number_of_files) + ") " + "for" + ":\n" + name
				self.session.openWithCallback(
					boundFunction(self.getCover, name, path, filename, ext),
					MessageBox,
					msg,
					timeout=1,
					type=MessageBox.TYPE_INFO
				)
			else:
				self.getCover(name, path, filename, ext)
		else:
			if self.session:
				#print("MVC: MovieCoverDownload: getCover: cover result: %s of %s covers found: %s percent" % (self.cover_found, self.tried, str(float(float(self.cover_found) / float(self.tried)) * 100)))
				self.movielist = None
				msg = "Download finished: %s of %s covers found." % (self.cover_found, self.tried)
				self.session.open(
					MessageBox,
					msg,
					timeout=10,
					type=MessageBox.TYPE_INFO
				)

	def getCover(self, name, path, filename, ext, _answer=True):
		#print("MVC: MovieCoverDownload: getCover: path: %s, filename: %s" % (path, filename))
		self.tried += 1
		self.cover_found += self.getCoverTitle(name, path, filename, ext)
		self.nextMovieInLine()

	def getCoverOfRecording(self, path):
		self.filelist = []
		self.filelist.append(MovieCache.getInstance().getFile(path))
		self.nextMovieInLine()

	def getCovers(self):
		self.tried = 0
		self.cover_found = 0
		bookmarks = self.getBookmarks()
		self.filelist = MovieCache.getInstance().getFileList(bookmarks)
		self.number_of_files = len(self.filelist)
		self.nextMovieInLine()
