#!/usr/bin/python
# encoding: utf-8
#
# Copyright (C) 2011 betonme
# Copyright (C) 2018-2021 dream-alpha
#
# In case of reuse of this source code please do not remove this copyright.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# For more information on the GNU General Public License see:
# <http://www.gnu.org/licenses/>.


from Components.Renderer.PositionGauge import PositionGauge


class MVCPositionGauge(PositionGauge):
	def __init__(self):
		PositionGauge.__init__(self)
		self.__cutlist = []

	def getCutlist(self):
		return self.__cutlist

	def setCutlist(self, cutlist):
		if self.__cutlist != cutlist:
			# E2 Bug: Use a list copy instead of a reference
			self.__cutlist = cutlist[:]
			if self.instance is not None:
				self.instance.setInOutList(cutlist)

	cutlist = property(getCutlist, setCutlist)
