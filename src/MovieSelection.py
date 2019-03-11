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
from __init__ import _
from Components.config import config
from Components.ActionMap import HelpableActionMap
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
from Components.VideoWindow import VideoWindow
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
from ConfigInit import choices_skin_layout, sort_values, sort_modes
from MovieInfoEPG import MovieInfoEPG
from MovieInfoTMDB import MovieInfoTMDB
from MediaCenter import MediaCenter
from MovieSelectionContextMenu import FUNC_MOVIE_HOME, FUNC_DIR_UP, FUNC_RELOAD_CACHE, FUNC_DELETE,\
	FUNC_EMPTY_TRASHCAN, FUNC_OPEN_TRASHCAN, FUNC_SELECT_ALL, FUNC_COPY, FUNC_MOVE, FUNC_REMOVE_MARKER,\
	FUNC_DELETE_CUTLIST, FUNC_OPEN_BOOKMARKS, FUNC_RELOAD_MOVIE_SELECTION, FUNC_SET_LISTTYPE, FUNC_NOOP,\
	MENU_FUNCTIONS, MENU_PLUGINS
from MovieList import MovieList
from FileListUtils import FileListUtils
from MovieSelectionKeyFunctions import KeyFunctions, KEY_RED, KEY_GREEN, KEY_YELLOW, KEY_BLUE
from ConfigScreen import ConfigScreen

instance = None


class MovieSelectionSummary(Screen, object):

	def __init__(self, session, parent):
		#print("MVC: MovieSelectionSummary: MovieSelectionSummary: __init__")
		Screen.__init__(self, session, parent)
		self.skinName = ["MVCSelectionSummary"]


