#!/usr/bin/python
# encoding: utf-8
#
# Copyright (C) 2018 dream-alpha
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
import struct
import shutil
from bisect import insort
from Components.config import config
from FileUtils import readFile

cutsParser = struct.Struct('>QI')  # big-endian, 64-bit PTS and 32-bit type

# InfoBarCueSheetSupport types
CUT_TYPE_IN = 0
CUT_TYPE_OUT = 1
CUT_TYPE_MARK = 2
CUT_TYPE_LAST = 3
# Additional custom MVC specific types
# Have to be removed before starting a player
CUT_TYPE_LENGTH = 5


def readCutsFile(path):
	#print("MVC: CutListUtils: readCutsFile: " + path)
	data = ""
#	cut_list = []
	if os.path.isfile(path):
		data = readFile(path)
#		cut_list = unpackCutList(data)
	#print("MVC: CutListUtils: readCutsFile: cut_list: " + str(cut_list))
	return data


def writeCutsFile(path, data):
	f = open(path, 'wb')
	f.write(data)
	f.close()


def backupCutsFilePath(path):
	return path + ".save"


def backupCutsFile(path):
	backup_path = backupCutsFilePath(path)
	if os.path.exists(path):
		shutil.copy2(path, backup_path)


def mergeBackupCutsFile(path, cut_list):
	#print("MVC: CutListUtils: mergeBackupCutsFile")
	backup_cut_file = backupCutsFilePath(path)
	if os.path.exists(backup_cut_file):
		#print("MVC: CutListUtils: mergeBackupCutsFile: reading from Backup-File")
		data = readCutsFile(backup_cut_file)
		backup_cut_list = unpackCutList(data)
		#print("MVC: CutListUtils: mergeBackupCutsFile: backup_cut_list: %s" % backup_cut_list)
		cut_list = mergeCutList(cut_list, backup_cut_list)
		writeCutsFile(path, packCutList(cut_list))
		os.remove(backup_cut_file)
	else:
		#print("MVC: CutListUtils: mergeBackupCutsFile: no Backup-File found: " + backup_path)
		pass
	return cut_list

def deleteCutsFile(path):
	try:
		os.remove(path)
	except Exception as e:
		print("MVC: CutListUtils: deleteCutsFile:exception:\n" + str(e))

def verifyCutList(cut_list):
	if config.MVC.movie_ignore_firstcuts.value:
		# Don't care about the first 10 seconds
		for cp in cut_list:
			pts, _what = cp
			if pts < secondsToPts(10):
				cut_list.remove(cp)
	return cut_list


def ptsToSeconds(pts):
	# Cut files are using the presentation time stamp time format
	# pts has a resolution of 90kHz
	return int(pts / 90 / 1000)


def secondsToPts(seconds):
	return int(seconds * 90 * 1000)


def packCutList(cut_list):
	data = ""
	for (pts, what) in cut_list:
		data += struct.pack('>QI', pts, what)
	return data


def insortCutList(cut_list, pts, what):
	INSORT_SCOPE = 45000  # 0.5 seconds * 90 * 1000
	for (clpts, clwhat) in cut_list:
		if clwhat == what:
			if clpts - INSORT_SCOPE < pts < clpts + INSORT_SCOPE:
				# Found a conflicting entry, replace it to avoid doubles and short jumps
				cut_list.remove((clpts, clwhat))
	insort(cut_list, (pts, what))
	return cut_list


def unpackCutList(data):
	cut_list = []
	pos = 0
	while pos + 12 <= len(data):
		(pts, what) = struct.unpack('>QI', data[pos:pos + 12])
		cut_list = insortCutList(cut_list, long(pts), what)
		# Next cut_list entry
		pos += 12
	return cut_list


def mergeCutList(destination_cut_list, source_cut_list):
	# merge cut_list2 into cut_list1
	for pts, what in source_cut_list:
		destination_cut_list = insortCutList(destination_cut_list, long(pts), what)
	return destination_cut_list


def getCutListLast(cut_list):
	for (pts, what) in cut_list:
		if what == CUT_TYPE_LAST:
			return pts
	return 0


def replaceLast(cut_list, pts):
	for cp in cut_list:
		_pts, what = cp
		if what == CUT_TYPE_LAST:
			cut_list.remove(cp)
	if pts > 0:
		cut_list = insortCutList(cut_list, pts, CUT_TYPE_LAST)
	return cut_list


def getCutListLength(cut_list):
	for (pts, what) in cut_list:
		if what == CUT_TYPE_LENGTH:
			return pts
	return 0


def replaceLength(cut_list, pts):
	for cp in cut_list:
		_pts, what = cp
		if what == CUT_TYPE_LENGTH:
			cut_list.remove(cp)
	if pts > 0:
		cut_list = insortCutList(cut_list, pts, CUT_TYPE_LENGTH)
	return cut_list

def removeMarks(cut_list):
	for cp in cut_list:
		_pts, what = cp
		if what == CUT_TYPE_MARK:
			cut_list.remove(cp)
	return cut_list
