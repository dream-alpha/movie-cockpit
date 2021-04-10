#!/usr/bin/python
# coding=utf-8
#
# EitSupport
# Copyright (C) 2011 by betonme
# Copyright (C) 2018-2021 by dream-alpha
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


from Debug import logger
import os
import struct
import re
from Components.config import config
from Tools.ISO639 import LanguageCodes
from FileUtils import readFile
import datetime
import time
from UnicodeUtils import convertToUtf8


class ParserEitFile():

	def __init__(self, path):
		self.eit = {
			"start": 0,
			"length": 0,
			"name": "",
			"short_description": "",
			"description": "",
			"when": "",
			"content": "",
		}
		self.name_event_descriptor = []
		self.name_event_descriptor_multi = []
		self.name_event_codepage = None
		self.short_event_descriptor = []
		self.short_event_descriptor_multi = []
		self.short_event_codepage = None
		self.extended_event_descriptor = []
		self.extended_event_descriptor_multi = []
		self.extended_event_codepage = None
		self.component_descriptor = []
		self.content_descriptor = []
		self.linkage_descriptor = []
		self.parental_rating_descriptor = []
		self.pdc_descriptor = []
		self.prev1_ISO_639_language_code = "x"
		self.prev2_ISO_639_language_code = "x"

		path, _ext = os.path.splitext(path)
		eit_path = path + ".eit"
		if not os.path.exists(eit_path):
			# Strip existing cut number
			if path[-4:-3] == "_" and path[-3:].isdigit():
				path = path[:-4]
				eit_path = path + ".eit"
				if not os.path.exists(eit_path):
					eit_path = ""
		if eit_path:
			data = readFile(eit_path)
			if data and len(data) >= 12:
				self.__parse(data)

	### Get functions

	def getEit(self):
		if self.eit["short_description"].startswith(self.eit["name"]):
			self.eit["short_description"] = self.eit["short_description"][len(self.eit["name"]) + 1:]
		self.eit["short_description"] = self.eit["short_description"].replace("\n", ", ")
		return self.eit

	def __parse(self, data):
		EIT_LINKAGE_DESCRIPTOR = 0x4a
		EIT_SHORT_EVENT_DESCRIPTOR = 0x4d
		EIT_EXTENDED_EVENT_DESCRIPTOR = 0x4e
		EIT_COMPONENT_DESCRIPTOR = 0x50
		EIT_CONTENT_DESCRIPTOR = 0x54
		EIT_PARENTAL_RATING_DESCRIPTOR = 0x55
		EIT_PDC_DESCRIPTOR = 0x69

		def make_int(s):
			return int(s) if s else 0

		def parseMJD(MJD):
			# Parse 16 bit unsigned int containing Modified Julian Date as per DVB-SI spec
			# returning year, month, day
			YY = int((MJD - 15078.2) / 365.25)
			MM = int((MJD - 14956.1 - int(YY * 365.25)) / 30.6001)
			D = MJD - 14956 - int(YY * 365.25) - int(MM * 30.6001)
			K = 0
			if MM in [14, 15]:
				K = 1
			return (1900 + YY + K), (MM - 1 - K * 12), D

		def unBCD(byte):
			return (byte >> 4) * 10 + (byte & 0xf)

		def language_iso639_2to3(alpha2):
			if alpha2 in LanguageCodes:
				language = LanguageCodes[alpha2]
				for alpha, name in LanguageCodes.items():
					if name == language:
						if len(alpha) == 3:
							return alpha
			return alpha2

		def determineCodepage(byte):
			codepage = None
			if byte == "1":
				codepage = 'iso-8859-5'
			elif byte == "2":
				codepage = 'iso-8859-6'
			elif byte == "3":
				codepage = 'iso-8859-7'
			elif byte == "4":
				codepage = 'iso-8859-8'
			elif byte == "5":
				codepage = 'iso-8859-9'
			elif byte == "6":
				codepage = 'iso-8859-10'
			elif byte == "7":
				codepage = 'iso-8859-11'
			elif byte == "9":
				codepage = 'iso-8859-13'
			elif byte == "10":
				codepage = 'iso-8859-14'
			elif byte == "11":
				codepage = 'iso-8859-15'
			elif byte == "21":
				codepage = 'utf-8'
			return codepage

		def parseHeader(data, pos):
			e = struct.unpack(">HHBBBBBBH", data[pos:pos + 12])
			#event_id = e[0]
			y, mo, d = parseMJD(e[1])				# Y, M, D
			h, mi, s = unBCD(e[2]), unBCD(e[3]), unBCD(e[4])	# HH, MM, SS
			try:
				dt = datetime.datetime(y, mo, d, h, mi, s)
				logger.debug("dt: %s", str(dt))
				start_seconds = int(time.mktime(dt.timetuple()))
				self.eit["start"] = start_seconds - time.timezone + time.localtime(start_seconds).tm_isdst * 3600  # daylight savings time
			except Exception as e:
				logger.error("exception: %s", e)
				self.eit["start"] = 0

			length_hhmmss = unBCD(e[5]), unBCD(e[6]), unBCD(e[7])	# HH, MM, SS
			if len(length_hhmmss) > 2:
				event_length = make_int((length_hhmmss[0] * 60 + length_hhmmss[1]) * 60 + length_hhmmss[2])
			elif len(length_hhmmss) > 1:
				event_length = make_int(length_hhmmss[0] * 60 + length_hhmmss[1])
			else:
				event_length = make_int(length_hhmmss)
			self.eit["length"] = event_length

			#free_CA_mode = e[8] & 0x1000
			#descriptors_loop_length = e[8] & 0x0fff

			running_status = (e[8] & 0xe000) >> 13
			if running_status in [1, 2]:
				self.eit['when'] = "NEXT"
			elif running_status in [3, 4]:
				self.eit['when'] = "NOW"

		def parseShortEventDescriptor(data, pos):
			ISO_639_language_code = str(data[pos + 2:pos + 5]).upper()
			event_name_length = ord(data[pos + 5])
			name_event_description = ""
			for i in range(pos + 6, pos + 6 + event_name_length):
				if str(ord(data[i])) == "10" or int(str(ord(data[i]))) > 31:
					name_event_description += data[i]
			if not self.name_event_codepage:
				try:
					byte1 = str(ord(data[pos + 6]))
				except Exception:
					byte1 = ''
				self.name_event_codepage = determineCodepage(byte1)

			short_event_description = ""
			if not self.short_event_codepage:
				try:
					byte1 = str(ord(data[pos + 7 + event_name_length]))
				except Exception:
					byte1 = ''
				self.short_event_codepage = determineCodepage(byte1)
			for i in range(pos + 7 + event_name_length, pos + length):
				if str(ord(data[i])) == "10" or int(str(ord(data[i]))) > 31:
					short_event_description += data[i]
			if ISO_639_language_code == lang:
				self.short_event_descriptor.append(short_event_description)
				self.name_event_descriptor.append(name_event_description)
			if (ISO_639_language_code == self.prev1_ISO_639_language_code) or (self.prev1_ISO_639_language_code == "x"):
				self.short_event_descriptor_multi.append(short_event_description)
				self.name_event_descriptor_multi.append(name_event_description)
			else:
				self.short_event_descriptor_multi.append("\n\n" + short_event_description)
				self.name_event_descriptor_multi.append(" " + name_event_description)
			self.prev1_ISO_639_language_code = ISO_639_language_code

		def parseExtendedEventDescriptor(data, pos):
			ISO_639_language_code = ""
			for i in range(pos + 3, pos + 6):
				ISO_639_language_code += data[i]
			ISO_639_language_code = ISO_639_language_code.upper()
			extended_event_description = ""
			if not self.extended_event_codepage:
				try:
					byte1 = str(ord(data[pos + 8]))
				except Exception:
					byte1 = ''
				self.extended_event_codepage = determineCodepage(byte1)
			for i in range(pos + 8, pos + length):
				if str(ord(data[i])) == "10" or int(str(ord(data[i]))) > 31:
					extended_event_description += data[i]
			if ISO_639_language_code == lang:
				self.extended_event_descriptor.append(extended_event_description)
			if (ISO_639_language_code == self.prev2_ISO_639_language_code) or (self.prev2_ISO_639_language_code == "x"):
				self.extended_event_descriptor_multi.append(extended_event_description)
			else:
				self.extended_event_descriptor_multi.append("\n\n" + extended_event_description)
			self.prev2_ISO_639_language_code = ISO_639_language_code

		def parseContentDescriptor(_data, _pos):
			logger.debug("...")
			self.content_descriptor.append("n/a")

		epglang = config.plugins.moviecockpit.epglang.value
		lang = (language_iso639_2to3(epglang.lower()[:2])).upper()

		# Parse the data
		pos = 0
		parseHeader(data, pos)
		pos += 12

		while pos < len(data) - 2:
			rec = ord(data[pos])
			length = ord(data[pos + 1]) + 2

			if rec == EIT_SHORT_EVENT_DESCRIPTOR:
				parseShortEventDescriptor(data, pos)

			elif rec == EIT_EXTENDED_EVENT_DESCRIPTOR:
				parseExtendedEventDescriptor(data, pos)

			elif rec == EIT_COMPONENT_DESCRIPTOR:
				self.component_descriptor.append(data[pos + 8:pos + length])

			elif rec == EIT_CONTENT_DESCRIPTOR:
				parseContentDescriptor(data, pos)
				self.eit['content'] = self.content_descriptor

			elif rec == EIT_LINKAGE_DESCRIPTOR:
				self.linkage_descriptor.append(data[pos + 8:pos + length])

			elif rec == EIT_PARENTAL_RATING_DESCRIPTOR:
				self.parental_rating_descriptor.append(data[pos + 2:pos + length])

			elif rec == EIT_PDC_DESCRIPTOR:
				self.pdc_descriptor.append(data[pos + 5:pos + length])

			else:
				logger.info("unsupported descriptor: %x %x", rec, length)
				logger.info("%s", (data[pos:pos + length]))

			pos += length

		if self.name_event_descriptor:
			self.name_event_descriptor = "".join(self.name_event_descriptor)
		else:
			self.name_event_descriptor = ("".join(self.name_event_descriptor_multi)).strip()
		self.eit['name'] = convertToUtf8(self.name_event_descriptor, self.name_event_codepage)

		if self.short_event_descriptor:
			self.short_event_descriptor = "".join(self.short_event_descriptor)
		else:
			self.short_event_descriptor = ("".join(self.short_event_descriptor_multi)).strip()
		self.eit['short_description'] = convertToUtf8(self.short_event_descriptor, self.short_event_codepage)

		if self.extended_event_descriptor:
			self.extended_event_descriptor = "".join(self.extended_event_descriptor)
		else:
			self.extended_event_descriptor = ("".join(self.extended_event_descriptor_multi)).strip()
		self.extended_event_descriptor = convertToUtf8(self.extended_event_descriptor, self.extended_event_codepage)
		if self.extended_event_descriptor:
			# This will fix EIT data of RTL group with missing line breaks in extended event description
			self.extended_event_descriptor = re.sub('((?:Moderat(?:ion:|or(?:in){0,1})|Vorsitz: |Jur(?:isten|y): |G(?:\xC3\xA4|a)st(?:e){0,1}: |Mit (?:Staatsanwalt|Richter(?:in){0,1}|den Schadenregulierern) |Julia Leisch).*?[a-z]+)(\'{0,1}[0-9A-Z\'])', r'\1\n\n\2', self.extended_event_descriptor)
		self.eit['description'] = self.extended_event_descriptor