class MovieSelection(Screen, HelpableScreen, KeyFunctions, FileListUtils, FileOps, CutList, object):

	# Define static member variables
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

	level = property(fget=attrgetter('_level', 0), fset=attrsetter('_level'))
	return_path = property(fget=attrgetter('_return_path', None), fset=attrsetter('_return_path'))
	current_sorting = property(fget=attrgetter('_current_sorting', sort_modes.get(config.MVC.list_sort.value)[0]), fset=attrsetter('_current_sorting'))

	@staticmethod
	def getInstance():
		return instance

	def __init__(self, session, *__):
		#print("MVC: MovieSelection: __init__: self.return_path: %s" % self.return_path)
		global instance
		instance = self

		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		KeyFunctions.__init__(self, self.initColorKeyFunctions())

		self.initActions()
		self.filelist = []
		self.skinName = self.getSkinName()
		self["cover"] = Pixmap()
		desktop_size = getDesktop(0).size()
		self["Video"] = VideoWindow(decoder=0, fb_width=desktop_size.width(), fb_height=desktop_size.height())
		self["Service"] = MVCServiceEvent(ServiceCenter.getInstance())
		self["list"] = MovieList()
		self.cursor_direction = 0
		self.lastservice = None
		self["no_support"] = Label(_("Skin resolution other than Full HD is not supported yet."))
		self["space_info"] = Label()
		self["sort_mode"] = Label()
		self.cover = config.MVC.cover.value

		self.short_key = True  # used for long / short key press detection
		self.delayTimer = eTimer()
		self.delayTimer_conn = self.delayTimer.timeout.connect(self.updateInfoDelayed)

		self.onShow.append(self.onDialogShow)
		self.onHide.append(self.onDialogHide)
		self["list"].onSelectionChanged.append(self.selectionChanged)

	def initColorKeyFunctions(self):
		#print("MVC: MovieSelection: initKeyFunctions")
		color_buttons_matrix = [
			[							# level 0
				[_("Delete"), self.deleteMovies],		# red
				[_("Sort Mode"), self.toggleSortMode],		# green
				[_("Move"), self.moveMovies],			# yellow
				[_("Home"), self.moveToMovieHome]		# blue
			],
			[							# level 1
				[_("Delete"), self.deleteMovies],		# red
				[_("Sort Order"), self.toggleSortOrder],	# green
				[_("Copy"), self.copyMovies],			# yellow
				[_("Home"), self.moveToMovieHome]		# blue
			],
			[							# level 2
				[_("Reload cache"), self.reloadCache],		# red
				[_("List type"), self.toggleListType],		# green
				[_("Skin type"), self.toggleSkin],		# yellow
				[_("Bookmarks"), self.openBookmarks]		# blue
			],
			[							# level 3
				[_("Reset progress"), self.resetProgress],	# red
				[_("Date/Mount"), self.toggleDateMount],	# green
				[_("Timer list"), self.openTimerList],		# yellow
				[_("Open setup"), self.openConfigScreen],	# blue
			],
		]
		if config.MVC.trashcan_enable.value:
			color_buttons_matrix[1][KEY_RED] = [_("Empty Trashcan"), self.emptyTrashcan]
			color_buttons_matrix[0][KEY_BLUE] = [_("Trashcan"), self.openTrashcan]

		return color_buttons_matrix

	def initActions(self):
		self["actions"] = HelpableActionMap(
			self,
			"PluginMovieSelectionActions",
			{
				"MVCRED":		(boundFunction(self.execColorButton, KEY_RED),  	_("Color key red")),
				"MVCGREEN":		(boundFunction(self.execColorButton, KEY_GREEN), 	_("Color key green")),
				"MVCYELLOW":		(boundFunction(self.execColorButton, KEY_YELLOW), 	_("Color key yellow")),
				"MVCBLUE":		(boundFunction(self.execColorButton, KEY_BLUE), 	_("Color key blue")),
				"MVCOK":		(self.entrySelected, 		 			_("Play")),
				"MVCEXIT":		(self.exit, 	 					_("Exit")),
				"MVCMENU":		(self.openContextMenu,				 	_("Context menu")),
				"MVCMENUL":		(self.openPluginsMenu,				 	_("Plugins menu")),
				"MVCINFO":		(self.movieInfoEPG, 					_("EPG info")),
				"MVCINFOL":		(self.movieInfoTMDB,					_("TMDB info")),
				"MVCLEFT":		(self.pageUp, 						_("Cursor page up")),
				"MVCRIGHT":		(self.pageDown, 					_("Cursor page down")),
				"MVCUP":		(self.moveUp, 						_("Cursor up")),
				"MVCDOWN":		(self.moveDown, 					_("Cursor down")),
				"MVCBQTPLUS":		(self.bqtPlus, 						_("Bouquet up")),
				"MVCBQTMINUS":		(self.bqtMinus, 					_("Bouquet down")),
				"MVCVIDEOB":		(self.videoFuncShort, 					_("Selection on/off")),
				"MVCVIDEOL":		(self.videoFuncLong, 					_("Selection off")),
				"MVCSTOP":		(self.stopRecordings, 					_("Stop recording(s)")),
				"MVCARROWNEXT":		(self.nextColorButtonsLevel,				_("Color buttons next")),
				"MVCARROWPREVIOUS":	(self.previousColorButtonsLevel,			_("Color buttons previous")),
				"0":			(self.moveToMovieHome, 					_("Home")),
			},
			prio=-3  # give them a little more priority to win over base class buttons
		)
		self["actions"].csel = self

	def onDialogShow(self):
		print("MVC-I: MovieSelection: onDialogShow: self.return_path: %s" % self.return_path)
		self.lastservice = self.session.nav.getCurrentlyPlayingServiceReference()
		print("MVC-I: MovieSelection: onDialogShow: self.lastservice: %s" % (self.lastservice.toString() if self.lastservice else None))
		self.updateSortMode()
		self["space_info"].setText(config.MVC.disk_space_info.value)

		if not self.filelist:
			current_dir = self.getBookmarks()[0]
			if not config.MVC.list_start_home.value and self.return_path:
				current_dir = os.path.dirname(self.return_path)
			self.loadList(current_dir)
			self.return_path = self["list"].getCurrentPath()

		if self.return_path:
			self.moveToPath(self.return_path)

	def onDialogHide(self):
		if config.MVC.mini_tv.value:
			self.pigWorkaround()
			self.session.nav.playService(self.lastservice)

	def callHelpAction(self, *args):
		HelpableScreen.callHelpAction(self, *args)

	def pigWorkaround(self):
		desktop_size = getDesktop(0).size()
		self.instance.resize(eSize(*(desktop_size.width(), desktop_size.height())))
		self.session.nav.stopService()
		self["Video"].instance.resize(eSize(*(desktop_size.width(), desktop_size.height())))
		self["Video"].hide()

	def getSkinName(self):
		#print("MVC: MovieSelection: getSkinName: skin_layout: %s" % config.MVC.skin_layout.value)
		width = getDesktop(0).size().width()
		if width == 1920:
			skinName = config.MVC.skin_layout.value
		else:
			skinName = "MVCNoSupport"
			self.setTitle(_("Information"))

		config.MVC.mini_tv.value = False
		config.MVC.cover.value = False

		if skinName == "MVCSelectionPIG":
			config.MVC.mini_tv.value = True
		elif skinName == "MVCSelectionCover":
			config.MVC.cover.value = True
		return skinName

	def createSummary(self):
		return MovieSelectionSummary

	def exit(self):
		print("MVC-I: MovieSelection: exit")
		self.delayTimer.stop()
		self.close()

