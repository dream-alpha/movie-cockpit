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
from sqlite3 import dbapi2 as sqlite
import datetime
from ParserEitFile import ParserEitFile
from ParserMetaFile import ParserMetaFile
from CutListUtils import readCutsFile, unpackCutList, ptsToSeconds, getCutListLength
from Components.config import config
from Bookmarks import Bookmarks
from MediaTypes import extTS, extVideo, extBlu
from RecordingUtils import getRecording

# file indexes
FILE_IDX_DIR = 0
FILE_IDX_TYPE = 1
FILE_IDX_PATH = 2
FILE_IDX_FILENAME = 3
FILE_IDX_EXT = 4
FILE_IDX_NAME = 5
FILE_IDX_DATE = 6
FILE_IDX_LENGTH = 7
FILE_IDX_DESCRIPTION = 8
FILE_IDX_EXTENTED_DESCRIPTION = 9
FILE_IDX_SERVICE_REFERENCE = 10
FILE_IDX_SIZE = 11
FILE_IDX_CUTS = 12
FILE_IDX_TAGS = 13

# filetype values
TYPE_ISFILE = 1
TYPE_ISDIR = 2
TYPE_ISLINK = 3


def convertToUtf8(name):
	try:
		name.decode('utf-8')
	except UnicodeDecodeError:
		try:
			name = name.decode("cp1252").encode("utf-8")
		except UnicodeDecodeError:
			name = name.decode("iso-8859-1").encode("utf-8")
	return name


def str2date(date_string):
	date = None
	#print("MVC: FileCache: str2date: " + date_string)
	try:
		date = datetime.datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
	except ValueError:
		print("MVC-E: FileCache: str2date: exception: %s" % date_string)
	return date


def parseDate(filename):
	#print("MVC: FileCache: parseDate: filename = " + filename)
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
	#print("MVC: FileCache: parseDate: date = " + date)
	return date


def parseCutNo(filename):
	#print("MVC: FileCache: parseCutNo: filename: " + filename)
	cutno = ""
	if filename[-4:-3] == "_" and filename[-3:].isdigit():
		cutno = filename[-3:]
		filename = filename[:-4]
	#print("MVC: FileCache: parseCutNo: filename: " + filename + ", cutno: " + cutno)
	return cutno, filename


instance = None


