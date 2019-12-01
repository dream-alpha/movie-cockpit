#!/usr/bin/python
# coding=utf-8
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
from __init__ import _
from Components.config import config
from Components.Label import Label
from Components.Pixmap import Pixmap
from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen
from Screens.MessageBox import MessageBox
from enigma import eTimer, eSize
from ServiceReference import ServiceReference
from Screens.TimerEdit import TimerEditList
from Screens.LocationBox import LocationBox
from Tools.BoundFunction import boundFunction
from enigma import getDesktop
from Components.Sources.MVCServiceEvent import MVCServiceEvent
from ServiceCenter import ServiceCenter
from MovieSelectionContextMenu import MovieSelectionContextMenu
from RecordingUtils import isRecording, stopRecording
from CutList import CutList
from FileOps import FileOps, FILE_OP_DELETE, FILE_OP_MOVE, FILE_OP_COPY
from FileCache import FILE_IDX_PATH, FILE_IDX_TYPE, FILE_IDX_EXT, FILE_IDX_NAME, FILE_TYPE_DIR
from FileOpsProgress import FileOpsProgress
from FileCacheLoadProgress import FileCacheLoadProgress
from ServiceUtils import extVideo
from ConfigInit import sort_modes
from MovieInfoEPG import MovieInfoEPG
from MovieInfoTMDB import MovieInfoTMDB
from MediaCenter import MediaCenter
from MovieList import MovieList
from MovieSelectionContextMenu import MENU_FUNCTIONS, MENU_PLUGINS
from FileListUtils import FileListUtils
from ConfigScreen import ConfigScreen
from StylesScreen import StylesScreen
from MovieSelectionKeyFunctions import KeyFunctions

instance = None


class MovieSelectionSummary(Screen):

	def __init__(self, session, parent):
		print("MVC-I: MovieSelectionSummary: MovieSelectionSummary: __init__")
		Screen.__init__(self, session, parent)
		self.skinName = ["MVCSelectionSummary"]