### cursor movements

	def bqtPlus(self):
		if config.MVC.list_bouquet_keys.value == "":
			self.moveTop()
		elif config.MVC.list_bouquet_keys.value == "Skip":
			self.moveSkipUp()
		elif config.MVC.list_bouquet_keys.value == "Folder":
			self.bqtNextFolder()

	def bqtMinus(self):
		if config.MVC.list_bouquet_keys.value == "":
			self.moveEnd()
		elif config.MVC.list_bouquet_keys.value == "Skip":
			self.moveSkipDown()
		elif config.MVC.list_bouquet_keys.value == "Folder":
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
		for _i in range(int(config.MVC.list_skip_size.value)):
			self.return_path = self["list"].moveUp()

	def moveSkipDown(self):
		self.cursor_direction = 1
		for _i in range(int(config.MVC.list_skip_size.value)):
			self.return_path = self["list"].moveDown()

	def moveEnd(self):
		self.return_path = self["list"].moveEnd()

	def moveToPath(self, path):
		#print("MVC: MovieSelection: moveToPath: path: %s" % path)
		index = self.getIndex4Path(self.filelist, path)
		self.return_path = self["list"].moveToIndex(index)

	def moveToMovieHome(self):
		self.changeDir(self.getBookmarks()[0])
		self.resetColorButtonsLevel()

