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
import shutil
from RecordingUtils import isRecording
from CutListUtils import packCutList, unpackCutList, replaceLast, replaceLength, removeMarks, mergeCutList
from FileUtils import readFile, writeFile, deleteFile
from FileCache import FileCache
from FileCacheSQL import FILE_IDX_CUTS


def backupCutList(path):
	backup_path = path + ".save"
	if os.path.exists(path):
		shutil.copy2(path, backup_path)


def mergeBackupCutList(path):
	logger.debug("...")
	backup_path = path + ".save"
	ts_path = os.path.splitext(path)[0]
	if os.path.exists(backup_path):
		logger.debug("reading from backup file: %s", backup_path)
		cut_list = readCutList(ts_path)
		backup_cut_list = unpackCutList(readFile(backup_path))
		logger.debug("backup_cut_list: %s", backup_cut_list)
		cut_list = mergeCutList(cut_list, backup_cut_list)
		writeCutList(ts_path, cut_list)
		deleteFile(backup_path)
	else:
		logger.debug("no backup file found: %s", backup_path)


def updateCutList(path, play=None, length=None):
	logger.debug("play: %s, length: %s", play, length)
	if play is not None:
		cut_list = replaceLast(readCutList(path), play)
		writeCutList(path, cut_list)
	if length is not None:
		cut_list = replaceLength(cut_list, length)
		writeCutList(path, cut_list)


def removeCutListMarks(path):
	cut_list = removeMarks(readCutList(path))
	writeCutList(path, cut_list)


def deleteCutList(path):
	data = ""
	FileCache.getInstance().update(path, cuts=data)
	deleteFile(path)


def reloadCutList(path):
	data = readFile(path + ".cuts")
	FileCache.getInstance().update(path, cuts=data)
	cut_list = unpackCutList(data)
	return cut_list


def readCutList(path):
	cut_list = []
	logger.debug("reading cut_list from cache: %s", path)
	file_data = FileCache.getInstance().getFile(path)
	if file_data:
		data = file_data[FILE_IDX_CUTS]
		cut_list = unpackCutList(data)
	logger.info("cut_list: %s", cut_list)
	return cut_list


def writeCutList(path, cut_list):
	logger.debug("path: %s, cut_list: %s", path, cut_list)
	data = packCutList(cut_list)
	writeFile(path + ".cuts", data)

	# update file in cache
	logger.info("updating cut_list in cache: %s", path)
	FileCache.getInstance().update(path, cuts=data)

	# Always make a backup-copy when recording, it will be merged with enigma cutfile after recording has ended
	if isRecording(path):
		logger.debug("creating backup file: %s", path + ".cuts")
		backupCutList(path + ".cuts")
