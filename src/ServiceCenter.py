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
from __init__ import _
from time import mktime
from CutListUtils import unpackCutList
from Components.config import config
from enigma import eServiceCenter, iServiceInformation
from FileCache import FileCache, TYPE_ISFILE, str2date

instance = None


class ServiceCenter(object):

	def __init__(self):
		global instance
		instance = eServiceCenter.getInstance()
		instance.info = self.info

	@staticmethod
	def getInstance():
		if instance is None:
			ServiceCenter()
		return instance

	def info(self, service):
		return ServiceInfo(service)


class ServiceInfo(object):

	def __init__(self, service):
		self.info = None
		if service:
			self.info = Info(service)

	def getLength(self, _service=None):
		return self.info and self.info.getLength()

	def getInfoString(self, _service=None, info_type=None):
		if info_type == iServiceInformation.sServiceref:
			return self.info and self.info.getServiceReference()
		if info_type == iServiceInformation.sDescription:
			return self.info and self.info.getShortDescription()
		if info_type == iServiceInformation.sTags:
			return self.info and self.info.getTags()
		return "None"

	def getInfo(self, _service=None, info_type=None):
		if info_type == iServiceInformation.sTimeCreate:
			return self.info and self.info.getMTime()
		return None

	def getInfoObject(self, _service=None, info_type=None):
		if info_type == iServiceInformation.sFileSize:
			return self.info and self.info.getSize()
		return None

	def getName(self, _service=None):
		return self.info and self.info.getName()

	def getEvent(self, _service=None):
		return self.info

	def getStartTime(self, _service=None):
		return self.info and self.info.getMTime()


class Info(object):

	def __init__(self, service):
		self.path = service and service.getPath()
		_dirname, filetype, _path, _filename, _ext, name, date, length, description, extended_description, service_reference, size, cuts, tags = FileCache.getInstance().getFile(self.path)
		self.__filetype = filetype
		self.__date = str2date(date)
		self.__name = name if name != "trashcan" else _(name)
		self.__mtime = int(mktime(self.__date.timetuple()))
		self.__shortdescription = description
		self.__extendeddescription = extended_description
		self.__length = length
		self.__service_reference = service_reference
		self.__size = size
		self.__tags = tags
		self.__cut_list = unpackCutList(cuts)
		self.__id = 0

	def getName(self):
		#EventName NAME
		return self.__name

	def getServiceReference(self):
		return self.__service_reference

	def getTags(self):
		return self.__tags

	def getEventName(self):
		return self.__name

	def getShortDescription(self):
		#EventName SHORT_DESCRIPTION
		return self.__shortdescription

	def getExtendedDescription(self):
		#EventName EXTENDED_DESCRIPTION
		return self.__extendeddescription

	def getEventId(self):
		#EventName ID
		return self.__id

	def getBeginTimeString(self):
		return self.__date.strftime(config.MVC.movie_date_format.value)

	def getMTime(self):
		return self.__mtime

	def getLength(self):
		return self.__length

	def getDuration(self):
		return self.getLength()

	def getSize(self):
		if self.__filetype == TYPE_ISFILE:
			size = self.__size
		else:
			if config.MVC.directories_info.value or (os.path.basename(self.path) == "trashcan" and config.MVC.movie_trashcan_info.value):
				_count, size = FileCache.getInstance().getCountSize(self.path)
		return size