### key functions

	def openTimerList(self):
		self.session.open(TimerEditList)

	def toggleDateMount(self):
		config.MVC.movie_mountpoints.value = False if config.MVC.movie_mountpoints.value else True
		self["list"].invalidateList()

	def movieInfoEPG(self):
		if self.short_key is False:
			self.short_key = True
		else:
			path = self["list"].getCurrentPath()
			#print("MVC: MovieSelection: infoFunc: path: %s" % path)
			epg_available = False
			if path and self["list"].getCurrentSelection()[FILE_IDX_EXT] in extVideo:
				service = self.getService4Path(self.filelist, path)
				if service:
					evt = ServiceCenter.getInstance().info(service).getEvent()
					if evt:
						epg_available = True
						self.session.open(MovieInfoEPG, evt, ServiceReference(service))
			if not epg_available:
				self.session.open(
					MessageBox,
					_("No EPG Info available"),
					MessageBox.TYPE_INFO
				)

	def movieInfoTMDB(self):
		self.short_key = False
		path = self["list"].getCurrentPath()
		entry = self.getEntry4Path(self.filelist, path)
		if entry and entry[FILE_IDX_EXT] in extVideo:
			name = entry[FILE_IDX_NAME]
			self.session.openWithCallback(self.movieInfoTMDBCallback, MovieInfoTMDB, path, name)

	def movieInfoTMDBCallback(self):
		self.updateInfo()

	def changeDir(self, path):
		#print("MVC: MovieSelection: changeDir: path: %s" % path)
		if path:
			target_dir = path
			if os.path.basename(path) == "..":
				# open parent folder
				target_dir = os.path.abspath(path)
			self.loadList(target_dir)
			self.return_path = self.moveTop()

	def openBookmarks(self):
		self.selectDirectory(
			self.openBookmarksCallback,
			_("Bookmarks") + ":"
		)

	def openBookmarksCallback(self, path):
		if path:
			self.changeDir(os.path.normpath(path))

	def videoFuncShort(self):
		if self.short_key is False:
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
		self.delayTimer.start(int(config.MVC.movie_description_delay.value), True)

	def updateInfoDelayed(self):
		#print("MVC: MovieSelection: updateInfoDelayed")
		path = self["list"].getCurrentPath()
		if path:
			current_service = self.getService4Path(self.filelist, path)
			self["Service"].newService(current_service)
		if self.cover:
			self.showCover(path)

	def resetInfo(self):
		#print("MVC: MovieSelection: resetInfo")
		self.delayTimer.stop()
		self["Service"].newService(None)

	def updateSpaceInfo(self):
		disk_space_info = self.getMountPointsSpaceUsedPercent()
		config.MVC.disk_space_info.value = disk_space_info
		config.MVC.disk_space_info.save()
		#print("MVC: MovieSelection: updateSpaceInfo: disk_space_info: %s" % disk_space_info)
		self["space_info"].setText(disk_space_info)

	def updateTitle(self):
		title = "MovieCockpit"
		if self["list"].getCurrentDir():
			title += " - "
			if os.path.basename(self["list"].getCurrentDir()) == "trashcan":
				title += _("trashcan")
			else:
				title += _("Recordings")
		self.setTitle(title)

	### sorting

	def updateSortMode(self):
		sort_mode_text = ""
		for _k, v in sort_modes.items():
			if v[0] == self.current_sorting:
				sort_mode_text = _("Sort Mode") + ": " + v[1]
				break
		self["sort_mode"].setText(sort_mode_text)

	def toggleSortMode(self):
		index = sort_values.index(self.current_sorting)
		self.current_sorting = sort_values[(index + 1) % len(sort_values)]
		self.return_path = self["list"].getCurrentPath()
		self.loadList(self["list"].getCurrentDir())
		self.updateSortMode()

	def toggleSortOrder(self):
		mode, order = self.current_sorting
		order = not order
		self.current_sorting = mode, order
		self.return_path = self["list"].getCurrentPath()
		self.loadList(self["list"].getCurrentDir())
		self.updateSortMode()

	def resetProgress(self):
		self.return_path = self["list"].getCurrentPath()
		selection_list = self.getSelectionList()
		for path in selection_list:
			self.resetLastCutList(path)
		self.loadList(self["list"].getCurrentDir())

	def toggleSkin(self):
		index = 0
		for i, layout in enumerate(choices_skin_layout):
			if layout[0] == config.MVC.skin_layout.value:
				index = i
				break
		index = (index + 1) % len(choices_skin_layout)
		config.MVC.skin_layout.value = choices_skin_layout[index][0]
		config.MVC.skin_layout.save()
		#print("MVC: MovieSelection: toggleSkin: skin_layout: %s" % config.MVC.skin_layout.value)
		self.close(self.session, True)

	def reloadList(self, path, update_disk_space_info=False):
		#print("MVC: MovieSelection: loadListRecording: path: %s" % path)
		#print("MVC: MovieSelection: loadedDirs: " + str(self.loadedDirs(self.filelist)))
		if path in self.loadedDirs(self.filelist):
			self.loadList(path, update_disk_space_info)
		elif update_disk_space_info:
			self.updateSpaceInfo()

	def loadList(self, path, update_disk_space_info=False):
		#print("MVC: MovieSelection: loadList: path: %s" % path)
		#print("MVC: MovieSelection: loadList start: self.return_path: %s" % self.return_path)
		self.resetInfo()
		MovieList.selection_list = []
		filelist = self.createFileList(path)
		if config.MVC.directories_show.value:
			filelist += self.createDirList(path)
		custom_list = self.createCustomList(path)
		self.filelist = custom_list + self.sortList(filelist, self.current_sorting)
		self["list"].setList(self.filelist)
		if self.return_path:
			self.moveToPath(self.return_path)
		if update_disk_space_info:
			self.updateSpaceInfo()
		#print("MVC: MovieSelection: loadList end: self.return_path: %s" % self.return_path)

