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


class Bookmarks(object):

	def __saveBookmarks(self, bookmarks):
		config.movielist.videodirs.value = bookmarks
		config.movielist.videodirs.save()

	def isBookmark(self, path):
		return path in self.getBookmarks()

	def getBookmarks(self):
		bookmarks = []
		if config.movielist and config.movielist.videodirs:
			bookmarks = [os.path.normpath(bookmark) for bookmark in config.movielist.videodirs.value]
		return bookmarks

	def getBookmark(self, path):
		for bookmark in self.getBookmarks():
			if path.startswith(bookmark):
				return bookmark
		return None
#
# 	def addBookmark(self, path):
# 		if path and config.movielist and config.movielist.videodirs:
# 			bookmark = os.path.normpath(path)
# 			bookmarks = self.getBookmarks()
# 			if bookmark not in bookmarks:
# 				bookmarks.append(bookmark)
# 				self.__saveBookmarks(bookmarks)
#
# 	def removeBookmark(self, path):
# 		if path and config.movielist and config.movielist.videodirs:
# 			bookmark = os.path.normpath(path)
# 			bookmarks = self.getBookmarks()
# 			if bookmark in bookmarks:
# 				bookmarks.remove(bookmark)
# 				self.__saveBookmarks(bookmarks)
