#!/usr/bin/python
# encoding: utf-8
#
# Copyright (C) 2018 by dream-alpha
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
from MovieCover import MovieCover
from Bookmarks import Bookmarks
from MountPoints import MountPoints
from TMDB import TMDB

class FileOps(TMDB, MountPoints, Bookmarks, object):

	def execFileDelete(self, c, path, file_type):
		print("MVC: FileOps: execFileDelete: path: %s, file_type: %s" % (path, file_type))
		if file_type == "file":
			path, _ext = os.path.splitext(path)
			c.append('rm -f "' + path + '."*')     # name.*
			cover_path = MovieCover.getCoverPath(path, self.getBookmarks())
			info_path = self.getInfoPath(path)
			if config.MVC.cover_flash.value and path.find(config.MVC.movie_trashcan_path.value) == 0:
				cover_path = config.MVC.cover_bookmark.value + "/" + os.path.basename(path) + ".jpg"
				info_path = config.MVC.cover_bookmark.value + "/" + os.path.basename(path) + ".txt"
			print("MVC: FileOps: execFileDelete: cover_path: %s, info_path: %s" % (cover_path, info_path))
			c.append('rm -f "' + cover_path + '"') # name.jpg
			c.append('rm -f "' + info_path + '"') # name.txt
		elif file_type == "dir":
			c.append('rm -rf "' + path + '"')
		elif file_type == "link":
			c.append('rm -f "' + path + '"')
		print("MVC: FileOps: execFileDelete: c: %s" % c)
		return c

	def execFileMove(self, c, path, target_path, file_type):
		print("MVC: FileOps: execFileMove: path: %s, target_path: %s, file_type: %s" % (path, target_path, file_type))
		c = self.__changeFileOwner(c, path, target_path)
		path, _ext = os.path.splitext(path)
		if file_type == "file":
			if target_path == config.MVC.movie_trashcan_path.value:
				c.append('touch "' + path + '."*')
			c.append('mv "' + path + '."* "' + target_path + '/"')
		elif file_type == "dir":
			if target_path == config.MVC.movie_trashcan_path.value:
				c.append('touch "' + path)
			c.append('mv "' + path + '" "' + target_path + '"')
		elif file_type == "link":
			if target_path == config.MVC.movie_trashcan_path.value:
				c.append('touch "' + path)
			c.append('mv "' + path + '" "' + target_path + '"')
		print("MVC: FileOps: execFileMove: c: %s" % c)
		return c

	def execFileCopy(self, c, path, target_path):
		print("MVC: FileOps: execFileCopy: path: %s, target_path: %s" % (path, target_path))
		c = self.__changeFileOwner(c, path, target_path)
		path, _ext = os.path.splitext(path)
		c.append('cp "' + path + '."* "' + target_path + '/"')
		print("MVC: FileOps: execFileCopy: c: %s" % c)
		return c

	def __changeFileOwner(self, c, path, target_path):
		if self.isMountPoint(target_path) != self.isMountPoint(config.MVC.movie_homepath.value):  # CIFS to HDD is ok!
			# need to change file ownership to match target filesystem file creation
			tfile = "\"" + target_path + "/owner_test" + "\""
			path = path.replace("'", "\'")
			sfile = "\"" + path + ".\"*"
			c.append("touch %s;ls -l %s | while read flags i owner group crap;do chown $owner:$group %s;done;rm %s" % (tfile, tfile, sfile, tfile))
		return c