### selection functions

	def getSelectionList(self, including_current=True):
		if not MovieList.selection_list and including_current:
			# if no selections made, select the current cursor position
			current_path = self["list"].getCurrentPath()
			if current_path:
				MovieList.selection_list.append(current_path)
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
		self["list"].invalidateList()

	def selectionChanged(self):
		#print("MVC: MovieSelection: selectionChanged")
		self.updateInfo()

	def toggleSelection(self):
		#print("MVC: MovieSelection: toggleSelection")
		path = self["list"].getCurrentPath()
		selection_list = self.getSelectionList(including_current=False)
		#print("MVC: MovieSelection: toggleSelection: selection_list: %s" % selection_list)
		if path in selection_list:
			self.unselectPath(path)
		else:
			self.selectPath(path)

		# Move cursor
		if config.MVC.list_selmove.value != "o":
			if self.cursor_direction == -1 and config.MVC.list_selmove.value == "b":
				self.return_path = self["list"].moveUp()
			else:
				self.return_path = self["list"].moveDown()

	def entrySelected(self):
		path = self["list"].getCurrentPath()
		if path:
			if self["list"].getCurrentSelection()[FILE_IDX_TYPE] == FILE_TYPE_DIR:
				self.changeDir(path)
			else:
				if config.MVC.mini_tv.value:
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
			self.getService4Path(self.filelist, path)
		)

### context menu

	def contextMenuCallback(self, function=None, param1=None):
		print("MVC-I: MovieSelection: contextMenuCallback: function: %s" % function)
		if function == FUNC_MOVIE_HOME:
			self.moveToMovieHome()
		elif function == FUNC_COPY:
			self.copyMovies()
		elif function == FUNC_MOVE:
			self.moveMovies()
		elif function == FUNC_OPEN_TRASHCAN:
			self.openTrashcan()
		elif function == FUNC_DELETE:
			self.deleteMovies()
		elif function == FUNC_DIR_UP:
			self.changeDir(self["list"].getCurrentDir() + "/..")
		elif function == FUNC_SELECT_ALL:
			self.selectAll()
		elif function == FUNC_EMPTY_TRASHCAN:
			self.emptyTrashcan()
		elif function == FUNC_RELOAD_CACHE:
			self.reloadCache()
		elif function == FUNC_REMOVE_MARKER:
			self.removeCutListMarker()
		elif function == FUNC_DELETE_CUTLIST:
			self.deleteCutListFile()
		elif function == FUNC_OPEN_BOOKMARKS:
			self.openBookmarks()
		elif function == FUNC_RELOAD_MOVIE_SELECTION:
			self.close(self.session, True)
		elif function == FUNC_SET_LISTTYPE:
			self.setListType(param1)
		elif function == FUNC_NOOP:
			pass
		else:
			print("MVC-E: MovieSelection: contextMenuCallback: unknown function: %s" % function)

	def openContextMenu(self):
		if self.short_key is False:
			self.short_key = True
		else:
			self.return_path = self["list"].getCurrentPath()
			self.session.openWithCallback(
				self.contextMenuCallback,
				MovieSelectionContextMenu,
				MENU_FUNCTIONS,
				self["list"].getCurrentDir(),
				None
			)

	def openPluginsMenu(self):
		self.short_key = False

		self.return_path = self["list"].getCurrentPath()
		service = self.getService4Path(self.filelist, self.return_path)
		self.session.open(
			MovieSelectionContextMenu,
			MENU_PLUGINS,
			self["list"].getCurrentDir(),
			service
		)