class MovieSelection(Screen, HelpableScreen, KeyFunctions, FileListUtils, FileOps, CutList):

	# define static member variables
	def attrgetter(self, default=None):
		attr = self

		def get_any(_self):
			return getattr(MovieSelection, attr, default)
		return get_any

	def attrsetter(self):
		attr = self

		def set_any(_self, value):
			setattr(MovieSelection, attr, value)
		return set_any

	color_buttons_level = property(fget=attrgetter('_color_buttons_level', 0), fset=attrsetter('_color_buttons_level'))
	return_path = property(fget=attrgetter('_return_path', None), fset=attrsetter('_return_path'))
	current_sort_mode = property(fget=attrgetter('_current_sort_mode', None), fset=attrsetter('_current_sort_mode'))

	@staticmethod
	def getInstance():
		return instance

	def __init__(self, session, *__):
		print("MVC-I: MovieSelection: __init__: self.return_path: %s" % self.return_path)
		global instance
		instance = self

		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		KeyFunctions.__init__(self)
		FileOps.__init__(self)
		FileListUtils.__init__(self)
		CutList.__init__(self)

		self["actions"] = self.initActions(self)
		self["actions"].csel = self
		self.filelist = []
		self["mini_tv"] = Pixmap()
		self.enable_mini_tv = False
		self.skinName = self.getSkinName()
		self["Service"] = MVCServiceEvent(ServiceCenter.getInstance())
		self["list"] = MovieList()
		self.cursor_direction = 0
		self.lastservice = None
		self["no_support"] = Label(_("Skin resolution other than Full HD is not supported yet"))
		self["space_info"] = Label()
		self["sort_mode"] = Label()
		if self.current_sort_mode is None:
			self.current_sort_mode = config.plugins.moviecockpit.list_sort.value
		self.short_key = True  # used for long / short key press detection
		self.delayTimer = eTimer()
		self.delayTimer_conn = self.delayTimer.timeout.connect(self.updateInfoDelayed)

		self.onShow.append(self.onDialogShow)
		self.onHide.append(self.onDialogHide)
		self["list"].onSelectionChanged.append(self.selectionChanged)

	def onDialogShow(self):
		print("MVC-I: MovieSelection: onDialogShow: self.return_path: %s" % self.return_path)
		#print("MVC: MovieSelection: onDialogShow: self[\"mini_tv\"].instance: " + str(self["mini_tv"].instance.size().width()))
		self.enable_mini_tv = self["mini_tv"].instance.size().width() > -1
		self.lastservice = self.session.nav.getCurrentlyPlayingServiceReference()
		print("MVC-I: MovieSelection: onDialogShow: self.lastservice: %s" % (self.lastservice.toString() if self.lastservice else None))

		if not self.filelist:
			current_dir = self.getHomeDir()
			if not config.plugins.moviecockpit.list_start_home.value and self.return_path:
				current_dir = os.path.dirname(self.return_path)
			self.loadList(current_dir)
		elif self.return_path:
			self.moveToPath(self.return_path)

	def onDialogHide(self):
		print("MVC-I: MovieSelection: onDialogHide: self.return_path: %s" % self.return_path)
		if self.enable_mini_tv:
			self.pigWorkaround()
			self.session.nav.playService(self.lastservice)

	def callHelpAction(self, *args):
		HelpableScreen.callHelpAction(self, *args)

	def pigWorkaround(self):
		self.session.nav.stopService()
		desktop_size = getDesktop(0).size()
		self.instance.resize(eSize(*(desktop_size.width(), desktop_size.height())))

	def getSkinName(self):
		width = getDesktop(0).size().width()
		if width == 1920:
			skinName = "MVCSelection"
		else:
			skinName = "MVCNoSupport"
			self.setTitle(_("Information"))
		return skinName

	def createSummary(self):
		return MovieSelectionSummary

	def exit(self):
		print("MVC-I: MovieSelection: exit")
		self.delayTimer.stop()
		self.close()

### cursor movements

	def bqtPlus(self):
		if config.plugins.moviecockpit.list_bouquet_keys.value == "":
			self.moveTop()
		elif config.plugins.moviecockpit.list_bouquet_keys.value == "Skip":
			self.moveSkipUp()
		elif config.plugins.moviecockpit.list_bouquet_keys.value == "Folder":
			self.bqtNextFolder()

	def bqtMinus(self):
		if config.plugins.moviecockpit.list_bouquet_keys.value == "":
			self.moveEnd()
		elif config.plugins.moviecockpit.list_bouquet_keys.value == "Skip":
			self.moveSkipDown()
		elif config.plugins.moviecockpit.list_bouquet_keys.value == "Folder":
			self.bqtPrevFolder()

	def bqtNextFolder(self):
		dirlist = self.getDirList()
		if dirlist:
			pos = dirlist[FILE_IDX_PATH].index(self["list"].getCurrentDir()) % len(dirlist)
			pos = pos + 1 if pos < len(dirlist) - 1 else 0
			self.changeDir(dirlist[pos])

	def bqtPrevFolder(self):
		dirlist = self.getDirList()
		if dirlist:
			pos = dirlist[FILE_IDX_PATH].index(self["list"].getCurrentDir()) % len(dirlist)
			pos = pos - 1 if pos > 0 else len(dirlist) - 1
			self.changeDir(dirlist[pos])

	def moveUp(self):
		self.cursor_direction = -1
		self.return_path = self["list"].moveUp()

	def moveDown(self):
		self.cursor_direction = 1
		self.return_path = self["list"].moveDown()

	def pageUp(self):
		self.cursor_direction = 0
		self.return_path = self["list"].pageUp()

	def pageDown(self):
		self.cursor_direction = 0
		self.return_path = self["list"].pageDown()

	def moveTop(self):
		self.return_path = self["list"].moveTop()

	def moveSkipUp(self):
		self.cursor_direction = -1
		for _i in range(int(config.plugins.moviecockpit.list_skip_size.value)):
			self.return_path = self["list"].moveUp()

	def moveSkipDown(self):
		self.cursor_direction = 1
		for _i in range(int(config.plugins.moviecockpit.list_skip_size.value)):
			self.return_path = self["list"].moveDown()

	def moveEnd(self):
		self.return_path = self["list"].moveEnd()

	def moveToPath(self, path):
		index = self.getIndex4Path(self.filelist, path)
		self.return_path = self["list"].moveToIndex(index)

	def moveToMovieHome(self):
		self.changeDir(self.getHomeDir())
		self.resetColorButtonsLevel()

