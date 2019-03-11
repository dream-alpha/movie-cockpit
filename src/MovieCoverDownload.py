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
from Components.config import config
from MovieTMDB import MovieTMDB, SELECTION_ID, SELECTION_TYPE, SELECTION_URL, INFO_COVER_URL
from MovieCover import MovieCover
from FileUtils import deleteFile

substitutelist = [(".", " "), ("_", " "), ("1080p", ""), ("720p", ""), ("x264", ""), ("h264", ""), ("1080i", ""), ("AC3", "")]


class MovieCoverDownload(MovieTMDB, MovieCover, object):
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
		#print("MVC: MovieCoverDownload: downloadCover: cover_path: %s, cover_url: %s" % (cover_path, cover_url))
		cover_found = 0
		cover_tried = 1
		if cover_url is not None:
			if os.path.isfile(cover_path):
				if config.MVC.cover_replace_existing.value:
					deleteFile(cover_path)
				else:
					cover_tried = 0
			if not os.path.isfile(cover_path):
				try:
					#print("MVC: MovieCoverDownload: downloadCover: cover_path: %s, cover_url: %s" % (cover_path, cover_url))
					os.system("wget -O \"" + cover_path + "\" " + cover_url)
					cover_found = 1
				except Exception as e:
					print("MVC-E: MovieCoverDownload: downloadCover: exception: %s" % e)
		return cover_tried, cover_found

	def getCover4SplitTitles(self, path, _filename, titles):
		#print("MVC: MovieCoverDownload: getCover4SplitTitles: path: %s, titles: %s" % (path, titles))
		cover_found = 0
		cover_tried = 1
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
						cover_tried, cover_found = self.downloadCover(cover_url, cover_path)
						info_path = self.getInfoPath(path)
						self.saveInfo(info_path, self.info)
						break
			else:
				#print("MVC: MovieCoverDownload: getCover4SplitTitles: nothing found")
				pass

		#print("MVC: MovieCoverDownload: getCover4SplitTitles: cover_tried: %s, cover_found: %s" % (cover_tried, cover_found))
		return cover_tried, cover_found

	def getCover(self, path, title):
		#print("MVC: MovieCoverDownload: getCover: path: %s, filename: %s" % path)
		filename, _ext = os.path.splitext(path)
		cover_found = 0
		cover_tried = 1
		title = self.__removeCutNumbers(title)
		title = title.replace("_", ":")
		cover_tried, cover_found = self.getCover4SplitTitles(path, filename, [title])
		if cover_found == 0:
			for sep in [":", " - "]:
				titles = title.split(sep)
				if len(titles) > 1:
					cover_tried, cover_found = self.getCover4SplitTitles(path, filename, titles)
					if cover_found > 0:
						break
		#print("MVC: MovieCoverDownload: getCover: cover_tried: %s, cover_found: %s" % (cover_tried, cover_found))
		return cover_tried, cover_found
