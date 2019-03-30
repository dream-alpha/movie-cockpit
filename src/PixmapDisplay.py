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

from enigma import ePicLoad, gPixmapPtr
from Components.AVSwitch import AVSwitch


class PixmapDisplay(object):
	def __init__(self):
		self.picload = ePicLoad()
		self.picload_conn = None

	def displayPixmap(self, location, path):
		#print("MVC: PixmapDisplay: displayPixmap: path: %s, location: %s" % (path, location))
		self.location = location
		if path is not None and self.picload_conn is None:
			scale = AVSwitch().getFramebufferScale()
			size = self[location].instance.size()
			#print("MVC: PixmapDisplay: displayPixmap: size: %s, %s, scale: %s, %s" % (size.width(), size.height(), scale[0], scale[1]))
			self[location].instance.setPixmap(gPixmapPtr())
			self.picload_conn = self.picload.PictureData.connect(self.displayPixmapCallback)
			self.picload.setPara((size.width(), size.height(), scale[0], scale[1], False, 1, "#ff000000"))
			self.picload.startDecode(path, True)

	def displayPixmapCallback(self, picinfo=None):
		#print("MVC: PixmapDisplay: displayPixmapCallback")
		if self.picload and picinfo:
			self[self.location].instance.setPixmap(self.picload.getData())
			self.picload_conn = None