class FileCache(Bookmarks, object):

	def __init__(self):
		self.sql_db_name = "/etc/enigma2/moviecockpit.db"
		first_load = not os.path.exists(self.sql_db_name)
		print("MVC-I: FileCache: __init__: first_load: %s" % first_load)
		self.sql_conn = sqlite.connect(self.sql_db_name)
		self.sql_conn.execute('''CREATE TABLE IF NOT EXISTS recordings (directory TEXT, filetype INTEGER, path TEXT, fileName TEXT, fileExt TEXT, name TEXT, date TEXT, length INTEGER,\
				description TEXT, extended_description TEXT, service_reference TEXT, size INTEGER, cuts TEXT, tags TEXT)''')
		self.sql_conn.text_factory = str
		self.cursor = self.sql_conn.cursor()
		self.filelist = [] # cache starts empty
		self.loaded_dirs = []
		self.bookmarks = self.getBookmarks()
		#print("MVC: FileCache: __init__: " + str(self.bookmarks))
		if first_load:
			#print("MVC: FileCache: __init__: sql_db does not exist")
			self.loadDatabaseDirs(self.bookmarks)
		else:
			#print("MVC: FileCache: __init__: sql_db exists")
			self.__loadCache(self.bookmarks)
		#print("MVC: FileCache: __init__: done")

	@staticmethod
	def getInstance():
		global instance
		if instance is None:
			instance = FileCache()
		return instance

	def newFileEntry(self, directory="", filetype="0", path="", filename="", ext="", name="", date=str(datetime.datetime.fromtimestamp(0)), length=0, description="", extended_description="", service_reference="", size=0, cuts="", tags=""):
		return (directory, filetype, path, filename, ext, name, date, length, description, extended_description, service_reference, size, cuts, tags)

	def reloadDatabase(self):
		#print("MVC: FileCache: reloadDatabase")
		self.clearDatabase()
		self.loadDatabaseDirs(self.bookmarks)

	def __loadCache(self, dirs):
		#print("MVC: FileCache: __loadCache: dirs: %s" % dirs)
		# check for dirs not loaded in self.list yet
		not_loaded_dirs = []
		#print("MVC: FileCache: __loadCache:     loaded_dirs: %s" % self.loaded_dirs)
		for adir in dirs:
			if adir not in self.loaded_dirs and os.path.basename(adir) != "..":
				not_loaded_dirs.append(adir)
		#print("MVC: FileCache: __loadCache: not_loaded_dirs: %s" % not_loaded_dirs)

		if not_loaded_dirs:
			# WHERE clause
			sql = "SELECT * FROM recordings WHERE "
			or_op = ""
			for directory in not_loaded_dirs:
				sql += or_op + "directory = \"" + directory + "\""
				or_op = " OR "
			#print("MVC: FileCache: __loadCache: " + sql)
			# do it
			self.cursor.execute(sql)
			filelist = self.cursor.fetchall()
			self.sql_conn.commit()
			#print("MVC: FileCache: __loadCache: len(filelist): " + str(len(filelist)))
			self.loaded_dirs += not_loaded_dirs
			#print("MVC: FileCache: __loadCache: loaded_dirs after merge: " + str(self.loaded_dirs))
			self.filelist += filelist
			#print("MVC: FileCache: __loadCache: len(self.filelist): " + str(len(self.filelist)))