### setup

	def openConfigScreen(self):
		self.session.openWithCallback(self.openConfigScreenCallback, ConfigScreen)

	def openConfigScreenCallback(self, reload_movie_selection=False):
		#print("MVC: MovieSelection: configScrenCallback: reload_movie_selection: %s" % reload_movie_selection)
		if reload_movie_selection:
			self.close(self.session, True)

### templated list

	def setListType(self, list_style):
		self.return_path = self["list"].getCurrentPath()
		config.MVC.list_style.value = list_style
		config.MVC.list_style.save()
		self["list"].setListType(list_style)

	def toggleListType(self):
		index = self["list"].getListType()
		list_style = (index + 1) % len(MovieList.list_styles)
		self.setListType(list_style)

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
			self.session.openWithCallback(self.reloadCacheCallback, FileCacheLoadProgress)

	def reloadCacheCallback(self):
		#print("MVC: MovieSelection: reloadCacheCallback")
		reload_dir = self.getBookmarks()[0]
		if self.return_path:
			reload_dir = os.path.dirname(self.return_path)
		self.loadList(reload_dir, update_disk_space_info=True)

### movie ops

	### utils

	def selectDirectory(self, callback, title):
		self.session.openWithCallback(
			callback,
			LocationBox,
			windowTitle=title,
			text=_("Select directory"),
			currDir=self.getBookmarks()[0],
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

	def deleteMovies(self, delete_permanently=False):
		self.file_ops_list = []
		self.file_delete_list = []
		self.recordings_to_stop = []
		selection_list = self.getSelectionList()
		for path in selection_list:
			#print("MVC: MovieSelection: deleteFile: %s" % path)
			filetype = self.getEntry4Path(self.filelist, path)[FILE_IDX_TYPE]
			directory = os.path.dirname(path)
			if delete_permanently or not config.MVC.trashcan_enable.value or os.path.basename(directory) == "trashcan":
				self.file_ops_list.append((FILE_OP_DELETE, filetype, path, None))
				self.file_delete_list.append(path)
			else:
				trashcan_path = self.getBookmark(path) + "/trashcan"
				self.file_ops_list.append((FILE_OP_MOVE, filetype, path, trashcan_path))

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
			self.execFileOps(self.file_ops_list)

	###  move

	def moveMovies(self):
		self.selectDirectory(
			boundFunction(self.targetDirSelected, FILE_OP_MOVE),
			_("Move file(s)")
		)

	### copy

	def copyMovies(self):
		self.selectDirectory(
			boundFunction(self.targetDirSelected, FILE_OP_COPY),
			_("Copy file(s)"),
		)

	### move or copy

	def targetDirSelected(self, file_op, target_path):
		#print("MVC: MovieSelection: targetDirSelected")
		self.file_ops_list = []
		if target_path:
			selection_list = self.getSelectionList()
			for path in selection_list:
				if not isRecording(path):
					filetype = self.getEntry4Path(self.filelist, path)[FILE_IDX_TYPE]
					self.file_ops_list.append((file_op, filetype, path, os.path.normpath(target_path)))
				else:
					self.file_ops_list = []
					msg = _("Can't move recordings") if file_op == FILE_OP_MOVE else _("Can't copy recordings")
					self.session.open(
						MessageBox,
						msg,
						MessageBox.TYPE_INFO
					)
					break
		self.unselectAll()
		self.execFileOps(self.file_ops_list)

	# trashcan

	def openTrashcan(self):
		#print("MVC: MovieSelection: openTrashcan")
		if config.MVC.trashcan_enable.value:
			self.changeDir(self.getBookmarks()[0] + "/trashcan")
		else:
			self.session.open(
				MessageBox,
				_("Trashcan is not enabled"),
				MessageBox.TYPE_INFO
			)

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
			filelist = self.createFileList(self.getBookmarks()[0] + "/trashcan")
			for entry in filelist:
				path = entry[FILE_IDX_PATH]
				if os.path.basename(path) != "..":
					file_ops_list.append((FILE_OP_DELETE, entry[FILE_IDX_TYPE], path, None))
			print("MVC: MovieSelection: emptyTrash: file_ops_list: " + str(file_ops_list))
			self.execFileOps(file_ops_list)

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

	### execute movie ops (including progress display)/file ops (without progress display)

	def execFileOps(self, selection_list):
		#print("MVC: MovieSelection: execFileOps: selection_list: " + str(selection_list))
		exec_progress = False
		path_list = []
		indexes = []
		for op, _filetype, path, target_path in selection_list:
			if target_path and self.getMountPoint(path) != self.getMountPoint(target_path):
				exec_progress = True
			if op == FILE_OP_DELETE or op == FILE_OP_MOVE:
				path_list.append(path)
				indexes.append(self.getIndex4Path(self.filelist, path))

		#print("MVC: MovieSelection: execFileOps: path_list: " + str(path_list))
		#print("MVC: MovieSelection: execFileOps: indexes: " + str(indexes))

		current_path = self["list"].getCurrentPath()
		self.return_path = current_path

		if path_list and current_path in path_list:
			return_path = self.getEntry4Index(self.filelist, 0)[FILE_IDX_PATH]  # first service in list
			if indexes:
				indexes.sort()
				for i in range(indexes[0], len(self.filelist) - 1):
					path = self.getEntry4Index(self.filelist, i)[FILE_IDX_PATH]
					if path not in path_list:
						return_path = path
						break
				#print("MVC: MovieSelection: execFileOps: return_path: %s" % return_path)
				self.return_path = return_path

		if exec_progress:
			self.execFileOpsWithProgress(selection_list)
		else:
			self.execFileOpsWithoutProgress(selection_list)

	def execFileOpsWithProgressCallback(self):
		#print("MVC: MovieSelection: execFileOpsWithProgressCallback: self.return_path: %s" % self.return_path)
		self.loadList(os.path.dirname(self.return_path), update_disk_space_info=True)

	def execFileOpsWithProgress(self, selection_list):
		print("MVC-I: MovieSelection: execFileOpsWithProgress: selection_list: " + str(selection_list))
		self.session.openWithCallback(self.execFileOpsWithProgressCallback, FileOpsProgress, selection_list)

	def execFileOpsWithoutProgress(self, selection_list):
		print("MVC-I: MovieSelection: execFileOpsWithoutProgress: selection_list: " + str(selection_list))
		self.execution_list = selection_list
		if self.execution_list:
			self.execNextFileOp()

	def execNextFileOp(self):
		op, filetype, path, target_path = self.execution_list.pop(0)
		print("MVC-I: MovieSelection: execNextFileOp: op: %s, path: %s, target_path: %s, filetype: %s" % (op, path, target_path, filetype))
		if path and not path.endswith(".."):
			self.execFileOp(op, path, target_path, filetype)
		else:
			if self.execution_list:
				self.execNextFileOp()

	def execFileOpCallback(self, _op, _path, _target_path, _filetype):
		print("MVC-I: MovieSelection: execFileOpCallback: self.return_path %s" % self.return_path)
		self.reloadList(os.path.dirname(self.return_path), update_disk_space_info=True)
		if self.execution_list:
			self.execNextFileOp()
