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
from RecordingUtils import isRecording, adjustTimerPathAfterMove
from Tasker import tasker
from MountPoints import MountPoints
from FileCache import FileCache, TYPE_ISFILE, TYPE_ISDIR, TYPE_ISLINK

FILE_OP_DELETE = 1
FILE_OP_MOVE = 2
FILE_OP_COPY = 3

class FileOps(MovieTMDB, MovieCover, MountPoints, object):

	def execFileOp(self, op, path, target_path, file_type, execFileOpCallback=None):
		cmd = []
		association = []
		print("MVC-I: FileOps: execFileOp: op: %s, path: %s, target_path: %s, file_type: %s" % (op, path, target_path, file_type))
		if op == FILE_OP_DELETE:
			c = self.__execFileDelete(path, file_type)
			cmd.append(c)
			association.append((self.__deleteCallback, path, target_path, file_type))
		elif op == FILE_OP_MOVE:
			free = 0
			used = 0
			if file_type != TYPE_ISFILE:
				_count, used = FileCache.getInstance().getCountSize(path)
				free = self.getMountPointSpaceFree(target_path)
				#print("MVC: FileOps: execFileOp: move_dir: used: %s, free: %s" % (used, free))
			if free >= used:
				c = self.__execFileMove(path, target_path, file_type)
				cmd.append(c)
				association.append((self.__moveCallback, path, target_path, file_type))
			else:
				print("MVC-I: FileOps: execFileOp: move_dir: not enough space left: size: %s, free: %s" % (used, free))
		elif op == FILE_OP_COPY:
			if os.path.dirname(path) != target_path:
				c = self.__execFileCopy(path, target_path, file_type)
				cmd.append(c)
				association.append((self.__copyCallback, path, target_path, file_type))
		if cmd:
			#print("MVC: FileOps: execFileOp: cmd: %s" % cmd)
			if execFileOpCallback:
				association.append((execFileOpCallback, op, path, target_path, file_type))
			# Sync = True: Run script for one file do association and continue with next file
			tasker.shellExecute(cmd, association, True)

	def __deleteCallback(self, path, target_path, file_type):
		print("MVC-I: MovieSelection: __deleteCallback: path: %s, target_path: %s, file_type: %s" % (path, target_path, file_type))
		if file_type == TYPE_ISFILE:
			FileCache.getInstance().delete(path)
		if file_type == TYPE_ISDIR:
			FileCache.getInstance().deleteDir(path)

	def __moveCallback(self, path, target_path, file_type):
		print("MVC-I: FileOps: __moveCallback: path: %s, target_path: %s, file_type: %s" % (path, target_path, file_type))
		if file_type == TYPE_ISFILE:
			FileCache.getInstance().move(path, target_path)
			# check if moved a file that is currently being recorded and fix path
			if isRecording(path):
				adjustTimerPathAfterMove(path, os.path.join(target_path, os.path.basename(path)))
		if file_type == TYPE_ISDIR:
			FileCache.getInstance().moveDir(path, target_path)

	def __copyCallback(self, path, target_path, file_type):
		print("MVC-I: FileOps: __copyCallback: path: %s, target_path: %s, file_type: %s" % (path, target_path, file_type))
		if file_type == TYPE_ISFILE:
			FileCache.getInstance().copy(path, target_path)
		if file_type == TYPE_ISDIR:
			FileCache.getInstance().copyDir(path, target_path)

	def __execFileDelete(self, path, file_type):
		print("MVC-I: FileOps: __execFileDelete: path: %s, file_type: %s" % (path, file_type))
		c = []
		if file_type == TYPE_ISFILE:
			c.append('rm -f "' + self.getCoverPath(path) + '"')
			c.append('rm -f "' + self.getInfoPath(path) + '"')
			path, _ext = os.path.splitext(path)
			c.append('rm -f "' + path + '."*')
		elif file_type == TYPE_ISDIR:
			c.append('rm -rf "' + path + '"')
		elif file_type == TYPE_ISLINK:
			c.append('rm -f "' + path + '"')
		#print("MVC: FileOps: __execFileDelete: c: %s" % c)
		return c

	def __execFileMove(self, path, target_path, file_type):
		print("MVC-I: FileOps: __execFileMove: path: %s, target_path: %s, file_type: %s" % (path, target_path, file_type))
		c = self.__changeFileOwner(path, target_path)
		if file_type == TYPE_ISFILE:
			#print("MVC: FileOps: __execFileMove: %s, %s" % (self.getCoverPath(path), os.path.splitext(self.getCoverPath(target_path))[0]))
			c.append('mv "' + self.getCoverPath(path) + '" "' + os.path.splitext(self.getCoverPath(target_path))[0] + '/"')
			c.append('mv "' + self.getInfoPath(path) + '" "' + os.path.splitext(self.getInfoPath(target_path))[0] + '/"')
			path, _ext = os.path.splitext(path)
			if os.path.basename(target_path) == "trashcan":
				c.append('touch "' + path + '."*')
			c.append('mv "' + path + '."* "' + target_path + '/"')
		elif file_type == TYPE_ISDIR:
			if os.path.basename(target_path) == "trashcan":
				c.append('touch "' + path + '"')
			c.append('mv "' + path + '" "' + target_path + '"')
		elif file_type == TYPE_ISLINK:
			if os.path.basename(target_path) == "trashcan":
				c.append('touch "' + path + '"')
			c.append('mv "' + path + '" "' + target_path + '"')
		#print("MVC: FileOps: __execFileMove: c: %s" % c)
		return c

	def __execFileCopy(self, path, target_path, file_type):
		print("MVC-I: FileOps: __execFileCopy: path: %s, target_path: %s, file_type: %s" % (path, target_path, file_type))
		c = self.__changeFileOwner(path, target_path)
		if file_type == TYPE_ISFILE:
			path, _ext = os.path.splitext(path)
			c.append('cp "' + path + '."* "' + target_path + '/"')
		elif file_type == TYPE_ISDIR:
			c.append('cp -ar "' + path + '" "' + target_path + '"')
		elif file_type == TYPE_ISLINK:
			c.append('cp -ar "' + path + '" "' + target_path + '"')
		#print("MVC: FileOps: __execFileCopy: c: %s" % c)
		return c

	def __changeFileOwner(self, path, target_path):
		c = []
		if self.isMountPoint(target_path) != self.isMountPoint(path):
			# need to change file ownership to match target filesystem file creation
			tfile = "\"" + target_path + "/owner_test" + "\""
			path = path.replace("'", "\'")
			sfile = "\"" + path + ".\"*"
			c.append("touch %s;ls -l %s | while read flags i owner group crap;do chown $owner:$group %s;done;rm %s" % (tfile, tfile, sfile, tfile))
		return c