#			self.dump(cache=True, detailed=False)
		else:
			#print("MVC: FileCache: __loadCache: all dirs are already loaded")
			pass

	def clearDatabase(self):
		#print("MVC: FileCache: clearDatabase")
		self.cursor.execute("DELETE FROM recordings")
		self.sql_conn.commit()
		self.filelist = []
		self.loaded_dirs = []

	def loadDatabaseFile(self, path):
		#print("MVC: FileCache: loadDatabaseFile: " + path)
		name, date, description, extended_description, service_reference, cuts, tags = "", "", "", "", "", "", ""
		size = 0
		length = 0
		filepath, ext = os.path.splitext(path)
		filename = os.path.basename(filepath)
		ext = ext.lower()
		if ext in extVideo:
			# Media file found
			date = None
			name = filename
			fdate = str2date(parseDate(os.path.basename(path)))
			#print("MVC: FileCache: loadDatabaseFile: file date: " + str(fdate))
			if fdate:
				date = str(fdate + datetime.timedelta(minutes=config.recording.margin_before.value))

			recording = getRecording(path, False)
			if recording:
				#print("MVC: FileCache: loadDatabaseFile: recording")
				timer_begin, timer_end, _service_reference = recording
				date = str(datetime.datetime.fromtimestamp(timer_begin))
				length = timer_end - timer_begin
				#print("MVC: FileCache: loadDatabaseFile: timer_begin: " + date)
				#print("MVC: FileCache: loadDatabaseFile: length:      " + str(length / 60))

			if not date:
				date = str(datetime.datetime.fromtimestamp(os.stat(path).st_ctime))[0:19]

			if ext in extTS:
				name_splits = name.split(" - ")
				if name_splits[2]:
					name = name_splits[2]
					cutno, _name = parseCutNo(name)
					if cutno:
						name = "%s (%s)" % (name, cutno)

			cuts = readCutsFile(path + ".cuts")

			if ext in extTS:
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
			else:
				length = ptsToSeconds(getCutListLength(unpackCutList(cuts)))

			if ext in extTS:
				meta = ParserMetaFile(path)
				if meta:
					service_reference = meta.getServiceReference()
					tags = meta.getTags()

			size = os.path.getsize(path)

			self.add((os.path.dirname(path), TYPE_ISFILE, path, filename, ext, name, date, length, description, extended_description, service_reference, size, cuts, tags))
		else:
			#print("MVC: FileCache: loadDatabaseFile: file ext not supported: " + ext)
			pass

	def updateDatabaseFile(self, path):
		#print("MVC: FileCache: updateDatabaseFile: path: %s" % path)
		self.delete(path)
		self.loadDatabaseFile(path)

	def addDatabaseFileType(self, path, file_type):
		#print("MVC: FileCache: addDatabaseFileType: path: %s, file_type: %s" % (path, file_type))
		if file_type == TYPE_ISFILE:
			self.loadDatabaseFile(path)
		elif file_type in [TYPE_ISDIR, TYPE_ISLINK]:
			ext, description, extended_description, service_reference, cuts, tags = "", "", "", "", "", ""
			size, length = 0, 0
			date = str(datetime.datetime.fromtimestamp(os.stat(path).st_ctime))[0:19]
			name = convertToUtf8(os.path.basename(path))
			self.add((os.path.dirname(path), file_type, path, os.path.basename(path), ext, name, date, length, description, extended_description, service_reference, size, cuts, tags))

	def loadDatabaseDir(self, movie_dir):
		#print("MVC: FileCache: loadDatabaseDir: movie_dir: %s" % movie_dir)
		try:
			walk_listdir = os.listdir(movie_dir)
		except IOError as e:
			print("MVC-E: FileCache: loadDatabaseDir: exception: %s" % e)
			return

		for walk_name in walk_listdir:
			path = os.path.join(movie_dir, walk_name)
			if os.path.isfile(path):
				self.addDatabaseFileType(path, TYPE_ISFILE)
			elif os.path.islink(path):
				self.addDatabaseFileType(path, TYPE_ISLINK)
				self.loadDatabaseDir(path)
			elif os.path.isdir(path):
				self.addDatabaseFileType(path, TYPE_ISDIR)
				self.loadDatabaseDir(path)
			else:
				#print("MVC: FileCache: loadDatabaseDir: file type not supported")
				pass

		self.addDatabaseFileType(os.path.join(movie_dir, ".."), TYPE_ISDIR)

		self.loaded_dirs.append(movie_dir)

	def getDirLoadList(self, movie_dir):
		#print("MVC: FileCache: getDirLoadList: movie_dir: %s" % movie_dir)
		try:
			walk_listdir = os.listdir(movie_dir)
		except IOError as e:
			print("MVC-E: FileCache: getDirLoadList: exception: %s" % e)
			return self.load_list

		for walk_name in walk_listdir:
			path = os.path.join(movie_dir, walk_name)
			if os.path.isfile(path):
				_filename, ext = os.path.splitext(path)
				if ext in extVideo:
					self.load_list.append((path, TYPE_ISFILE))
			elif os.path.islink(path):
				print("MVC: FileCache: loadDatabaseDir: link:" + path)
				self.load_list.append((path, TYPE_ISLINK))
				self.getDirLoadList(path)
			elif os.path.isdir(path):
				print("MVC: FileCache: loadDatabaseDir: dir:" + path)
				self.load_list.append((path, TYPE_ISDIR))
				self.getDirLoadList(path)

		self.load_list.append((os.path.join(movie_dir, ".."), TYPE_ISDIR))

		self.loaded_dirs.append(movie_dir)
		return self.load_list

	def getDirsLoadList(self, movie_dirs):
		print("MVC: FileCache: getDirsLoadList: movie_dirs: %s" % movie_dirs)
		self.load_list = []
		for movie_dir in movie_dirs:
			self.getDirLoadList(movie_dir)
		return self.load_list

	def loadDatabaseDirs(self, movie_dirs):
		#print("MVC: FileCache: loadDatabaseDirs: loading directories: " + str(movie_dirs))
		for movie_dir in movie_dirs:
			#print("MVC: FileCache: loadDatabaseDirs: walking: " + movie_dir)
			self.loadDatabaseDir(movie_dir)

	def __resolveVirtualDirs(self, dirs):
		#print("MVC: FileCache: __resolveVirtualDirs: dirs: %s" % dirs)
		more_dirs = []
		for adir in dirs:
			if adir in self.bookmarks:
				for bookmark in self.bookmarks:
					if bookmark not in more_dirs:
						more_dirs.append(bookmark)
			elif os.path.basename(adir) == "trashcan":
				for bookmark in self.bookmarks:
					trashcan_dir = bookmark + "/trashcan"
					if trashcan_dir not in more_dirs:
						more_dirs.append(trashcan_dir)
			else:
				if adir not in more_dirs:
					more_dirs.append(adir)

		#print("MVC: FileCache: __resolveVirtualDirs: more__dirs: %s" % more_dirs)
		return more_dirs

	def getFileList(self, dirs, include_dirs=False):
		#print("MVC: FileCache: getFileList:    get_dirs: %s" % dirs)
		#print("MVC: FileCache: getFileList: loaded_dirs: %s" % self.loaded_dirs)
		extMovie = extVideo - extBlu
		more_dirs = self.__resolveVirtualDirs(dirs)
		self.__loadCache(more_dirs)
		filelist = []
		for filedata in self.filelist:
			#print("MVC: FileCache: getFileList: dir: " + filedata[FILE_IDX_DIR] + ", filename: " + filedata[FILE_IDX_FILENAME] + ", ext: " + filedata[FILE_IDX_EXT])
			if (
				filedata[FILE_IDX_DIR] in more_dirs
				and filedata[FILE_IDX_TYPE] == TYPE_ISFILE
				and filedata[FILE_IDX_EXT] in extMovie
			) or (
				include_dirs
				and filedata[FILE_IDX_TYPE] > TYPE_ISFILE
				and filedata[FILE_IDX_DIR] in more_dirs
				and filedata[FILE_IDX_FILENAME] != ".."
				and filedata[FILE_IDX_FILENAME] != "trashcan"
				and filedata[FILE_IDX_PATH] not in more_dirs
			):
				filelist.append(filedata)
		return filelist

	def getDirList(self, dirs):
		#print("MVC: FileCache: getDirlist: " + str(dirs))
		more_dirs = self.__resolveVirtualDirs(dirs)
		self.__loadCache(more_dirs)

		subdirlist = []
		for filedata in self.filelist:
			if filedata[FILE_IDX_TYPE] > TYPE_ISFILE and filedata[FILE_IDX_FILENAME] != "trashcan" and filedata[FILE_IDX_FILENAME] != "..":
				subdirlist.append(filedata)
		return subdirlist

	def add(self, filedata):
		#print("MVC: FileCache: add: " + filedata[FILE_IDX_PATH])
		self.cursor.execute("INSERT INTO recordings VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", filedata)
		self.sql_conn.commit()
		# add to memory cache as well
		self.filelist.append(filedata)
