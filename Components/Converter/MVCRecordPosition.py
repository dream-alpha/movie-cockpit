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


from Components.Converter.ServicePosition import ServicePosition
from Components.Element import cached


class MVCRecordPosition(ServicePosition):
	def __init__(self, ptype):
		ServicePosition.__init__(self, ptype)

	@cached
	def getCutlist(self):
		# Not used
		return []

	cutlist = property(getCutlist)

	@cached
	def getPosition(self):
		player = self.source.player
		return player.getRecordingPosition()

	position = property(getPosition)

	@cached
	def getLength(self):
		player = self.source.player
		return player.getLength()

	length = property(getLength)
