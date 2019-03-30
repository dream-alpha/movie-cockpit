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

import os
from Bookmarks import Bookmarks

class MountPoints(Bookmarks, object):

	def __disk_usage(self, path):
		st = os.statvfs(path)
		free = (st.f_bavail * st.f_frsize)
		total = (st.f_blocks * st.f_frsize)
		used = (st.f_blocks - st.f_bfree) * st.f_frsize
		percent_used = round((float(used) / total) * 100, 1) if total > 0 else 0
		return percent_used, free

	def getMountPoint(self, path, first=True):
		if first:
			path = os.path.realpath(path)
		if os.path.ismount(path) or not path:
			return path
		return self.getMountPoint(os.path.dirname(path), False)

	def getMountPointsSpaceUsedPercent(self):
		space_used_percent = ""
		bookmarks = self.getBookmarks()
		mountpoints = []
		for bookmark in bookmarks:
			mountpoint = self.getMountPoint(bookmark)
			if mountpoint not in mountpoints:
				mountpoints.append(mountpoint)
				percent_used = self.__getMountPointSpaceUsedPercent(mountpoint)
				if space_used_percent != "":
					space_used_percent += ", "
				space_used_percent += mountpoint + (": %.1f" % percent_used) + "%"
		#print("MVC: MountPoints: getMountPointsSpaceUsedPercent: space_used_percent: %s" % space_used_percent)
		return space_used_percent

	def __getMountPointSpaceUsedPercent(self, path):
		percent_used = 0
		if os.path.exists(path):
			percent_used, _free = self.__disk_usage(path)
		return percent_used

	def getMountPointSpaceFree(self, path):
		free = 0
		if os.path.exists(path):
			_percent_used, free = self.__disk_usage(path)
		return free
