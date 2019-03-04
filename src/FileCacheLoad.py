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
import datetime
from ParserEitFile import ParserEitFile
from ParserMetaFile import ParserMetaFile
#from ServiceReference import ServiceReference
from CutListUtils import unpackCutList, ptsToSeconds, getCutListLength
from Components.config import config
from Bookmarks import Bookmarks
from MediaTypes import extTS, extVideo
from RecordingUtils import getRecording
from FileUtils import readFile
from ServiceCenter import str2date
from FileCache import FILE_TYPE_FILE, FILE_TYPE_DIR
from FileCacheSQL import FileCacheSQL
from DelayedFunction import DelayedFunction

instance = None


class FileCacheLoad(FileCacheSQL, Bookmarks, object):

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

	def doFileOp(self, entry):
		path, file_type = entry
		self.loadDatabaseFile(path, file_type)
		DelayedFunction(10, self.nextFileOp)

	def nextFileOp(self):
		#print("MVC: FileCacheLoad: nextFileOp")
		if self.load_list:
			entry = self.load_list.pop(0)
			self.doFileOp(entry)
		else:
			#print("MVC: FileCacheLoad: nextFileOp: done.")
			pass

	def loadDatabase(self, dirs=None):
		#print("MVC: FileCacheLoad: loadDatabase: dirs: %s" % dirs)
		if dirs is None:
			dirs = self.getBookmarks()
		self.clearDatabase()
		self.load_list = self.getDirsLoadList(dirs)
		DelayedFunction(10, self.nextFileOp)

	### database directory functions

	def makeDir(self, path):
		self.loadDatabase([path])

	def moveDir(self, _src_path, _dest_path):
		self.loadDatabase()

	def copyDir(self, _src_path, _dest_path):
		self.loadDatabase()

	def deleteDir(self, _path):
		self.loadDatabase()

	### database load file/dir functions

	def loadDatabaseFile(self, path, file_type=FILE_TYPE_FILE):
		#print("MVC: FileCacheLoad: loadDatabaseFile: path: %s, file_type: %s" % (path, file_type))
		if file_type == FILE_TYPE_FILE:
			filedata = self.__newFileData(path)
			self.sqlInsert(filedata)
		elif file_type == FILE_TYPE_DIR:
			filedata = self.__newDirData(path)
			self.sqlInsert(filedata)

	def __newDirData(self, path):

		def convertToUtf8(name):
			try:
				name.decode('utf-8')
			except UnicodeDecodeError:
				try:
					name = name.decode("cp1252").encode("utf-8")
				except UnicodeDecodeError:
					name = name.decode("iso-8859-1").encode("utf-8")
			return name

		ext, description, extended_description, service_reference, cuts, tags = "", "", "", "", "", ""
		size, length = 0, 0
		date = str(datetime.datetime.fromtimestamp(os.stat(path).st_ctime))[0:19]
		name = convertToUtf8(os.path.basename(path))
		filedata = (os.path.dirname(path), FILE_TYPE_DIR, path, os.path.basename(path), ext, name, date, length, description, extended_description, service_reference, size, cuts, tags)
		return filedata

	def __newFileData(self, path):

		def parseCutNo(filename):
			#print("MVC: FileCacheLoad: parseCutNo: filename: %s" % filename)
			cutno = ""
			if filename[-4:-3] == "_" and filename[-3:].isdigit():
				cutno = filename[-3:]
				filename = filename[:-4]
			#print("MVC: FileCacheLoad: parseCutNo: filename: %s, cutno: %s" % (filename, cutno))
			return cutno, filename

		def parseDate(filename):
			#print("MVC: FileCacheLoad: parseDate: filename: %s" % filename)
			date = ""
			# extract title from recording filename
			filename = filename.strip()
			if filename[0:8].isdigit():
				if filename[8] == " " and filename[9:13].isdigit():
					# Default: filename = YYYYMMDD TIME - service_name
					d = filename[0:13]
					dyear = d[0:4]
					dmonth = d[4:6]
					dday = d[6:8]
					dhour = d[9:11]
					dmin = d[11:13]
					date = dyear + "-" + dmonth + "-" + dday + " " + dhour + ":" + dmin + ":" + "00"
			#print("MVC: FileCacheLoad: parseDate: date: %s" % date)
			return date

		#print("MVC: FileCacheLoad: __newFileData: %s" % path)
		filepath, ext = os.path.splitext(path)
		filename = os.path.basename(filepath)

		description, extended_description, service_reference, tags = "", "", "", ""
		length = 0
		date = str(datetime.datetime.fromtimestamp(os.stat(path).st_ctime))[0:19]
		size = os.path.getsize(path)
		name = filename
		cuts = readFile(path + ".cuts")

		if ext in extTS:
			filename_date = str2date(parseDate(os.path.basename(path)))
			#print("MVC: FileCacheLoad: __newFileData: filename date: %s" % filename_date)
			if filename_date:
				date = str(filename_date + datetime.timedelta(minutes=config.recording.margin_before.value))

			recording = getRecording(path, False)
			if recording:
				#print("MVC: FileCacheLoad: __newFileData: recording")
				timer_begin, timer_end, _service_reference = recording
				date = str(datetime.datetime.fromtimestamp(timer_begin))
				length = timer_end - timer_begin
				#print("MVC: FileCacheLoad: __newFileData: timer_begin: %s, length: %s" % (date, length / 60))

			eit = ParserEitFile(path)
			if eit:
				eit_name = eit.getName()
				if eit_name:
					name = eit_name
					cutno, _filename = parseCutNo(filename)
					if cutno:
						name = "%s (%s)" % (name, cutno)

				if length == 0:
					length = eit.getLengthInSeconds()

				description = eit.getShortDescription()
				extended_description = eit.getExtendedDescription()

			meta = ParserMetaFile(path)
			if meta:
				service_reference = meta.getServiceReference()
				tags = meta.getTags()

#				service = ServiceReference(service_reference)
#				if service is not None:
#					service_name = service.getServiceName()
#				#print("MVC: FileCacheLoad: __newFileData: service_name: %s" % service_name)
		else:
			length = ptsToSeconds(getCutListLength(unpackCutList(cuts)))

		return(os.path.dirname(path), FILE_TYPE_FILE, path, filename, ext, name, date, length, description, extended_description, service_reference, size, cuts, tags)

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
			if os.path.isfile(path):
				_filename, ext = os.path.splitext(path)
				if ext in extVideo:
					self.load_list.append((path, FILE_TYPE_FILE))
			elif os.path.isdir(path):
				#print("MVC: FileCacheLoad: __getDirLoadList: dir: %s" % path)
				self.load_list.append((path, FILE_TYPE_DIR))
				self.__getDirLoadList(path)
			elif os.path.islink(path):
				print("MVC-I: FileCacheLoad: __getDirLoadList: unsupported link: %s" % path)

		self.load_list.append((os.path.join(adir, ".."), FILE_TYPE_DIR))

		return self.load_list

	def getDirsLoadList(self, dirs):
		#print("MVC: FileCacheLoad: getDirsLoadList: dirs: %s" % dirs)
		self.load_list = []
		for adir in dirs:
			self.__getDirLoadList(adir)
		return self.load_list
