#!/usr/bin/python
# encoding: utf-8
#
# Copyright (C) 2018-2020 dream-alpha
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


from Components.Converter.ServicePosition import ServicePosition
from Components.Element import cached
import time


class MVCServicePosition(ServicePosition):
	def __init__(self, ptype):
		ServicePosition.__init__(self, ptype)

	@cached
	def getCutlist(self):
		cutlist = []
		try:
			service = self.source.service
			if service is not None:
				cut = service and service.cutList()
				if cut:
					cutlist = cut.getCutList()
		except Exception:
			cutlist = ServicePosition.getCutlist(self)
		return cutlist

	cutlist = property(getCutlist)

	@cached
	def getLength(self):
		length = 0
		try:
			player = self.source.player
			length = player.getLength()
		except Exception:
			length = ServicePosition.getLength(self)
		return length

	length = property(getLength)

	@cached
	def getPosition(self):
		position = 0
		try:
			player = self.source.player
			position = player.getPosition()
		except Exception:
			position = ServicePosition.getPosition(self)
		return position

	position = property(getPosition)

	@cached
	def getText(self):
		text = ""
		pos = 0
		seek = self.getSeek()
		if seek is not None:
			if self.type == self.TYPE_ENDTIME:
				pos = (self.length - self.position) / 90000
				t = time.localtime(time.time() + pos)
				text = "%02d:%02d" % (t.tm_hour, t.tm_min)
				if not self.showNoSeconds:
					text += ":%02d" % t.tm_sec
			else:
				if self.type == self.TYPE_LENGTH:
					pos = self.length
				elif self.type == self.TYPE_POSITION:
					pos = self.position
				elif self.type == self.TYPE_REMAINING:
					pos = self.length - self.position

				pos = -pos if self.negate else pos
				milliseconds = (abs(pos) % 90000) / 90
				pos /= 90000
				if self.showHours:
					text += "%+d:" % (pos / 3600)  # hours
					text += "%02d" % (abs(pos) % 3600 / 60)  # minutes
				else:
					text += "%+d" % (pos / 60)  # minutes
				if not self.showNoSeconds:
					text += ":%02d" % (abs(pos) % 60)  # seconds
					if self.detailed:
						text += ":%03d" % milliseconds  # milliseconds
		return text

	text = property(getText)
