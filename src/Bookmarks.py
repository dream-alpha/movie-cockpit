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
from Components.config import config
from MountPoints import getMountPoint, getDiskSpaceInfo


def getHomeDir():
	return getBookmarks()[0]


def isBookmark(path):
	return path in getBookmarks()


def getBookmarks():
	bookmarks = []
	if config.movielist and config.movielist.videodirs:
		bookmarks = [os.path.normpath(bookmark) for bookmark in config.movielist.videodirs.value]
	return bookmarks


def getBookmark(path):
	for bookmark in getBookmarks():
		if path.startswith(bookmark):
			return bookmark
	return None


def getBookmarksSpaceInfo():
	space_used_percent = ""
	bookmarks = getBookmarks()
	mountpoints = []
	for bookmark in bookmarks:
		mountpoint = getMountPoint(bookmark)
		if mountpoint and mountpoint not in mountpoints:
			mountpoints.append(mountpoint)
			percent_used, _used, _free = getDiskSpaceInfo(mountpoint)
			if space_used_percent != "":
				space_used_percent += ", "
			space_used_percent += mountpoint + (": %.1f" % percent_used) + "%"
	#print("MVC: Bookmarks: getBookmarksSpaceInfo: space_used_percent: %s" % space_used_percent)
	return space_used_percent
