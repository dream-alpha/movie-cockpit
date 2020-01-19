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
import re
from Components.config import config
from MovieTMDB import MovieTMDB, SELECTION_ID, SELECTION_TYPE, SELECTION_URL, INFO_COVER_URL, INFO_BACKDROP_URL
from MovieCover import MovieCover
from FileUtils import deleteFile

substitutelist = [(".", " "), ("_", " "), ("1080p", ""), ("720p", ""), ("x264", ""), ("h264", ""), ("1080i", ""), ("AC3", "")]


class MovieCoverDownload(MovieTMDB, MovieCover):

	def __init__(self):
		MovieTMDB.__init__(self)
		MovieCover.__init__(self)

	def getMovieNameWithoutPhrases(self, moviename):
		# Remove phrases which are encapsulated in [*] or (*) from the movie name
		moviename = re.sub(r'\[.*\]', "", moviename)
		moviename = re.sub(r'\(.*\)', "", moviename)
		moviename = re.sub(r' S\d\dE\d\d .*', "", moviename)
		for (phrase, sub) in substitutelist:
			moviename = moviename.replace(phrase, sub)
		return moviename

	def downloadCover(self, cover_url, cover_path, backdrop_url=None):
		print("MVC-I: MovieCoverDownload: downloadCover: cover_path: %s, cover_url: %s" % (cover_path, cover_url))
		print("MVC-I: MovieCoverDownload: downloadCover: backdrop_url: %s" % backdrop_url)
		cover_found = 0
		if cover_url is not None:
			deleteFile(cover_path)
			#print("MVC: MovieCoverDownload: downloadCover: cover_path: %s, cover_url: %s" % (cover_path, cover_url))
			rc = os.system("wget -qO \"" + cover_path + "\" " + cover_url)
			cover_found = rc == 0
			if rc:
				print("MVC-E: MovieCoverDownload: downloadCover: cover: rc: %s" % rc)

		if backdrop_url is not None:
			backdrop_path, ext = os.path.splitext(cover_path)
			backdrop_path += ".backdrop" + ext
			deleteFile(backdrop_path)
			#print("MVC: MovieCoverDownload: downloadCover: backdrop_path: %s, backdrop_url: %s" % (backdrop_path, backdrop_url))
			rc = os.system("wget -qO \"" + backdrop_path + "\" " + backdrop_url)
			if rc:
				print("MVC-E: MovieCoverDownload: downloadCover: backdrop: rc: %s" % rc)
		return cover_found

	def getCover(self, path, title):
		print("MVC-I: MovieCoverDownload: getCover: path: %s, title: %s" % (path, title))
		cover_found = 0
		cover_tried = 0
		cover_path, _backdrop_path = self.getCoverPath(path)
		info_path = self.getInfoPath(path)
		if not os.path.isfile(cover_path) or config.plugins.moviecockpit.cover_replace_existing.value:
			cover_tried = 1
			title = self.getMovieNameWithoutPhrases(title)
			self.titles = [title]
			for sep in [":", " - "]:
				titles = title.split(sep)
				if len(titles) > 1:
					self.titles += titles

			for atitle in self.titles:
				#print("MVC: MovieCoverDownload: getCover: atitle: %s" % atitle)
				self.movielist = self.getMovieList(atitle)
				if self.movielist:
					selection = self.movielist[0]
					if selection[SELECTION_URL]:
						self.info = self.getTMDBInfo(selection[SELECTION_ID], selection[SELECTION_TYPE], config.plugins.moviecockpit.cover_language.value)
						if self.info:
							cover_url = self.info[INFO_COVER_URL]
							backdrop_url = self.info[INFO_BACKDROP_URL]
							cover_found = self.downloadCover(cover_url, cover_path, backdrop_url)
							self.saveInfo(info_path, self.info)
							break
				else:
					#print("MVC: MovieCoverDownload: getCover: nothing found")
					pass

		return cover_tried, cover_found
