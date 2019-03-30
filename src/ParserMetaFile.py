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

import os
from FileUtils import readFile

META_IDX_SERVICE = 0
META_IDX_NAME = 1
META_IDX_DESC = 2
META_IDX_RECTIME = 3
META_IDX_TAGS = 4
META_IDX_LENGTH = 5
META_IDX_FILESIZE = 6


# http://git.opendreambox.org/?p=enigma2.git;a=blob;f=doc/FILEFORMAT
class ParserMetaFile(object):

	def __init__(self, path=None):
		self.meta = {}
		meta_list = []
		if path:
			meta_path = path + ".meta"
			if not os.path.exists(meta_path):
				path, ext = os.path.splitext(path)
				# Strip existing cut number
				if path[-4:-3] == "_" and path[-3:].isdigit():
					path = path[:-4] + ext
					meta_path = path + ".meta"
					if not os.path.exists(meta_path):
						meta_path = ""
			if meta_path:
				meta_list = readFile(meta_path).splitlines()
				if meta_list:
					meta_list = [l.strip() for l in meta_list]
					self.meta["name"] = meta_list[META_IDX_NAME]
					self.meta["service_reference"] = meta_list[META_IDX_SERVICE]
					self.meta["tags"] = meta_list[META_IDX_TAGS]

	def getMeta(self):
		return self.meta

	def getServiceReference(self):
		return self.meta["service_reference"]

	def getName(self):
		return self.meta["name"]

	def getTags(self):
		return self.meta["tags"]

#	def __mk_int(self, s):
#		if s:
#			try:
#				return int(s)
#			except Exception:
#				return 0
#		else:
#			return 0

#	def __secondsToDate(self, s):
#		return s and datetime.fromtimestamp(s) or None

#	def getMTime(self):
#		return self.meta_mtime

#	def getDescription(self):
#		try:
#			self.meta[self.DESC].decode('utf-8')
#		except UnicodeDecodeError:
#			try:
#				self.meta[self.DESC] = self.meta[META_IDX_DESC].decode("cp1252").encode("utf-8")
#			except UnicodeDecodeError:
#				self.meta[self.DESC] = self.meta[META_IDX_DESC].decode("iso-8859-1").encode("utf-8")
#		return self.meta and self.meta[self.DESC]

#	def getRecordingTime(self):
#		# Time in seconds since 1970
#		return self.meta and self.__mk_int(self.meta[META_IDX_RECTIME])

#	def getLength(self):
#		return self.meta and self.__ptsToSeconds(self.__mk_int(self.meta[META_IDX_LENGTH]))

#	def getFileSize(self):
#		return self.meta and self.__mk_int(self.meta[META_IDX_FILESIZE])

#	def getDate(self):
#		return self.__secondsToDate(self.getRecordingTime())
