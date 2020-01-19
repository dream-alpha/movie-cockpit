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


import os
import time
from datetime import datetime
from ParserEitFile import ParserEitFile
from ParserMetaFile import ParserMetaFile
#from ServiceReference import ServiceReference
from CutListUtils import unpackCutList, ptsToSeconds, getCutListLength
from Bookmarks import getBookmarks
from ServiceUtils import extTS, extVideo
from FileUtils import readFile
from FileCache import FILE_TYPE_FILE, FILE_TYPE_DIR
from FileCacheSQL import FileCacheSQL
from DelayTimer import DelayTimer
from UnicodeUtils import convertToUtf8


instance = None


class FileCacheLoad(FileCacheSQL):

	def __init__(self):
		print("MVC-I: FileCacheLoad: __init__")
		FileCacheSQL.__init__(self)

	@staticmethod
	def getInstance():
		global instance
		if instance is None:
			instance = FileCacheLoad()
		return instance

	### database functions

	def closeDatabase(self):
		#print("MVC: FileCacheLoad: closeDatabase")
		self.sqlClose()

	def clearDatabase(self):
		#print("MVC: FileCacheLoad: clearDatabase")
		self.sqlClearTable()

	def nextFileOp(self, callback):
		#print("MVC: FileCacheLoad: nextFileOp")
		if self.load_list:
			path, filetype = self.load_list.pop(0)
			self.loadDatabaseFile(path, filetype)
			DelayTimer(10, self.nextFileOp, callback)
		else:
			#print("MVC: FileCacheLoad: nextFileOp: done.")
			if callback:
				callback()

	def loadDatabase(self, dirs=None, sync=False, callback=None):
		#print("MVC: FileCacheLoad: loadDatabase: dirs: %s" % dirs)
		if dirs is None:
			dirs = getBookmarks()
		if dirs:
			self.clearDatabase()
			self.load_list = self.getDirsLoadList(dirs)
			if sync:
				for path, filetype in self.load_list:
					self.loadDatabaseFile(path, filetype)
			else:
				DelayTimer(10, self.nextFileOp, callback)

	### database directory functions

	def makeDir(self, path):
		self.loadDatabase([path], sync=True)

	def moveDir(self, _src_path, _dest_path):
		self.loadDatabase(sync=True)

	def copyDir(self, _src_path, _dest_path):
		self.loadDatabase(sync=True)

	def deleteDir(self, _path):
		self.loadDatabase(sync=True)

	### database load file/dir functions

	def reloadDatabaseFile(self, path, filetype=FILE_TYPE_FILE):
		where = "path = \"" + path + "\""
		self.sqlDelete(where)
		self.loadDatabaseFile(path, filetype)

	def loadDatabaseFile(self, path, filetype=FILE_TYPE_FILE):
		#print("MVC: FileCacheLoad: loadDatabaseFile: path: %s, filetype: %s" % (path, filetype))
		if filetype == FILE_TYPE_FILE:
			filedata = self.newFileData(path)
			self.sqlInsert(filedata)
		elif filetype == FILE_TYPE_DIR:
			filedata = self.newDirData(path)
			self.sqlInsert(filedata)

	def newDirData(self, path):
		ext, short_description, extended_description, service_reference, cuts, tags = "", "", "", "", "", ""
		size = length = recording_start_time = recording_stop_time = 0
		event_start_time = int(os.stat(path).st_ctime)
		name = convertToUtf8(os.path.basename(path))
		filedata = (os.path.dirname(path), FILE_TYPE_DIR, path, os.path.basename(path), ext, name, event_start_time, recording_start_time, recording_stop_time, length, short_description, extended_description, service_reference, size, cuts, tags)
		return filedata

	def newFileData(self, path):

		def parseFilename(filename):
			#print("MVC: FileCacheLoad: parseFilename: filename: %s" % filename)
			name = filename
			date, service_name = "", ""
			start_time = 0

			# extract title from recording filename
			words = filename.split(" - ", 2)

			date_string = words[0]
			if date_string[0:8].isdigit():
				if date_string[8] == " " and date_string[9:13].isdigit():
					# Default: filename = YYYYMMDD TIME - service_name
					d = date_string[0:13]
					dyear = d[0:4]
					dmonth = d[4:6]
					dday = d[6:8]
					dhour = d[9:11]
					dmin = d[11:13]
					date = dyear + "-" + dmonth + "-" + dday + " " + dhour + ":" + dmin + ":" + "00"
			#print("MVC: FileCacheLoad: parseFilename: date: %s" % date)

			if len(words) > 1:
				service_name = words[1]
				#print("MVC: FileCacheLoad: parseFilename: service_name: %s" % service_name)
			if len(words) > 2:
				name = words[2]

			#print("MVC: FileCacheLoad: parseFilename: filename: %s" % filename)
			cutno = ""
			if name[-4:-3] == "_" and name[-3:].isdigit():
				cutno = name[-3:]
				name = name[:-4]

			if date:
				dt = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
				start_time = int(time.mktime(dt.timetuple()))
			#print("MVC: FileCacheLoad: parseFilename: filename: %s, cutno: %s" % (filename, cutno))
			return start_time, service_name, name, cutno

		def getEitData(eit, recording_start_time, recording_stop_time):
			print("MVC-I: FileCacheLoad: getEitData: recording_start_time: %s, recording_stop_time: %s" % (recording_start_time, recording_stop_time))
			name = eit["name"]
			event_start_time = eit["start"]
			length = eit["length"]
			short_description = eit["short_description"]
			extended_description = eit["description"]
			if recording_start_time and (recording_start_time > event_start_time):
				length -= recording_start_time - event_start_time
				event_start_time = recording_start_time
			if recording_stop_time and (recording_stop_time > event_start_time) and (recording_stop_time < event_start_time + length):
				length = recording_stop_time - event_start_time
			elif recording_stop_time and (recording_stop_time < event_start_time):
				length = 0
			#print("MVC: FileCacheLoad: getEitData: event_start_time: %s, length: %s" % (event_start_time, length))
			return name, event_start_time, length, short_description, extended_description

		def getMetaData(meta, recording_start_time, recording_stop_time, timer_start_time, timer_stop_time):
			print("MVC-I: FileCacheLoad: getMetaData: recording_start_time: %s, recording_stop_time: %s, timer_start_time: %s, timer_stop_time: %s" % (recording_start_time, recording_stop_time, timer_start_time, timer_stop_time))
			name = meta["name"]
			start_time = meta["rec_time"]
			if meta["recording_margin_before"]:
				start_time += meta["recording_margin_before"]
			length = 0
			short_description = ""
			extended_description = ""

			if timer_start_time and timer_stop_time:
				start = timer_start_time
				stop = timer_stop_time
				if recording_start_time and recording_start_time > timer_start_time:
					start = recording_start_time
				if recording_stop_time > start and recording_stop_time < timer_stop_time:
					stop = recording_stop_time
				length = stop - start
			#print("MVC: FileCacheLoad: getMetaData: start_time: %s, length: %s" % (start_time, length))
			return name, start_time, length, short_description, extended_description

		#print("MVC: FileCacheLoad: newFileData: %s" % path)
		filepath, ext = os.path.splitext(path)
		filename = os.path.basename(filepath)
		name = filename
		short_description, extended_description, service_reference, tags = "", "", "", ""
		recording_start_time = recording_stop_time = length = size = 0
		cuts = readFile(path + ".cuts")
		event_start_time = int(os.stat(path).st_ctime)
		size = os.path.getsize(path)

		if ext in extTS:
			start_time, _service_name, name, cutno = parseFilename(filename)
			#print("MVC: FileCacheLoad: newFileData: filename date: %s, service_name: %s, filename: %s, cutno: %s" % (filename_date, _service_name, filename, cutno))
			if start_time:
				event_start_time = start_time
			meta = ParserMetaFile(path).getMeta()
			meta_name = meta["name"]
			eit = ParserEitFile(path).getEit()
			eit_name = eit["name"]

			if eit_name and meta_name:
				service_reference = meta["service_reference"]
				tags = meta["tags"]
				recording_start_time = meta["recording_start_time"]
				recording_stop_time = meta["recording_stop_time"]
				timer_start_time = meta["timer_start_time"]
				timer_stop_time = meta["timer_stop_time"]

				eit_event_start_time = eit["start"]

				if timer_stop_time and eit_event_start_time and eit_event_start_time >= timer_stop_time:
					data = getMetaData(meta, recording_start_time, recording_stop_time, timer_start_time, timer_stop_time)
				else:
					data = getEitData(eit, recording_start_time, recording_stop_time)
				name, event_start_time, length, short_description, extended_description = data
				if cutno:
					name = "%s (%s)" % (name, cutno)
		else:
			length = ptsToSeconds(getCutListLength(unpackCutList(cuts)))

		print("MVC: FileCacheLoad: newFileData: name: %s, event_start_time %s, length: %s" % (name, datetime.fromtimestamp(event_start_time), length))
		return(os.path.dirname(path), FILE_TYPE_FILE, path, filename, ext, name, event_start_time, recording_start_time, recording_stop_time, length, short_description, extended_description, service_reference, size, cuts, tags)

	### database load list functions

	def __getDirLoadList(self, adir):
		#print("MVC: FileCacheLoad: getDirLoadList: adir: %s" % adir)
		try:
			walk_listdir = os.listdir(adir)
		except IOError as e:
			print("MVC-E: FileCacheLoad: __getDirLoadList: exception: %s" % e)
			return self.load_list

		for walk_name in walk_listdir:
			path = os.path.join(adir, walk_name)
			if os.path.islink(path):
				path = os.path.realpath(path)
			if os.path.isfile(path):
				_filename, ext = os.path.splitext(path)
				if ext in extVideo:
					self.load_list.append((path, FILE_TYPE_FILE))
			elif os.path.isdir(path):
				#print("MVC: FileCacheLoad: __getDirLoadList: dir: %s" % path)
				self.load_list.append((path, FILE_TYPE_DIR))
				self.__getDirLoadList(path)

		self.load_list.append((os.path.join(adir, ".."), FILE_TYPE_DIR))

		return self.load_list

	def getDirsLoadList(self, dirs):
		#print("MVC: FileCacheLoad: getDirsLoadList: dirs: %s" % dirs)
		self.load_list = []
		for adir in dirs:
			self.__getDirLoadList(adir)
		return self.load_list
