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


from Components.Converter.Converter import Converter
from Components.Element import cached


class MVCEventName(Converter):
	NAME = 0
	SHORT_DESCRIPTION = 1
	EXTENDED_DESCRIPTION = 2
	FULL_DESCRIPTION = 3
	ID = 4
	SHORT_AND_EXTENDED_DESCRIPTION = 5

	def __init__(self, atype):
		Converter.__init__(self, atype)
		if atype == "Description":
			self.type = self.SHORT_DESCRIPTION
		elif atype == "ExtendedDescription":
			self.type = self.EXTENDED_DESCRIPTION
		elif atype == "FullDescription":
			self.type = self.FULL_DESCRIPTION
		elif atype == "ShortAndExtendedDescription":
			self.type = self.SHORT_AND_EXTENDED_DESCRIPTION
		elif atype == "ID":
			self.type = self.ID
		else:
			self.type = self.NAME

	@cached
	def getText(self):
		text = ""
		event = self.source.event
		if event:
			if self.type == self.NAME:
				text = event.getEventName()
			elif self.type == self.SHORT_DESCRIPTION:
				text = event.getShortDescription()
			elif self.type == self.EXTENDED_DESCRIPTION:
				text = event.getExtendedDescription()
			elif self.type == self.FULL_DESCRIPTION:
				text = event.getShortDescription()
				if text:
					text += "\n\n"
				text += event.getExtendedDescription()
			elif self.type == self.SHORT_AND_EXTENDED_DESCRIPTION:
				text = event.getShortDescription() + "|" + event.getExtendedDescription()
			elif self.type == self.ID:
				text = str(event.getEventId())
		return text

	text = property(getText)
