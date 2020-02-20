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
from Bookmarks import getBookmarks
from FileCacheSQL import FileCacheSQL
from datetime import datetime
from ParserEitFile import ParserEitFile
from ParserMetaFile import ParserMetaFile
from CutListUtils import unpackCutList, ptsToSeconds, getCutListLength
from ServiceUtils import EXT_TS, EXT_VIDEO
from FileUtils import readFile
from DelayTimer import DelayTimer
from UnicodeUtils import convertToUtf8


SQL_DB_NAME = "/etc/enigma2/moviecockpit.db"


# file indexes
FILE_IDX_DIR = 0
FILE_IDX_TYPE = 1
FILE_IDX_PATH = 2
FILE_IDX_FILENAME = 3
FILE_IDX_EXT = 4
FILE_IDX_NAME = 5
FILE_IDX_EVENT_START_TIME = 6
FILE_IDX_RECORDING_START_TIME = 7
FILE_IDX_RECORDING_STOP_TIME = 8
FILE_IDX_LENGTH = 9
FILE_IDX_DESCRIPTION = 10
FILE_IDX_EXTENTED_DESCRIPTION = 11
FILE_IDX_SERVICE_REFERENCE = 12
FILE_IDX_SIZE = 13
FILE_IDX_CUTS = 14
FILE_IDX_TAGS = 15


# filetype values
FILE_TYPE_FILE = 1
FILE_TYPE_DIR = 2


instance = None