### key functions

	def openTimerList(self):
		self.session.open(TimerEditList)

	def toggleDateMount(self):
		config.plugins.moviecockpit.movie_mountpoints.value = not config.plugins.moviecockpit.movie_mountpoints.value
		config.plugins.moviecockpit.movie_mountpoints.save()
		self["list"].invalidateList()

	def showMovieInfoEPG(self):
		if not self.short_key:
			self.short_key = True
		else:
			path = self["list"].getCurrentPath()
			#print("MVC: MovieSelection: showMovieInfoEPG: path: %s" % path)
			epg_available = False
			if path and self["list"].getCurrentSelection()[FILE_IDX_EXT] in extVideo:
				service = self.getService4Path(self.filelist, path)
				if service:
					event = ServiceCenter.getInstance().info(service).getEvent()
					if event:
						epg_available = True
						self.session.open(MovieInfoEPG, event, ServiceReference(service))
			if not epg_available:
				self.session.open(
					MessageBox,
					_("No EPG info available"),
					MessageBox.TYPE_INFO
				)

	def showMovieInfoTMDB(self):
		self.short_key = False
		path = self["list"].getCurrentPath()
		entry = self.getEntry4Path(self.filelist, path)
		if entry and entry[FILE_IDX_EXT] in extVideo:
			name = entry[FILE_IDX_NAME]
			self.session.openWithCallback(self.showMovieInfoTMDBCallback, MovieInfoTMDB, path, name)

	def showMovieInfoTMDBCallback(self):
		self.updateInfo()

	def changeDir(self, path):
		#print("MVC: MovieSelection: changeDir: path: %s" % path)
		if path:
			target_dir = path
			if os.path.basename(path) == "..":
				# open parent folder
				target_dir = os.path.abspath(path)
			self.loadList(target_dir)
			self.moveTop()

	def openBookmarks(self):
		self.selectDirectory(
			self.openBookmarksCallback,
			_("Bookmarks") + ":"
		)

	def openBookmarksCallback(self, path):
		if path:
			self.changeDir(os.path.normpath(path))

	def videoFuncShort(self):
		if not self.short_key:
			self.short_key = True
		else:
			self.toggleSelection()

	def videoFuncLong(self):
		self.short_key = False
		self.unselectAll()

	def updateInfo(self):
		#print("MVC: MovieSelection: updateInfo")
		self.resetInfo()
		self.updateTitle()
		self.updateSortModeDisplay()
		self.updateSpaceInfoDisplay()
		self.delayTimer.start(int(config.plugins.moviecockpit.movie_description_delay.value), True)

	def updateInfoDelayed(self):
		#print("MVC: MovieSelection: updateInfoDelayed")
		path = self["list"].getCurrentPath()
		if path:
			current_service = self.getService4Path(self.filelist, path)
			self["Service"].newService(current_service)

	def resetInfo(self):
		#print("MVC: MovieSelection: resetInfo")
		self.delayTimer.stop()
		self["Service"].newService(None)

	def updateSpaceInfoDisplay(self):
		self["space_info"].setText(config.plugins.moviecockpit.disk_space_info.value)

	def updateTitle(self):
		title = "MovieCockpit"
		current_dir = self["list"].getCurrentDir()
		if current_dir:
			title += " - "
			title += _("trashcan") if os.path.basename(current_dir) == "trashcan" else _("Recordings")
		self.setTitle(title)

	### sorting

	def updateSortModeDisplay(self):
		self["sort_mode"].setText(_("Sort mode") + ": " + sort_modes[self.current_sort_mode][1])

	def updateSortMode(self):
		self.return_path = self["list"].getCurrentPath()
		self.loadList(self["list"].getCurrentDir())
		self.updateInfo()

	def toggleSortMode(self):
		self.current_sort_mode = str((int(self.current_sort_mode) + 1) % len(sort_modes))
		self.updateSortMode()

	def toggleSortOrder(self):
		mode, order = sort_modes[self.current_sort_mode][0]
		order = not order
		for sort_mode in sort_modes:
			if sort_modes[sort_mode][0] == (mode, order):
				self.current_sort_mode = sort_mode
				break
		self.updateSortMode()

