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


from Debug import logger
import os
from Components.config import config
from Plugins.SystemPlugins.CacheCockpit.FileCache import FileCache, FILE_TYPE_DIR
from Plugins.SystemPlugins.CacheCockpit.FileCacheSQL import FILE_IDX_TYPE, FILE_IDX_NAME, FILE_IDX_EVENT_START_TIME, FILE_IDX_PATH
from ServiceUtils import getService
from ConfigInit import sort_modes


def getFile4Path(file_list, path):
	afile = None
	for __afile in file_list:
		if __afile and __afile[FILE_IDX_PATH] == path:
			afile = __afile
			break
	return afile


def getIndex4Path(file_list, path):
	index = 0
	for i, afile in enumerate(file_list):
		if afile and afile[FILE_IDX_PATH] == path:
			index = i
			break
	return index


def getService4Path(file_list, path):
	service = None
	for afile in file_list:
		if afile and afile[FILE_IDX_PATH] == path:
			service = getService(path, afile[FILE_IDX_NAME])
			break
	return service


def createFileList(path, include_all_dirs=True):
	logger.info("path: %s", path)
	return FileCache.getInstance().getFileList([path], include_all_dirs)


def createDirList(path):
	logger.info("path: %s", path)
	return FileCache.getInstance().getDirList([path])


def createCustomList(path):
	logger.info("path: %s", path)
	file_list = []
	afile = FileCache.getInstance().getFile(os.path.join(path, ".."))
	if afile: # path is not a bookmark
		file_list.append(afile)
	else:  # path is a bookmark
		if config.plugins.moviecockpit.trashcan_enable.value and config.plugins.moviecockpit.trashcan_show.value:
			file_list.append(FileCache.getInstance().getFile(path + "/trashcan"))
	logger.debug("file_list: %s", str(file_list))
	return file_list


def sortList(file_list, sort_mode):
	file_type_list = [] if config.plugins.moviecockpit.directories_ontop.value else [FILE_TYPE_DIR]
	# This will find all unsortable items
	tmp_list = [i for i in file_list if i and i[FILE_IDX_TYPE] in file_type_list or i[FILE_IDX_NAME] == ".."]
	# Extract list items to be sorted
	file_list = [i for i in file_list if i and i[FILE_IDX_TYPE] not in file_type_list and i[FILE_IDX_NAME] != ".."]
	# Always sort via extension and sorttitle
	tmp_list.sort(key=lambda x: (x[FILE_IDX_TYPE], x[FILE_IDX_NAME].lower()))

	mode, order = sort_modes[sort_mode][0]

	if mode == "date":
		if not order:
			file_list.sort(key=lambda x: (x[FILE_IDX_EVENT_START_TIME], x[FILE_IDX_NAME].lower()), reverse=True)
		else:
			file_list.sort(key=lambda x: (x[FILE_IDX_EVENT_START_TIME], x[FILE_IDX_NAME].lower()))

	elif mode == "alpha":
		if not order:
			file_list.sort(key=lambda x: (x[FILE_IDX_NAME].lower(), -x[FILE_IDX_EVENT_START_TIME]))
		else:
			file_list.sort(key=lambda x: (x[FILE_IDX_NAME].lower(), x[FILE_IDX_EVENT_START_TIME]), reverse=True)

	return tmp_list + file_list
