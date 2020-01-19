#!/usr/bin/python
# coding=utf-8
#
# Copyright (C) 2018-2020 by dream-alpha
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


from __init__ import _
from datetime import datetime
from enigma import eServiceCenter, iServiceInformation
from FileCache import FileCache, FILE_TYPE_FILE
from CutListUtils import unpackCutList
from Components.config import config


instance = None


class ServiceCenter():

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


class ServiceInfo():

	def __init__(self, service):
		self.info = None
		if service:
			self.info = Info(service.getPath())

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
			return self.info and self.info.getEventStartTime()
		return None

	def getInfoObject(self, _service=None, info_type=None):
		if info_type == iServiceInformation.sFileSize:
			return self.info and self.info.getSize()
		return None

	def getName(self, _service=None):
		return self.info and self.info.getName()

	def getEvent(self, _service=None):
		return self.info

	def getEventStartTime(self, _service=None):
		return self.info and self.info.getEventStartTime()

	def getRecordingStartTime(self, _service=None):
		return self.info and self.info.getRecordingStartTime()


class Info():

	def __init__(self, path):
		filetype, name, event_start_time, description, extended_description, service_reference, cuts, tags = "", "", "", "", "", "", "", ""
		size = length = recording_start_time = 0
		self.path = path
		if self.path:
			filedata = FileCache.getInstance().getFile(self.path)
			if filedata is not None:
				_dirname, filetype, _path, _filename, _ext, name, event_start_time, recording_start_time, _recording_stop_time, length, description, extended_description, service_reference, size, cuts, tags = filedata
		self.__filetype = filetype
		self.__event_start_time = event_start_time
		self.__recording_start_time = recording_start_time
		self.__name = name if name != "trashcan" else _(name)
		self.__shortdescription = description
		self.__extendeddescription = extended_description
		self.__length = length
		self.__service_reference = service_reference
		self.__size = size
		self.__tags = tags
		self.__cut_list = unpackCutList(cuts)

	def getName(self):
		#EventName NAME
		return self.__name

	def getServiceReference(self):
		return self.__service_reference

	def getTags(self):
		return self.__tags

	def getEventId(self):
		return 0

	def getEventName(self):
		return self.__name

	def getShortDescription(self):
		#EventName SHORT_DESCRIPTION
		return self.__shortdescription

	def getExtendedDescription(self):
		#EventName EXTENDED_DESCRIPTION
		return self.__extendeddescription

	def getBeginTimeString(self):
		return datetime.fromtimestamp(self.__event_start_time).strftime(config.plugins.moviecockpit.movie_date_format.value)

	def getEventStartTime(self):
		return self.__event_start_time

	def getRecordingStartTime(self):
		return self.__recording_start_time

	def getDuration(self):
		return self.__length

	def getLength(self):
		return self.__length

	def getSize(self):
		if self.__filetype == FILE_TYPE_FILE:
			size = self.__size
		else:
			_count, size = FileCache.getInstance().getCountSize(self.path)
		return size