### progress functions

	def resetProgress(self):
		self.return_path = self["list"].getCurrentPath()
		selection_list = self.getSelectionList()
		for path in selection_list:
			self.resetLastCutList(path)
		self.loadList(self["list"].getCurrentDir())

### list functions

	def reloadList(self, path):
		#print("MVC: MovieSelection: loadListRecording: path: %s" % path)
		#print("MVC: MovieSelection: loadedDirs: " + str(self.loadedDirs(self.filelist)))
		if path in self.loadedDirs(self.filelist):
			self.loadList(path)

	def loadList(self, path):
		#print("MVC: MovieSelection: loadList: path: %s" % path)
		#print("MVC: MovieSelection: loadList start: self.return_path: %s" % self.return_path)
		self.resetInfo()
		MovieList.selection_list = []
		filelist = self.createFileList(path)
		if config.plugins.moviecockpit.directories_show.value:
			filelist += self.createDirList(path)
		custom_list = self.createCustomList(path)
		self.filelist = custom_list + self.sortList(filelist, self.current_sort_mode)
		self["list"].setList(self.filelist)
		if self.return_path:
			self.moveToPath(self.return_path)
		else:
			self.moveTop()

### selection functions

	def getSelectionList(self):
		if not MovieList.selection_list:
			# if no selections were made, add the current cursor position
			path = self["list"].getCurrentPath()
			if path:
				MovieList.selection_list.append(path)
		return MovieList.selection_list

	def selectPath(self, path):
		#print("MVC: MovieSelection: selectPath: path: %s" % path)
		if path not in MovieList.selection_list:
			MovieList.selection_list.append(path)
			index = self.getIndex4Path(self.filelist, path)
			self["list"].invalidateEntry(index)

	def unselectPath(self, path):
		#print("MVC: MovieSelection: unselectPath: path: %s" % path)
		if path in MovieList.selection_list:
			MovieList.selection_list.remove(path)
			index = self.getIndex4Path(self.filelist, path)
			self["list"].invalidateEntry(index)

	def selectAll(self):
		#print("MVC: MovieSelection: selectAll")
		for entry in self.filelist:
			self.selectPath(entry[FILE_IDX_PATH])

	def unselectAll(self):
		#print("MVC: MovieSelection: unselectAll")
		MovieList.selection_list = []
		self["list"].invalidateList()

	def selectionChanged(self):
		#print("MVC: MovieSelection: selectionChanged")
		self.updateInfo()

	def toggleSelection(self):
		#print("MVC: MovieSelection: toggleSelection")
		path = self["list"].getCurrentPath()
		#print("MVC: MovieSelection: toggleSelection: path: %s" % path)
		#print("MVC: MovieSelection: toggleSelection: selection_list: %s" % MovieList.selection_list)
		if path in MovieList.selection_list:
			self.unselectPath(path)
		else:
			self.selectPath(path)

		# Move cursor
		if config.plugins.moviecockpit.list_selmove.value != "o":
			if self.cursor_direction == -1 and config.plugins.moviecockpit.list_selmove.value == "b":
				self.moveUp()
			else:
				self.moveDown()

	def entrySelected(self):
		path = self["list"].getCurrentPath()
		if path:
			if self["list"].getCurrentSelection()[FILE_IDX_TYPE] == FILE_TYPE_DIR:
				self.changeDir(path)
			else:
				if self.enable_mini_tv:
					self.pigWorkaround()

				self.openPlayer(path)