#		self.dump(cache=True, detailed=True)

	def exists(self, path):
		filedata = self.getFile(path)
		directory, _filetype, _path, _filename, _ext, _name, _date, _length, _description, _extended_description, _service_reference, _size, _cuts, _tags = filedata
		return directory != ""

	def makeDir(self, path):
		if not self.exists(path):
			self.loadDatabaseDir(path)

	def deleteDir(self, _path):
		self.reloadDatabase()

	def delete(self, path):
		#print("MVC: FileCache: delete " + path)
		path = os.path.splitext(path)[0]
		filename = os.path.basename(path)
		directory = os.path.dirname(path)
		sql = 'DELETE FROM recordings WHERE directory=? AND filename=?'
		#print("MVC: FileCache: delete: sql = " + sql)
		self.cursor.execute(sql, (directory, filename))
		self.sql_conn.commit()

		# delete from memory cache as well
		filelist = []
		for filedata in self.filelist:
			if filedata[FILE_IDX_DIR] != directory or filedata[FILE_IDX_FILENAME] != filename:
				filelist.append(filedata)
		self.filelist = filelist
#		self.dump(cache = True, detailed=False)

	def update(self, path, pdirectory=None, pfiletype=None, ppath=None, pfilename=None, pext=None, pname=None, pdate=None, plength=None, pdescription=None, pextended_description=None, pservice_reference=None, psize=None, pcuts=None, ptags=None):
		#print("MVC: FileCache: update: " + path)
		filedata = self.getFile(path)
		directory, filetype, path, filename, ext, name, date, length, description, extended_description, service_reference, size, cuts, tags = filedata
		if path:
			if pdirectory is not None:
				directory = pdirectory
			if pfiletype is not None:
				filetype = pfiletype
			if ppath is not None:
				path = ppath
			if pfilename is not None:
				filename = pfilename
			if pext is not None:
				ext = pext
			if pname is not None:
				name = pname
			if pdate is not None:
				date = pdate
			if plength is not None:
				length = plength
			if pdescription is not None:
				description = pdescription
			if pextended_description is not None:
				extended_description = pextended_description
			if pservice_reference is not None:
				service_reference = pservice_reference
			if psize is not None:
				size = psize
			if pcuts is not None:
				cuts = pcuts
			if ptags is not None:
				tags = ptags

			self.delete(path)
			self.add((directory, filetype, path, filename, ext, name, date, length, description, extended_description, service_reference, size, cuts, tags))

	def updateSize(self, path, size):
		self.update(path, psize=size)

	def copyDir(self, _src_path, _dest_path):
		self.reloadDatabase()

	def copy(self, src_path, dest_path):
