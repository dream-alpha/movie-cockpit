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
from MovieCover import MovieCover
from MovieTMDB import MovieTMDB
from Tasker import tasker
from MountPoints import MountPoints
from FileCache import FileCache, FILE_TYPE_FILE, FILE_TYPE_DIR
from FileCacheLoad import FileCacheLoad

FILE_OP_DELETE = 1
FILE_OP_MOVE = 2
FILE_OP_COPY = 3

class FileOps(MovieTMDB, MovieCover, MountPoints, object):

	def execFileOp(self, op, path, target_path, filetype):
		cmd = []
		association = []
		print("MVC-I: FileOps: execFileOp: op: %s, path: %s, target_path: %s, filetype: %s" % (op, path, target_path, filetype))
		if op == FILE_OP_DELETE:
			c = self.__execFileDelete(path, filetype)
			cmd.append(c)
			association.append((self.__deleteCallback, path, target_path, filetype))
		elif op == FILE_OP_MOVE:
			free = 0
			used = 0
			if filetype != FILE_TYPE_FILE:
				_count, used = FileCache.getInstance().getCountSize(path)
				free = self.getMountPointSpaceFree(target_path)
				#print("MVC: FileOps: execFileOp: move_dir: used: %s, free: %s" % (used, free))
			if free >= used:
				c = self.__execFileMove(path, target_path, filetype)
				cmd.append(c)
				association.append((self.__moveCallback, path, target_path, filetype))
			else:
				print("MVC-I: FileOps: execFileOp: move_dir: not enough space left: size: %s, free: %s" % (used, free))
		elif op == FILE_OP_COPY:
			if os.path.dirname(path) != target_path:
				c = self.__execFileCopy(path, target_path, filetype)
				cmd.append(c)
				association.append((self.__copyCallback, path, target_path, filetype))
		if cmd:
			#print("MVC: FileOps: execFileOp: cmd: %s" % cmd)
			association.append((self.execFileOpCallback, op, path, target_path, filetype))
			# Sync = True: Run script for one file do association and continue with next file
			tasker.shellExecute(cmd, association, True)

	def execFileOpCallback(self, op, path, _target_path, _filetype):
		print("MVC-I: FileOps: execFileOpCallback: op: %s, path: %s" % (op, path))
		return

	def __deleteCallback(self, path, target_path, filetype):
		print("MVC-I: MovieSelection: __deleteCallback: path: %s, target_path: %s, filetype: %s" % (path, target_path, filetype))
		if filetype == FILE_TYPE_FILE:
			FileCache.getInstance().delete(path)
		if filetype == FILE_TYPE_DIR:
			FileCacheLoad.getInstance().deleteDir(path)

	def __moveCallback(self, path, target_path, filetype):
		print("MVC-I: FileOps: __moveCallback: path: %s, target_path: %s, filetype: %s" % (path, target_path, filetype))
		if filetype == FILE_TYPE_FILE:
			FileCache.getInstance().move(path, target_path)
		if filetype == FILE_TYPE_DIR:
			FileCacheLoad.getInstance().moveDir(path, target_path)

	def __copyCallback(self, path, target_path, filetype):
		print("MVC-I: FileOps: __copyCallback: path: %s, target_path: %s, filetype: %s" % (path, target_path, filetype))
		if filetype == FILE_TYPE_FILE:
			FileCache.getInstance().copy(path, target_path)
		if filetype == FILE_TYPE_DIR:
			FileCacheLoad.getInstance().copyDir(path, target_path)

	def __execFileDelete(self, path, filetype):
		print("MVC-I: FileOps: __execFileDelete: path: %s, filetype: %s" % (path, filetype))
		c = []
		if filetype == FILE_TYPE_FILE:
			c.append('rm -f "' + self.getCoverPath(path) + '"')
			c.append('rm -f "' + self.getInfoPath(path) + '"')
			path, _ext = os.path.splitext(path)
			c.append('rm -f "' + path + '."*')
		elif filetype == FILE_TYPE_DIR:
			c.append('rm -rf "' + path + '"')
		#print("MVC: FileOps: __execFileDelete: c: %s" % c)
		return c

	def __execFileMove(self, path, target_path, filetype):
		print("MVC-I: FileOps: __execFileMove: path: %s, target_path: %s, filetype: %s" % (path, target_path, filetype))
		c = self.__changeFileOwner(path, target_path)
		if filetype == FILE_TYPE_FILE:
			#print("MVC: FileOps: __execFileMove: %s, %s" % (self.getCoverPath(path), os.path.splitext(self.getCoverPath(target_path))[0]))
			c.append('mv "' + self.getCoverPath(path) + '" "' + os.path.splitext(self.getCoverPath(target_path))[0] + '/"')
			c.append('mv "' + self.getInfoPath(path) + '" "' + os.path.splitext(self.getInfoPath(target_path))[0] + '/"')
			path, _ext = os.path.splitext(path)
			if os.path.basename(target_path) == "trashcan":
				c.append('touch "' + path + '."*')
			c.append('mv "' + path + '."* "' + target_path + '/"')
		elif filetype == FILE_TYPE_DIR:
			if os.path.basename(target_path) == "trashcan":
				c.append('touch "' + path + '"')
			c.append('mv "' + path + '" "' + target_path + '"')
		#print("MVC: FileOps: __execFileMove: c: %s" % c)
		return c

	def __execFileCopy(self, path, target_path, filetype):
		print("MVC-I: FileOps: __execFileCopy: path: %s, target_path: %s, filetype: %s" % (path, target_path, filetype))
		c = self.__changeFileOwner(path, target_path)
		if filetype == FILE_TYPE_FILE:
			path, _ext = os.path.splitext(path)
			c.append('cp "' + path + '."* "' + target_path + '/"')
		elif filetype == FILE_TYPE_DIR:
			c.append('cp -ar "' + path + '" "' + target_path + '"')
		#print("MVC: FileOps: __execFileCopy: c: %s" % c)
		return c

	def __changeFileOwner(self, path, target_path):
		c = []
		if self.getMountPoint(target_path) != self.getMountPoint(path):
			# need to change file ownership to match target filesystem file creation
			tfile = "\"" + target_path + "/owner_test" + "\""
			path = path.replace("'", "\'")
			sfile = "\"" + path + ".\"*"
			c.append("touch %s;ls -l %s | while read flags i owner group crap;do chown $owner:$group %s;done;rm %s" % (tfile, tfile, sfile, tfile))
		return c