### player

	def playerCallback(self, reload_selection):
		print("MVC-I: MovieSelection: playerCallback: reload_selection: %s" % reload_selection)
		if not reload_selection:
			self.exit()
		else:
			self.return_path = self["list"].getCurrentPath()
			print("MVC-I: MovieSelection: playerCallback: return_path: %s" % self.return_path)
			self.loadList(self["list"].getCurrentDir())
			self.updateInfo()

	def openPlayer(self, path):
		print("MVC-I: MovieSelection: openPlayer: path: %s" % path)
		self.resetInfo()
		self.return_path = self["list"].getCurrentPath()
		# Start Player
		self.session.openWithCallback(
			self.playerCallback,
			MediaCenter,
			self.getService4Path(self.filelist, path),
		)

### context menu

	def openContextMenu(self):
		if not self.short_key:
			self.short_key = True
		else:
			self.return_path = self["list"].getCurrentPath()
			self.session.open(
				MovieSelectionContextMenu,
				self,
				MENU_FUNCTIONS,
				self["list"].getCurrentDir(),
				None
			)

	def openPluginsMenu(self):
		self.short_key = False

		self.return_path = self["list"].getCurrentPath()
		self.session.open(
			MovieSelectionContextMenu,
			self,
			MENU_PLUGINS,
			self["list"].getCurrentDir(),
			self.getService4Path(self.filelist, self.return_path)
		)

### config / styles

	def openConfigScreen(self):
		self.session.openWithCallback(self.openConfigScreenCallback, ConfigScreen)

	def openConfigScreenCallback(self, reload_movie_selection=False):
		#print("MVC: MovieSelection: configScrenCallback: reload_movie_selection: %s" % reload_movie_selection)
		if reload_movie_selection:
			self.close(self.session, True)

	def openStyles(self):
		self.session.open(StylesScreen)

### templated list

	def setListStyle(self, list_style):
		self.return_path = self["list"].getCurrentPath()
		config.plugins.moviecockpit.list_style.value = list_style
		config.plugins.moviecockpit.list_style.save()
		self["list"].setListStyle(list_style)

	def toggleListType(self):
		index = self["list"].getListStyle()
		list_style = (index + 1) % len(MovieList.list_styles)
		self.setListStyle(list_style)

### cache

	def reloadCache(self):
		self.session.openWithCallback(
			self.reloadCacheConfirmed,
			MessageBox,
			_("Do you really want to reload the SQL cache?"),
			MessageBox.TYPE_YESNO
		)

	def reloadCacheConfirmed(self, answer):
		if answer:
			self.return_path = self["list"].getCurrentPath()
			self.session.openWithCallback(self.reloadCacheCallback, FileCacheLoadProgress, self.return_path)

	def reloadCacheCallback(self):
		#print("MVC: MovieSelection: reloadCacheCallback")
		reload_dir = self.getHomeDir()
		if self.return_path:
			reload_dir = os.path.dirname(self.return_path)
		self.loadList(reload_dir)
		self.updateSpaceInfo()

