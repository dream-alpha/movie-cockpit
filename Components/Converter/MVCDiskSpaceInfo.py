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


from Poll import Poll
from Components.Element import cached
from Components.Converter.Converter import Converter
from Plugins.Extensions.MovieCockpit.Bookmarks import getBookmarksSpaceInfo


class MVCDiskSpaceInfo(Poll, Converter):
	SPACEINFO = 0

	def __init__(self, atype):
		#print("MVC: MVCDiskSpaceInfo: __init__")
		Converter.__init__(self, atype)
		Poll.__init__(self)

		self.type = self.SPACEINFO
		self.poll_interval = 2000
		self.poll_enabled = True

	def doSuspend(self, suspended):
		#print("MVC: MVCDiskSpaceInfo: doSuspend: %s" % suspended)
		if suspended:
			self.poll_enabled = False
		else:
			self.downstream_elements.changed((self.CHANGED_POLL,))
			self.poll_enabled = True

	@cached
	def getText(self):
		#print("MVC: MVCDiskSpaceInfo: getText")
		return getBookmarksSpaceInfo()

	text = property(getText)
