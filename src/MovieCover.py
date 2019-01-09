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
from enigma import ePicLoad, gPixmapPtr
from Components.config import config
from Components.Pixmap import Pixmap
from Components.AVSwitch import AVSwitch
from SkinUtils import getSkinPath
from Bookmarks import Bookmarks


class MovieCover(Bookmarks, object):

	def __init__(self):
		#print("MVC: MovieCover: MovieCover: __init__")
		self["cover"] = Pixmap()

	@staticmethod
	def getCoverPath(path, bookmarks):
#		#print("MVC: MovieCover getCoverPath: path: " + path)
		file_formats = "(.ts|.avi|.mkv|.divx|.f4v|.flv|.img|.iso|.m2ts|.m4v|.mov|.mp4|.mpeg|.mpg|.mts|.vob|.asf|.wmv|.stream|.webm)"
		cover_path = re.sub(file_formats + "$", '.jpg', path, flags=re.IGNORECASE)
		if config.MVC.cover_flash.value:
			for bookmark in bookmarks:
				if cover_path.startswith(bookmark):
					cover_path = config.MVC.cover_bookmark.value + cover_path[len(bookmark):]
					break
		#print("MVC: MovieCover getCoverPath: cover_path: " + cover_path)
		return cover_path

	def showCover(self, path, no_cover_path=None):
		print("MVC-I: MovieCover: showCover: path: %s" % path)
		if path:
			cover_path = MovieCover.getCoverPath(path, self.getBookmarks())
			if not os.path.exists(cover_path):
				cover_path = None
				if config.MVC.cover_fallback.value:
					if no_cover_path and os.path.exists(no_cover_path):
						cover_path = no_cover_path
					else:
						cover_path = getSkinPath("img/no_cover.svg")

			print("MVC-I: MovieCover: showCover: cover_path %s" % cover_path)
			if cover_path:
				self["cover"].show()
				self.displayCover(cover_path)
				return True
			else:
				self["cover"].hide()
		return False

	def displayCover(self, path):
		#print("MVC: MovieCover displayCover: path: %s" % path)
		if path is not None:
			#print("MVC: MovieCover displayCover: showing cover now")
			scale = AVSwitch().getFramebufferScale()
			size = self["cover"].instance.size()
			#print("MVC: MovieCover size: %s, %s, scale: %s, %s" % (size.width(), size.height(), scale[0], scale[1]))
			self["cover"].instance.setPixmap(gPixmapPtr())
			self.picload = ePicLoad()
			self.picload_conn = self.picload.PictureData.connect(self.displayCoverCallback)
			self.picload.setPara((size.width(), size.height(), scale[0], scale[1], False, 1, "#ff000000"))
			self.picload.startDecode(path, True)

	def displayCoverCallback(self, picinfo=None):
		#print("MVC: MovieCover displayCoverCallback")
		if self.picload and picinfo:
			self["cover"].instance.setPixmap(self.picload.getData())
