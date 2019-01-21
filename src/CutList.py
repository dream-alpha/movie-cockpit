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
from RecordingUtils import isRecording
from CutListUtils import packCutList, unpackCutList, readCutsFile, writeCutsFile,\
	replaceLast, replaceLength, removeMarks, mergeBackupCutsFile, verifyCutList, backupCutsFile
from FileUtils import deleteFile

# [Cutlist.Workaround] Creates a backup of the cutlist during recording and merge it with the cutlist-file from enigma after recording

# http://git.opendreambox.org/?p=enigma2.git;a=blob;f=doc/FILEFORMAT

# cut_list data structure
# cut_list[x][0] = pts  = long long
# cut_list[x][1] = what = long

class CutList(object):

	ENABLE_RESUME_SUPPORT = True

	def __init__(self, path=None):
		#print("MVC: CutList: __init__: path: %s" % path)
		self.cut_list = []
		self.cut_file = None
		if path:
			self.cut_file = path + ".cuts"
			self.cut_list = self.__readCutFile(self.cut_file)
			#print("MVC: CutList: __init__: cuts were read form cache: %s" % self.cut_list)

	def updateFromCuesheet(self):
		#print("MVC: CutList: updateFromCuesheet")
		self.cut_list = mergeBackupCutsFile(self.cut_file, self.cut_list)
		data = packCutList(self.cut_list)
		from FileCache import FileCache
		FileCache.getInstance().update(os.path.splitext(self.cut_file)[0], pcuts=data)

	def setCutList(self, cut_list):
		#print("MVC: CutList: setCutList: " + str(cut_list))
		self.cut_list = cut_list
		self.__writeCutFile(self.cut_file, self.cut_list)

	def getCutList(self):
		return self.cut_list

	def resetLastCutList(self):
		#print("MVC: resetLastCutList: self.cut_file: %s, self.cut_list: %s" % (self.cut_file, self.cut_list))
		self.cut_list = replaceLast(self.cut_list, 0)
		#print("MVC: resetLastCutList: self.cut_list: %s" % self.cut_list)
		self.__writeCutFile(self.cut_file, self.cut_list)

	def updateCutList(self, play, length):
		#print("MVC: CutList: updateCutList: play: " + str(play) + ", length: " + str(length))
		self.cut_list = replaceLast(self.cut_list, play)
		self.cut_list = replaceLength(self.cut_list, length)
		self.__writeCutFile(self.cut_file, self.cut_list)

	def removeMarksCutList(self):
		self.cut_list = removeMarks(self.cut_list)
		self.__writeCutFile(self.cut_file, self.cut_list)

	def deleteFileCutList(self):
		from FileCache import FileCache
		data = ""
		FileCache.getInstance().update(os.path.splitext(self.cut_file)[0], pcuts=data)
		deleteFile(self.cut_file)

	def reloadCutListFromFile(self):
		from FileCache import FileCache
		data = readCutsFile(self.cut_file)
		FileCache.getInstance().update(os.path.splitext(self.cut_file)[0], pcuts=data)
		self.cut_list = verifyCutList(unpackCutList(data))
		return self.cut_list

	def __readCutFile(self, path):
		from FileCache import FileCache, FILE_IDX_CUTS
		cut_list = []
		if path:
			#print("MVC: CutList: __readCutFile: reading cut_list from cache: " + os.path.splitext(path)[0])
			filedata = FileCache.getInstance().getFile(os.path.splitext(path)[0])
			data = filedata[FILE_IDX_CUTS]
			cut_list = unpackCutList(data)
			#print("MVC: CutList: __readCutFile: cut_list: " + str(cut_list))
		return cut_list

	def __writeCutFile(self, path, cut_list):
		from FileCache import FileCache
		#print("MVC: CutList: __writeCutFile: %s, cut_list: %s" % (path, cut_list))
		if path:
			data = packCutList(cut_list)
			writeCutsFile(path, data)

			# update file in cache
			#print("MVC: CutList: __writeCutFile: cut_list: " + str(cut_list))
			#print("MVC: CutList: __writeCutFile: updating cut_list in cache: " + os.path.splitext(path)[0])
			FileCache.getInstance().update(os.path.splitext(path)[0], pcuts=data)

			# [Cutlist.Workaround]
			# Always make a backup-copy when recording, it will be merged with enigma-cutfile after recording
			ts_path, __ = os.path.splitext(path)
			if isRecording(ts_path):
				#print("MVC: CutList: __writeCutFile: creating backup file: " + path)
				backupCutsFile(ts_path)
