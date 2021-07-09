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
from __init__ import _
from Plugins.SystemPlugins.CacheCockpit.FileCache import FileCache
from FileProgress import FileProgress
from Plugins.SystemPlugins.CacheCockpit.FileCacheSQL import FILE_IDX_FILENAME, FILE_IDX_PATH, FILE_IDX_NAME
from MovieCoverDownload import MovieCoverDownload
from DelayTimer import DelayTimer
from MovieListUtils import createFileList


class MovieCoverDownloadProgress(MovieCoverDownload, FileProgress):

	def __init__(self, session):
		logger.debug("...")
		FileProgress.__init__(self, session)
		MovieCoverDownload.__init__(self)
		self.covers_tried = 0
		self.covers_found = 0
		self.skinName = "FileCacheLoadProgress"
		self.setTitle(_("Download covers") + " ...")
		self.execution_list = []
		self.onShow.append(self.onDialogShow)

	def onDialogShow(self):
		logger.debug("...")
		DelayTimer(10, self.execMovieCoverDownloadProgress)

	def doFileOp(self, afile):
		file_name = afile[FILE_IDX_FILENAME]
		path = afile[FILE_IDX_PATH]
		name = afile[FILE_IDX_NAME]
		self.file_name = file_name
		self.status = _("Please wait") + " ..."
		self.updateProgress()
		cover_tried, cover_found = self.getCover(path, name)
		self.covers_tried += cover_tried
		self.covers_found += cover_found
		DelayTimer(10, self.nextFileOp)

	def completionStatus(self):
		covers_percent = 0 if self.covers_tried == 0 else float(float(self.covers_found) / float(self.covers_tried)) * 100
		logger.debug("%s of %s new covers: %.2f%%", self.covers_found, self.covers_tried, covers_percent)
		return (_("Done") + " : %s " + _("of") + " %s " + _("new covers") + " (%.2f%%)") % (self.covers_found, self.covers_tried, covers_percent)

	def execMovieCoverDownloadProgress(self):
		logger.info("...")
		self.status = _("Initializing") + " ..."
		self.updateProgress()
		self.execution_list = createFileList(FileCache.getInstance().getHomeDir())
		self.total_files = len(self.execution_list)
		DelayTimer(10, self.nextFileOp)