class FileCache(FileCacheSQL):

	def __init__(self):
		print("MVC-I: FileCache: __init__")
		FileCacheSQL.__init__(self, SQL_DB_NAME)

	@staticmethod
	def getInstance():
		global instance
		if instance is None:
			instance = FileCache()
		return instance

	### cache functions

	def add(self, filedata):
		#print("MVC: FileCache: add: path: %s" % filedata[FILE_IDX_PATH])
		# add to SQL database
		self.sqlInsert(filedata)

	### database row functions

	def exists(self, path):
		filedata = self.getFile(path)
		return filedata is not None

	def delete(self, path, filetype=FILE_TYPE_FILE):
		#print("MVC: FileCache: delete %s" % path)
		if filetype == FILE_TYPE_FILE:
			where = "path = \"" + path + "\""
			self.sqlDelete(where)
		elif filetype == FILE_TYPE_DIR:
			self.loadDatabase(sync=True)

	def update(self, path, **kwargs):
		#print("MVC: FileCache: update: %s, kwargs: %s" % (path, kwargs))
		filedata = self.getFile(path)
		if filedata:
			self.directory, self.filetype, self.path, self.filename, self.ext, self.name, self.event_start_time, self.recording_start_time, self.recording_stop_time, self.length, self.description, self.extended_description, self.service_reference, self.size, self.cuts, self.tags = filedata
			#print("MVC: FileCache: update: kwargs.items(): %s" % kwargs.items())
			for key, value in kwargs.items():
				#print("MVC: FileCache: update: key: %s, value: %s" % (key, value))
				setattr(self, key, value)
			self.delete(path)
			self.add((self.directory, self.filetype, self.path, self.filename, self.ext, self.name, self.event_start_time, self.recording_start_time, self.recording_stop_time, self.length, self.description, self.extended_description, self.service_reference, self.size, self.cuts, self.tags))

	def copy(self, src_path, dest_path, filetype=FILE_TYPE_FILE):
		if filetype == FILE_TYPE_FILE:
			src_path = os.path.normpath(src_path)
			dest_path = os.path.normpath(dest_path)
			#print("MVC: FileCache: copy: src_path: %s, dest_path: %s " % (src_path, dest_path))
			filedata = self.getFile(src_path)
			if filedata is not None:
				directory, filetype, path, filename, ext, name, event_start_time, recording_start_time, recording_stop_time, length, description, extended_description, service_reference, size, cuts, tags = filedata
				path = os.path.join(dest_path, filename) + ext
				# check of file already exists at destination
				dest_file = self.getFile(path)
				if dest_file is None:
					#print("MVC: FileCache: copy: dest_path: %s" % path)
					directory = dest_path
					self.add((directory, filetype, path, filename, ext, name, event_start_time, recording_start_time, recording_stop_time, length, description, extended_description, service_reference, size, cuts, tags))
				else:
					print("MVC-E: FileCache: copy: file already exists at destination")
			else:
				print("MVC-E: FileCache: copy: source file not found: src_path: %s" % src_path)
		elif filetype == FILE_TYPE_DIR:
			self.loadDatabase(sync=True)

	def move(self, src_path, dest_path, filetype=FILE_TYPE_FILE):
		if filetype == FILE_TYPE_FILE:
			src_path = os.path.normpath(src_path)
			dest_path = os.path.normpath(dest_path)
			#print("MVC: FileCache: move: src_path: %s, dest_path: %s" % (src_path, dest_path))
			srcfile = self.getFile(src_path)
			if srcfile is not None:
				directory, filetype, path, filename, ext, name, event_start_time, recording_start_time, recording_stop_time, length, description, extended_description, service_reference, size, cuts, tags = srcfile
				path = os.path.join(dest_path, filename) + ext
				directory = dest_path
				# check if file already exists at destination
				dest_file = self.getFile(path)
				if dest_file is None:
					#print("MVC: FileCache: move: dest_path: %s" % path)
					self.add((directory, filetype, path, filename, ext, name, event_start_time, recording_start_time, recording_stop_time, length, description, extended_description, service_reference, size, cuts, tags))
					self.delete(src_path)
				else:
					print("MVC-E: FileCache: move: source file already exists at destination: %s" % src_path)
					self.delete(src_path)
			else:
				print("MVC-E: FileCache: move: source file not found: src_path: %s" % src_path)
		elif filetype == FILE_TYPE_DIR:
			self.loadDatabase(sync=True)

	def getFile(self, path):
		where = "path = \"" + path + "\""
		#print("MVC: FileCache: getFile: where: %s" % where)
		filelist = self.sqlSelect(where)
		filedata = None
		if filelist:
			if len(filelist) == 1:
				filedata = filelist[0]
			else:
				print("MVC-E: FileCache: getFile: not a single response: " + str(filelist))
		return filedata

	def __resolveVirtualDirs(self, dirs):
		#print("MVC: FileCache: __resolveVirtualDirs: dirs: %s" % dirs)
		all_dirs = []
		bookmarks = getBookmarks()
		for adir in dirs:
			if adir in bookmarks:
				for bookmark in bookmarks:
					if bookmark not in all_dirs:
						all_dirs.append(bookmark)
			elif os.path.basename(adir) == "trashcan":
				for bookmark in bookmarks:
					trashcan_dir = bookmark + "/trashcan"
					if trashcan_dir not in all_dirs:
						all_dirs.append(trashcan_dir)
			else:
				if adir not in all_dirs:
					all_dirs.append(adir)

		#print("MVC: FileCache: __resolveVirtualDirs: all_dirs: %s" % all_dirs)
		return all_dirs

	def getFileList(self, dirs):
		#print("MVC: FileCache: getFileList: dirs: %s" % dirs)
		filelist = []
		all_dirs = self.__resolveVirtualDirs(dirs)
		if all_dirs:
			where = "("
			op = ""
			for directory in all_dirs:
				where += op + "directory = \"" + directory + "\""
				op = " OR "
			where += ") AND " + "filetype = " + str(FILE_TYPE_FILE)
			#print("MVC: FileCache: getFileList: where: %s" % where)
			filelist = self.sqlSelect(where)
		return filelist

	def getDirList(self, dirs):
		#print("MVC: FileCache: getDirlist: %s" % dirs)
		dirlist = []
		all_dirs = self.__resolveVirtualDirs(dirs)
		if all_dirs:
			where = "("
			op = ""
			for directory in all_dirs:
				where += op + "directory = \"" + directory + "\""
				op = " OR "
			where += ")"
			where += " AND " + "filename != \"trashcan\""
			where += " AND " + "filename != \"..\""
			where += " AND " + "filetype > " + str(FILE_TYPE_FILE)
			#print("MVC: FileCache: getDirList: where: %s" % where)
			dirlist = self.sqlSelect(where)
		return dirlist

	### utils

	def getCountSize(self, path):
		#print("MVC: FileCache: getCountSize: path: %s" % path)
		self.count = self.size = 0
		dirs = self.__resolveVirtualDirs([path])
		for adir in dirs:
			self.__getCountSize(adir)
		#print("MVC: FileCache: getCountSize: %s, %s" % (self.count, self.size))
		return self.count, self.size

	def __getCountSize(self, in_path):
		#print("MVC: FileCache: __getCountSize: in_path: %s" % in_path)
		where = "directory = \"" + in_path + "\""
		#print("MVC: FileCache: __getCountSize: where: %s" % where)
		filelist = self.sqlSelect(where)

		for directory, filetype, path, filename, _ext, _name, _event_start_time, _recording_start_time, _recording_stop_time, _length, _description, _extended_description, _service_reference, size, _cuts, _tags in filelist:
			#print("MVC: FileCache: __getCountSize: %s, %s" % (path, filetype))
			if path and filetype == FILE_TYPE_FILE and directory == in_path:
				#print("MVC: FileCache: __getCountSize: path: %s " % path)
				self.count += 1
				self.size += size
			if path and filetype > FILE_TYPE_FILE and directory.startswith(in_path) and filename != "..":
				self.__getCountSize(path)
		#print("MVC: FileCache: __getCountSize: %s, %s, %s" % (in_path, self.count, self.size))

	### database functions

	def closeDatabase(self):
		#print("MVC: FileCache: closeDatabase")
		self.sqlClose()

	def clearDatabase(self):
		#print("MVC: FileCache: clearDatabase")
		self.sqlClearTable()

	def loadDatabase(self, dirs=None, sync=False, callback=None):
		#print("MVC: FileCache: loadDatabase: dirs: %s" % dirs)
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

	def nextFileOp(self, callback):
		#print("MVC: FileCache: nextFileOp")
		if self.load_list:
			path, filetype = self.load_list.pop(0)
			self.loadDatabaseFile(path, filetype)
			DelayTimer(10, self.nextFileOp, callback)
		else:
			#print("MVC: FileCache: nextFileOp: done.")
			if callback:
				callback()

	### database load file/dir functions

	def reloadDatabaseFile(self, path, filetype=FILE_TYPE_FILE):
		where = "path = \"" + path + "\""
		self.sqlDelete(where)
		self.loadDatabaseFile(path, filetype)

	def loadDatabaseFile(self, path, filetype=FILE_TYPE_FILE):
		#print("MVC: FileCache: loadDatabaseFile: path: %s, filetype: %s" % (path, filetype))
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
		return (os.path.dirname(path), FILE_TYPE_DIR, path, os.path.basename(path), ext, name, event_start_time, recording_start_time, recording_stop_time, length, short_description, extended_description, service_reference, size, cuts, tags)

	def newFileData(self, path):

		def parseFilename(filename):
			#print("MVC: FileCache: parseFilename: filename: %s" % filename)
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
			#print("MVC: FileCache: parseFilename: date: %s" % date)

			if len(words) > 1:
				service_name = words[1]
				#print("MVC: FileCache: parseFilename: service_name: %s" % service_name)
			if len(words) > 2:
				name = words[2]

			#print("MVC: FileCache: parseFilename: filename: %s" % filename)
			cutno = ""
			if name[-4:-3] == "_" and name[-3:].isdigit():
				cutno = name[-3:]
				name = name[:-4]

			if date:
				dt = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
				start_time = int(time.mktime(dt.timetuple()))
			#print("MVC: FileCache: parseFilename: filename: %s, cutno: %s" % (filename, cutno))
			return start_time, service_name, name, cutno

		def getEitData(eit, recording_start_time, recording_stop_time):
			print("MVC-I: FileCache: getEitData: recording_start_time: %s, recording_stop_time: %s" % (recording_start_time, recording_stop_time))
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
			#print("MVC: FileCache: getEitData: event_start_time: %s, length: %s" % (event_start_time, length))
			return name, event_start_time, length, short_description, extended_description

		def getMetaData(meta, recording_start_time, recording_stop_time, timer_start_time, timer_stop_time):
			print("MVC-I: FileCache: getMetaData: recording_start_time: %s, recording_stop_time: %s, timer_start_time: %s, timer_stop_time: %s" % (recording_start_time, recording_stop_time, timer_start_time, timer_stop_time))
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
			#print("MVC: FileCache: getMetaData: start_time: %s, length: %s" % (start_time, length))
			return name, start_time, length, short_description, extended_description

		#print("MVC: FileCache: newFileData: %s" % path)
		filepath, ext = os.path.splitext(path)
		filename = os.path.basename(filepath)
		name = filename
		short_description, extended_description, service_reference, tags = "", "", "", ""
		recording_start_time = recording_stop_time = length = size = 0
		cuts = readFile(path + ".cuts")
		event_start_time = int(os.stat(path).st_ctime)
		size = os.path.getsize(path)

		if ext in EXT_TS:
			start_time, _service_name, name, cutno = parseFilename(filename)
			#print("MVC: FileCache: newFileData: start_time: %s, service_name: %s, filename: %s, cutno: %s" % (start_time, _service_name, filename, cutno))
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

		#print("MVC: FileCache: newFileData: name: %s, event_start_time %s, length: %s" % (name, datetime.fromtimestamp(event_start_time), length))
		return (os.path.dirname(path), FILE_TYPE_FILE, path, filename, ext, name, event_start_time, recording_start_time, recording_stop_time, length, short_description, extended_description, service_reference, size, cuts, tags)

	### database load list functions

	def __getDirLoadList(self, adir):
		#print("MVC: FileCache: getDirLoadList: adir: %s" % adir)
		load_list = []
		if os.path.exists(adir):
			walk_listdir = os.listdir(adir)
			for walk_name in walk_listdir:
				path = os.path.join(adir, walk_name)
				if os.path.islink(path):
					path = os.path.realpath(path)
				if os.path.isfile(path):
					_filename, ext = os.path.splitext(path)
					if ext in EXT_VIDEO:
						load_list.append((path, FILE_TYPE_FILE))
				elif os.path.isdir(path):
					load_list.append((path, FILE_TYPE_DIR))
					load_list += self.__getDirLoadList(path)
			load_list.append((os.path.join(adir, ".."), FILE_TYPE_DIR))
		else:
			print("MVC-E: FileCache: __getDirLoadList: adir: %s" % adir)
		return load_list

	def getDirsLoadList(self, dirs):
		#print("MVC: FileCache: getDirsLoadList: dirs: %s" % dirs)
		load_list = []
		for adir in dirs:
			load_list += self.__getDirLoadList(adir)
		return load_list
