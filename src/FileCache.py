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
from CutListUtils import unpackCutList
from Bookmarks import Bookmarks
from FileCacheSQL import FileCacheSQL

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
FILE_TYPE_FILE = 1
FILE_TYPE_DIR = 2


instance = None


class FileCache(FileCacheSQL, Bookmarks, object):

	def __init__(self):
		print("MVC-I: FileCache: __init__")
		FileCacheSQL.__init__(self)
		#print("MVC: FileCache: __init__: done")

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

#		self.dump(detailed=True)

	### database row functions

	def exists(self, path):
		filedata = self.getFile(path)
		return filedata is not None

	def delete(self, path):
		#print("MVC: FileCache: delete %s" % path)
		where = "path = \"" + path + "\""
		self.sqlDelete(where)

#		self.dump(detailed=False)

	def update(self, path, pdirectory=None, pfiletype=None, ppath=None, pfilename=None, pext=None, pname=None, pdate=None, plength=None, pdescription=None, pextended_description=None, pservice_reference=None, psize=None, pcuts=None, ptags=None):
		#print("MVC: FileCache: update: %s" % path)
		filedata = self.getFile(path)
		if filedata is not None:
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

	def copy(self, src_path, dest_path):
		src_path = os.path.normpath(src_path)
		dest_path = os.path.normpath(dest_path)
		#print("MVC: FileCache: copy: src_path: %s, dest_path: %s " % (src_path, dest_path))
		filedata = self.getFile(src_path)
		if filedata is not None:
			directory, filetype, path, filename, ext, name, date, length, description, extended_description, service_reference, size, cuts, tags = filedata
			path = os.path.join(dest_path, filename) + ext
			# check of file already exists at destination
			dest_file = self.getFile(path)
			if dest_file is None:
				#print("MVC: FileCache: copy: dest_path: %s" % path)
				directory = dest_path
				self.add((directory, filetype, path, filename, ext, name, date, length, description, extended_description, service_reference, size, cuts, tags))
			else:
				#print("MVC: FileCache: copy: file already exists at destination")
				pass
		else:
			#print("MVC: FileCache: copy: source file not found")
			pass

	def move(self, src_path, dest_path):
		src_path = os.path.normpath(src_path)
		dest_path = os.path.normpath(dest_path)
		#print("MVC: FileCache: move: src_path: %s, dest_path: %s" % (src_path, dest_path))
		srcfile = self.getFile(src_path)
		if srcfile is not None:
			directory, filetype, path, filename, ext, name, date, length, description, extended_description, service_reference, size, cuts, tags = srcfile
			path = os.path.join(dest_path, filename) + ext
			directory = dest_path
			# check if file already exists at destination
			dest_file = self.getFile(path)
			if dest_file is None:
				#print("MVC: FileCache: move: dest_path: %s" % path)
				self.add((directory, filetype, path, filename, ext, name, date, length, description, extended_description, service_reference, size, cuts, tags))
				self.delete(src_path)
			else:
				self.delete(src_path) # workaround
				print("MVC-E: FileCache: move: source file already exists at destination: %s" % src_path)
		else:
			print("MVC-E: FileCache: move: source file not found: src_path: %s" % src_path)
#		self.dump(detailed=False)

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
		bookmarks = self.getBookmarks()
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
			where = ""
			op = ""
			for directory in all_dirs:
				where += op + "path != \"" + directory + "\""
				op = " AND "
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

		for directory, filetype, path, filename, _ext, _name, _date, _length, _description, _extended_description, _service_reference, size, _cuts, _tags in filelist:
			#print("MVC: FileCache: __getCountSize: %s, %s" % (path, filetype))
			if path and filetype == FILE_TYPE_FILE and directory == in_path:
				#print("MVC: FileCache: __getCountSize: path: %s " % path)
				self.count += 1
				self.size += size
			if path and filetype > FILE_TYPE_FILE and directory.startswith(in_path) and filename != "..":
				self.__getCountSize(path)

		#print("MVC: FileCache: __getCountSize: %s, %s, %s" % (in_path, self.count, self.size))

	def dump(self, detailed=False):
		self.cursor.execute("SELECT * FROM recordings")
		rows = self.cursor.fetchall()
		print("MVC-I: FileCache: dump: =========== database dump ==============")

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
				#print("MVC: FileCache: dump: path does not exist: %s" % path)
				pass

		#print("MVC: FileCache: dump: number of files: %s" % len(rows))
