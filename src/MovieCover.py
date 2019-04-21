#!/usr/bin/python
# coding=utf-8
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
		cover_filename, cover_ext = os.path.splitext(cover_path)
		backdrop_path = cover_filename + ".backdrop" + cover_ext
		#print("MVC: MovieCover getCoverPath: cover_path: %s, backdrop_path: %s" % (cover_path, backdrop_path))
		return cover_path, backdrop_path

	def showCover(self, pixmap, path, no_cover_path=None):
		print("MVC-I: MovieCover: showCover: path: %s" % path)
		_filename, ext = os.path.splitext(path)
		cover_path = None
		if path and ext and ext != "..":
			cover_path, _backdrop_path = self.getCoverPath(path)
			no_cover_path = getSkinPath("images/no_cover.svg")
		return self.showImage(pixmap, cover_path, no_cover_path)

	def showBackdrop(self, pixmap, path, no_backdrop_path=None):
		print("MVC-I: MovieCover: showBackdrop: path: %s" % path)
		_filename, ext = os.path.splitext(path)
		backdrop_path = None
		if path and ext and ext != "..":
			_cover_path, backdrop_path = self.getCoverPath(path)
			no_backdrop_path = getSkinPath("images/no_backdrop.svg")
		return self.showImage(pixmap, backdrop_path, no_backdrop_path)

	def showImage(self, pixmap, path, default_path):
		print("MVC-I: MovieCover: showImage: path: %s" % path)
		if path and not os.path.exists(path):
			path = None
			if config.MVC.cover_fallback.value:
				if default_path and os.path.exists(default_path):
					path = default_path
		print("MVC-I: MovieCover: showImage: path %s" % path)
		if path:
			pixmap.instance.show()
			self.displayPixmap(pixmap, path)
			return True
		pixmap.instance.hide()
		return False
