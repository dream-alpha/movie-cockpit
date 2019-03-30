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
from Components.config import config
from SkinUtils import getSkinPath
from Bookmarks import Bookmarks
from PixmapDisplay import PixmapDisplay


class MovieCover(Bookmarks, PixmapDisplay, object):
	def __init__(self):
		PixmapDisplay.__init__(self)

	def getCoverPath(self, path):
		#print("MVC: MovieCover getCoverPath: path: " + path)
		cover_path = os.path.splitext(path)[0] + ".jpg"
		if config.MVC.cover_flash.value:
			for bookmark in self.getBookmarks():
				if cover_path.startswith(bookmark):
					cover_path = config.MVC.cover_bookmark.value + cover_path[len(bookmark):]
					break
		#print("MVC: MovieCover getCoverPath: cover_path: " + cover_path)
		return cover_path

	def showCover(self, path, no_cover_path=None):
		print("MVC-I: MovieCover: showCover: path: %s" % path)
		if path:
			cover_path = self.getCoverPath(path)
			if not os.path.exists(cover_path):
				cover_path = None
				if config.MVC.cover_fallback.value:
					if no_cover_path and os.path.exists(no_cover_path):
						cover_path = no_cover_path
					else:
						cover_path = getSkinPath("images/no_cover.svg")

			print("MVC-I: MovieCover: showCover: cover_path %s" % cover_path)
			if cover_path:
				self["cover"].show()
				self.displayPixmap("cover", cover_path)
				return True
			else:
				self["cover"].hide()
		return False