### movie ops

	### utils

	def selectDirectory(self, callback, title):
		self.session.openWithCallback(
			callback,
			LocationBox,
			windowTitle=title,
			text=_("Select directory"),
			currDir=self.getHomeDir(),
			bookmarks=config.movielist.videodirs,
			autoAdd=False,
			editDir=True,
			inhibitDirs=["/bin", "/boot", "/dev", "/etc", "/home", "/lib", "/proc", "/run", "/sbin", "/sys", "/usr", "/var"],
			minFree=100
		)

	### recording

	def stopRecordings(self):
		self.file_ops_list = []
		self.file_delete_list = []
		self.file_move_list = []
		self.exec_progress = False
		self.recordings_to_stop = []
		selection_list = self.getSelectionList()
		for path in selection_list:
			if isRecording(path):
				self.recordings_to_stop.append(path)
		if self.recordings_to_stop:
			self.stopRecordingsQuery()

	def stopRecordingsConfirmed(self, answer):
		if answer:
			for path in self.recordings_to_stop:
				stopRecording(path)
			self.deleteMoviesQuery()

	def stopRecordingsQuery(self):
		filenames = self.createMovieList(self.recordings_to_stop)
		self.session.openWithCallback(
			self.stopRecordingsConfirmed,
			MessageBox,
			_("Stop recording(s)") + "?\n" + filenames,
			MessageBox.TYPE_YESNO
		)

	### file I/O functions

	### utils

	def createMovieList(self, filelist):
		filenames = ""
		movies = len(filelist)
		for i, path in enumerate(filelist):
			if i >= 5 and movies > 5:  # only show first 5 entries in filelist
				filenames += " ..."
				break
			filename = os.path.basename(path)
			filenames += "\n" + filename
		return filenames

	### Delete

	def deleteMovies(self):
		self.file_ops_list = []
		self.file_delete_list = []
		self.file_move_list = []
		self.recordings_to_stop = []
		selection_list = self.getSelectionList()
		self.exec_progress = False
		for path in selection_list:
			#print("MVC: MovieSelection: deleteFile: %s" % path)
			filetype = self.getEntry4Path(self.filelist, path)[FILE_IDX_TYPE]
			directory = os.path.dirname(path)
			if not config.plugins.moviecockpit.trashcan_enable.value or os.path.basename(directory) == "trashcan":
				self.file_ops_list.append((FILE_OP_DELETE, path, None, filetype))
				self.file_delete_list.append(path)
			else:
				trashcan_path = self.getBookmark(path) + "/trashcan"
				self.file_ops_list.append((FILE_OP_MOVE, path, trashcan_path, filetype))
				self.file_move_list.append(path)

			if isRecording(path):
				self.recordings_to_stop.append(path)

		if self.recordings_to_stop:
			self.stopRecordingsQuery()
		else:
			self.deleteMoviesQuery()

	def deleteMoviesQuery(self, _answer=True):
		if self.file_delete_list:
			filenames = self.createMovieList(self.file_delete_list)
			msg = _("Permanently delete the selected video file(s) or dir(s)") + "?\n" + filenames
			self.session.openWithCallback(
				self.deleteMoviesConfirmed,
				MessageBox,
				msg,
				MessageBox.TYPE_YESNO
			)
		else:
			self.deleteMoviesConfirmed(True)

	def deleteMoviesConfirmed(self, answer):
		#print("MVC: MovieSelection: deleteMoviesConfirmed: answer: %s" % answer)
		self.unselectAll()
		if answer:
			self.execFileOps(self.file_ops_list, self.file_delete_list + self.file_move_list, self.exec_progress)

	###  move

	def moveMovies(self):
		self.selection_list = self.getSelectionList()
		self.selectDirectory(
			boundFunction(self.targetDirSelected, FILE_OP_MOVE),
			_("Move file(s)")
		)

	### copy

	def copyMovies(self):
		self.selection_list = self.getSelectionList()
		self.selectDirectory(
			boundFunction(self.targetDirSelected, FILE_OP_COPY),
			_("Copy file(s)"),
		)

	### move or copy

	def targetDirSelected(self, file_op, target_path):
		#print("MVC: MovieSelection: targetDirSelected")
		file_ops_list = []
		file_path_list = []
		exec_progress = False
		if target_path:
			#print("MVC: MovieSelection: targetDirSelected: self.selection_list: %s" % self.selection_list)
			for path in self.selection_list:
				if not isRecording(path):
					filetype = self.getEntry4Path(self.filelist, path)[FILE_IDX_TYPE]
					file_ops_list.append((file_op, path, os.path.normpath(target_path), filetype))
					file_path_list.append(path)
					exec_progress |= self.getMountPoint(path) != self.getMountPoint(target_path)
				else:
					msg = _("Can't move recordings") if file_op == FILE_OP_MOVE else _("Can't copy recordings")
					self.session.open(
						MessageBox,
						msg,
						MessageBox.TYPE_INFO
					)
					break
		self.unselectAll()
		#print("MVC: MovieSelection: targetDirSelected: file_ops_list: %s" % file_ops_list)
		self.execFileOps(file_ops_list, file_path_list, exec_progress)

	# trashcan

	def openTrashcan(self):
		#print("MVC: MovieSelection: openTrashcan")
		self.changeDir(self.getHomeDir() + "/trashcan")

	def emptyTrashcan(self):
		self.session.openWithCallback(
			self.emptyTrashcanConfirmed,
			MessageBox,
			_("Permanently delete all files in trashcan?"),
			MessageBox.TYPE_YESNO
		)

	def emptyTrashcanConfirmed(self, answer):
		if answer:
			file_ops_list = []
			self.return_path = self["list"].getCurrentPath()
			filelist = self.createFileList(self.getHomeDir() + "/trashcan")
			for entry in filelist:
				path = entry[FILE_IDX_PATH]
				if os.path.basename(path) != "..":
					file_ops_list.append((FILE_OP_DELETE, path, None, entry[FILE_IDX_TYPE]))
			#print("MVC: MovieSelection: emptyTrash: file_ops_list: " + str(file_ops_list))
			self.execFileOps(file_ops_list, [], False)

	### cutlist

	def removeCutListMarker(self):
		selection_list = self.getSelectionList()
		for path in selection_list:
			self.removeMarksCutList(path)
		self.unselectAll()
		#print("MVC: MovieSelection: removeCutListMarker: removed marker")

	def deleteCutListFile(self):
		selection_list = self.getSelectionList()
		for path in selection_list:
			self.deleteFileCutList(path)
		self.unselectAll()
		#print("MVC: MovieSelection: deleteCutListFile: deleted file")

	### fileops

	def execFileOps(self, file_ops_list, path_list, exec_progress):
		print("MVC-I: MovieSelection: execFileOps: file_ops_list: %s" % file_ops_list)
		print("MVC-I: MovieSelection: execFileOps: path_list: %s" % path_list)

		path = self["list"].getCurrentPath()
		self.return_path = path
		#print("MVC: MovieSelection: execFileOps: path: %s" % path)

		if path in path_list:
			self.return_path = self.filelist[0][FILE_IDX_PATH]  # first service in list
			index = 0
			for index, _entry in enumerate(self.filelist):
				if self.filelist[index][FILE_IDX_PATH] == path:
					break
			#print("MVC: MovieSelection: execFileOps: index 1: %s" % index)
			while (index < len(self.filelist) - 1) and path in path_list:
				index += 1
				path = self.filelist[index][FILE_IDX_PATH]
			#print("MVC: MovieSelection: execFileOps: index 2: %s" % index)
			if path not in path_list:
				self.return_path = path
			#print("MVC: MovieSelection: execFileOps: self.return_path: %s" % self.return_path)

		if exec_progress:
			self.session.open(FileOpsProgress, self, file_ops_list, self.return_path)
		else:
			self.execFileOpsNoProgress(file_ops_list)
