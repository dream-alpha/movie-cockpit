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

import os
from Components.config import config

class MountPoints(object):

	def __disk_usage(self, path):
		st = os.statvfs(path)
		free = (st.f_bavail * st.f_frsize)
		total = (st.f_blocks * st.f_frsize)
		used = (st.f_blocks - st.f_bfree) * st.f_frsize
		percent_used = round((float(used) / total) * 100, 1) if total > 0 else 0
		return percent_used, free

	def isMountPoint(self, path, first=True):
		if first:
			path = os.path.realpath(path)
		if os.path.ismount(path) or not path:
			return path
		return self.isMountPoint(os.path.dirname(path), False)

	def getMountPointsSpaceUsedPercent(self):
		space_used_percent = ""
		for videodir in config.movielist.videodirs.value:
			mountpoint = self.isMountPoint(videodir)
			percent_used = self.getMountPointSpaceUsedPercent(mountpoint)
			if space_used_percent != "":
				space_used_percent += ", "
			space_used_percent += mountpoint + (": %.1f" % percent_used) + "%"
		config.MVC.disk_space_info.value = space_used_percent
		print("MVC: MountPoints: getMountPointsSpaceUsedPercent: space_used_percent: %s" % space_used_percent)
		return space_used_percent

	def getMountPointSpaceUsedPercent(self, path):
		percent_used = 0
		if os.path.exists(path):
			percent_used, _free = self.__disk_usage(path)
		return percent_used

	def getMountPointSpaceFree(self, path):
		free = 0
		if os.path.exists(path):
			_percent_used, free = self.__disk_usage(path)
		return free
