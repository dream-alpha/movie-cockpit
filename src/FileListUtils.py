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

from enigma import eServiceReference
from FileCache import FILE_IDX_NAME, FILE_IDX_PATH, FILE_IDX_EXT
from MediaTypes import plyDVB, plyM2TS, plyDVD, sidDVB, sidDVD, sidM2TS

class FileListUtils(object):

	def getEntry4Index(self, filelist, index):
		return filelist[index]

	def getEntry4Path(self, filelist, path):
		list_entry = None
		for entry in filelist:
			if entry and entry[FILE_IDX_PATH] == path:
				list_entry = entry
				break
		return list_entry

	def getIndex4Path(self, filelist, path):
		index = -1
		for i, entry in enumerate(filelist):
			if entry and entry[FILE_IDX_PATH] == path:
				index = i
				break
		return index

	def getService4Path(self, filelist, path):
		service = None
		for entry in filelist:
			if entry and entry[FILE_IDX_PATH] == path:
				service = self.getService(path, entry[FILE_IDX_NAME], entry[FILE_IDX_EXT])
				break
		return service

	def getService(self, path, name="", ext=None):
		if ext in plyDVB:
			service = eServiceReference(sidDVB, 0, path)
		elif ext in plyDVD:
			service = eServiceReference(sidDVD, 0, path)
		elif ext in plyM2TS:
			service = eServiceReference(sidM2TS, 0, path)
		else:
			ENIGMA_SERVICE_ID = 0
			DEFAULT_VIDEO_PID = 0x44
			DEFAULT_AUDIO_PID = 0x45
			service = eServiceReference(ENIGMA_SERVICE_ID, 0, path)
			service.setData(0, DEFAULT_VIDEO_PID)
			service.setData(1, DEFAULT_AUDIO_PID)
		service.setName(name)
		return service
