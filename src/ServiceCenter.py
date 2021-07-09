#!/usr/bin/python
# coding=utf-8
#
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


from __init__ import _
from datetime import datetime
from enigma import eServiceCenter, iServiceInformation
from Plugins.SystemPlugins.CacheCockpit.FileCache import FileCache, FILE_TYPE_FILE
from Plugins.SystemPlugins.CacheCockpit.FileCacheSQL import FILE_IDX_TYPE, FILE_IDX_NAME, FILE_IDX_EVENT_START_TIME, FILE_IDX_RECORDING_START_TIME, FILE_IDX_LENGTH, FILE_IDX_DESCRIPTION, FILE_IDX_EXTENDED_DESCRIPTION, FILE_IDX_SERVICE_REFERENCE, FILE_IDX_SIZE, FILE_IDX_CUTS, FILE_IDX_TAGS
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
		self.file_type, self.name, self.event_start_time, self.short_description, self.extended_description, self.service_reference, self.cuts, self.tags = "", "", "", "", "", "", "", ""
		self.size = self.length = self.recording_start_time = 0
		self.path = path
		if self.path:
			file_data = FileCache.getInstance().getFile(self.path)
			if file_data is not None:
				self.file_type = file_data[FILE_IDX_TYPE]
				self.event_start_time = file_data[FILE_IDX_EVENT_START_TIME]
				self.recording_start_time = file_data[FILE_IDX_RECORDING_START_TIME]
				self.name = file_data[FILE_IDX_NAME] if file_data[FILE_IDX_NAME] != "trashcan" else _(file_data[FILE_IDX_NAME])
				self.short_description = file_data[FILE_IDX_DESCRIPTION]
				self.extended_description = file_data[FILE_IDX_EXTENDED_DESCRIPTION]
				self.length = file_data[FILE_IDX_LENGTH]
				self.service_reference = file_data[FILE_IDX_SERVICE_REFERENCE]
				self.size = file_data[FILE_IDX_SIZE]
				self.tags = file_data[FILE_IDX_TAGS]
				self.cut_list = unpackCutList(file_data[FILE_IDX_CUTS])

	def getName(self):
		#EventName NAME
		return self.name

	def getServiceReference(self):
		return self.service_reference

	def getTags(self):
		return self.tags

	def getEventId(self):
		return 0

	def getEventName(self):
		return self.name

	def getShortDescription(self):
		#EventName SHORT_DESCRIPTION
		return self.short_description

	def getExtendedDescription(self):
		#EventName EXTENDED_DESCRIPTION
		return self.extended_description

	def getBeginTimeString(self):
		return datetime.fromtimestamp(self.event_start_time).strftime(config.plugins.moviecockpit.movie_date_format.value)

	def getEventStartTime(self):
		return self.event_start_time

	def getRecordingStartTime(self):
		return self.recording_start_time

	def getDuration(self):
		return self.length

	def getLength(self):
		return self.length

	def getSize(self):
		if self.file_type == FILE_TYPE_FILE:
			size = self.size
		else:
			_count, size = FileCache.getInstance().getCountSize(self.path)
		return size
