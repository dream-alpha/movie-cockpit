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


from Converter import Converter
from Components.Element import cached
from Components.config import config
from time import localtime, strftime, gmtime


class MVCClockToText(Converter):
	DEFAULT = 0
	WITH_SECONDS = 1
	IN_MINUTES = 2
	DATE = 3
	FORMAT = 4
	AS_LENGTH = 5
	TIMESTAMP = 6

	def __init__(self, text_type):
		Converter.__init__(self, text_type)
		if text_type == "WithSeconds":
			self.text_type = self.WITH_SECONDS
		elif text_type == "InMinutes":
			self.text_type = self.IN_MINUTES
		elif text_type == "Date":
			self.text_type = self.DATE
		elif text_type == "AsLength":
			self.text_type = self.AS_LENGTH
		elif text_type == "Timestamp":
			self.text_type = self.TIMESTAMP
		elif str(text_type).find("Format") != -1:
			self.text_type = self.FORMAT
			self.fmt_string = text_type[7:]
		else:
			self.text_type = self.DEFAULT

	@cached
	def getText(self):
		text = ""
		time = self.source.time
		if not(not time or time > 169735005176 or time < 11):
			if self.text_type == self.IN_MINUTES:
				mins = time / 60
				if time % 60 >= 30:
					mins += 1
				text = "%d min" % mins
			elif self.text_type == self.AS_LENGTH:
				text = "%d:%02d" % (time / 60, time % 60)
			elif self.text_type == self.TIMESTAMP:
				text = str(time)
			else:
				if time > (31 * 24 * 60 * 60):
					# No Recording should be longer than 1 month
					t = localtime(time)
				else:
					t = gmtime(time)

				if self.text_type == self.WITH_SECONDS:
					text = "%2d:%02d:%02d" % (t.tm_hour, t.tm_min, t.tm_sec)
				elif self.text_type == self.DEFAULT:
					text = "%02d:%02d" % (t.tm_hour, t.tm_min)
				elif self.text_type == self.DATE:
					if config.osd.language.value == "de_DE":
						text = strftime("%A, %d. %B %Y", t)
					else:
						text = strftime("%A %B %d, %Y", t)
				elif self.text_type == self.FORMAT:
					spos = self.fmt_string.find("%")
					if spos > -1:
						s1 = self.fmt_string[:spos]
						s2 = strftime(self.fmt_string[spos:], t)
						text = str(s1 + s2)
					else:
						text = strftime(self.fmt_string, t)
		return text

	text = property(getText)