#		src_path = os.path.normpath(src_path)
		dest_path = os.path.normpath(dest_path)
		#print("MVC: FileCache: copy " + src_path + "|" + dest_path)
		source_dir = os.path.basename(src_path)
		self.__loadCache([source_dir])

		filedata = self.getFile(src_path)
		directory, filetype, path, filename, ext, name, date, length, description, extended_description, service_reference, size, cuts, tags = filedata
		if filename:
			path = os.path.join(dest_path, filename) + ext

			# check of file already exists at destination
			dest_file = self.getFile(path)
			if not dest_file[FILE_IDX_DIR]:
				#print("MVC: FileCache: copy: dest_path: " + path)
				directory = dest_path
				self.add((directory, filetype, path, filename, ext, name, date, length, description, extended_description, service_reference, size, cuts, tags))
			else:
				#print("MVC: FileCache: copy: file already exists at destination")
				pass
		else:
			#print("MVC: FileCache: copy: source file not found")
			pass

	def moveDir(self, _src_path, _dest_path):
		self.reloadDatabase()

	def move(self, src_path, dest_path):
		src_path = os.path.normpath(src_path)
		dest_path = os.path.normpath(dest_path)
		#print("MVC: FileCache: move " + src_path + "|" + dest_path)
		srcfile = self.getFile(src_path)
		directory, filetype, path, filename, ext, name, date, length, description, extended_description, service_reference, size, cuts, tags = srcfile
		if filename:
			path = os.path.join(dest_path, filename) + ext
			directory = dest_path
			# check if file already exists at destination
			dest_file = self.getFile(path)
			if not dest_file[FILE_IDX_PATH]:
				#print("MVC: FileCache: move: dest_path: " + path)
				self.add((directory, filetype, path, filename, ext, name, date, length, description, extended_description, service_reference, size, cuts, tags))
				self.delete(src_path)
			else:
				self.delete(src_path) # workaround
				print("MVC-E: FileCache: move: file already exists at destination: %s" % src_path)
		else:
			#print("MVC: FileCache: move: source file not found")
			pass
#		self.dump(cache=True, detailed=False)

	def getFile(self, path):
		path = os.path.splitext(path)[0]
		filename = os.path.basename(path)
		directory = os.path.dirname(path)
		#print("MVC: FileCache: getfile: " + directory + "|" + filename)
		#print("MVC: FileCache: getfile: loaded_dirs: " + str(self.loaded_dirs))

		self.__loadCache([directory])

		for filedata in self.filelist:
			#print("MVC: FileCache: getFile: |" + filedata[FILE_IDX_DIR] + "|" + directory + "|" + filedata[FILE_IDX_FILENAME] + "|" + filename + "|")
			if filedata[FILE_IDX_DIR] == directory and filedata[FILE_IDX_FILENAME] == filename:
				return filedata

		#print("MVC: FileCache: getFile: no file found")
		return self.newFileEntry()

	def dump(self, cache=True, detailed=False):
		if not cache:
			self.cursor.execute("SELECT * FROM recordings")
			rows = self.cursor.fetchall()
			print("MVC-I: FileCache: dump: =========== database dump ==============")
		else:
			rows = self.filelist
			print("MVC-I: FileCache: dump: =========== cache dump =================")

		for directory, filetype, path, filename, ext, name, date, length, description, extended_description, service_reference, size, cuts, tags in rows:
			print("MVC-I: FileCache: dump: media: %s|%s|%s|%s|%s" % (directory, filetype, path, filename, ext))
			if detailed:
				print("MVC-I: FileCache: dump: - name : %s" % name)
				print("MVC-I: FileCache: dump: - date : %s" % date)
				print("MVC-I: FileCache: dump: - len  : %s" % length)
				print("MVC-I: FileCache: dump: - desc : %s" % description)
				print("MVC-I: FileCache: dump: - ext  : %s" % extended_description)
				print("MVC-I: FileCache: dump: - sref : %s" % service_reference)
				print("MVC-I: FileCache: dump: - size : %s" % size)
				print("MVC-I: FileCache: dump: - cuts : %s" % unpackCutList(cuts))
				print("MVC-I: FileCache: dump: - tags : %s" % tags)

			if os.path.isfile(path):
				#print("MVC: FileCache: dump: file exists")
				pass
			elif os.path.isdir(path):
				#print("MVC: FileCache: dump: dir exists")
				pass
			elif os.path.islink(path):
				#print("MVC: FileCache: dump: link exists")
				pass
			else:
				#print("MVC: FileCache: dump: path does not exist: " + path)
				pass

		#print("MVC: FileCache: dump: number of files: " + str(len(rows)))

	def getCountSize(self, in_path):
		#print("MVC: FileCache: getCountSize: " + in_path)
		self.count = self.size = 0
		self.__getCountSize(in_path)
		#print("MVC: FileCache: getCountSize: %s, %s" % (self.count, self.size))
		return self.count, self.size

	def __getCountSize(self, in_path):
		#print("MVC: FileCache: __getCountSize: " + in_path)
		self.__loadCache([in_path])

		for directory, filetype, path, filename, _ext, _name, _date, _length, _description, _extended_description, _service_reference, size, _cuts, _tags in self.filelist:
			#print("MVC: FileCache: __getCountSize: %s, %s" % (path, filetype))
			if path and filetype == TYPE_ISFILE and directory == in_path:
				#print("MVC: FileCache: __getCountSize file: " + path)
				self.count += 1
				self.size += size
			if path and filetype > TYPE_ISFILE and directory.startswith(in_path) and filename != "..":
				self.__getCountSize(path)

		#print("MVC: FileCache: __getCountSize: %s, %s, %s" % (in_path, self.count, self.size))

	def close(self):
		#print("MVC: FileCache: close: closing database")
		self.sql_conn.commit()
		self.sql_conn.close()
