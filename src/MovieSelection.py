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
from Components.Button import Button
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
from MovieList import MovieList
from MovieSelectionMenu import MovieSelectionMenu
from SkinUtils import getSkinPath
from RecordingUtils import isRecording, stopRecording
from CutList import CutList
from FileOps import FileOps, FILE_OP_DELETE, FILE_OP_MOVE, FILE_OP_COPY
from FileUtils import readFile
from FileCache import FILE_IDX_PATH, FILE_IDX_TYPE, FILE_IDX_EXT, FILE_IDX_NAME, FILE_TYPE_IS_DIR
from FileOpsProgress import FileOpsProgress
from FileCacheLoadProgress import FileCacheLoadProgress
from MediaTypes import extVideo
from ConfigInit import choices_skin_layout, sort_values, sort_modes, function_key_names, KEY_RED_SHORT, KEY_RED_LONG,\
	KEY_GREEN_SHORT, KEY_GREEN_LONG, KEY_YELLOW_SHORT, KEY_YELLOW_LONG, KEY_BLUE_SHORT, KEY_BLUE_LONG, KEY_INFO_SHORT, KEY_INFO_LONG
from MovieInfoEPG import MovieInfoEPG
from MovieInfoTMDB import MovieInfoTMDB
from MediaCenter import MediaCenter
from Trashcan import Trashcan
from MovieSelectionMenu import FUNC_MOVIE_HOME, FUNC_DIR_UP, FUNC_RELOAD_CACHE, FUNC_DELETE,\
	FUNC_DELETE_PERMANENTLY, FUNC_EMPTY_TRASHCAN, FUNC_OPEN_TRASHCAN, FUNC_SELECT_ALL, FUNC_COPY, FUNC_MOVE,\
	FUNC_REMOVE_MARKER, FUNC_DELETE_CUTLIST, FUNC_OPEN_BOOKMARKS, FUNC_RELOAD_MOVIE_SELECTION, FUNC_NOOP

instance = None


class MovieSelectionSummary(Screen, object):

	def __init__(self, session, parent):
		#print("MVC: MovieSelectionSummary: MovieSelectionSummary: __init__")
		Screen.__init__(self, session, parent)
		self.skinName = ["MVCSelectionSummary"]


class MovieSelection(Screen, HelpableScreen, FileOps, CutList, object):

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

		self.skinName = ["MVCSelection"]
		self.skin = readFile(self.getSkin())
		self["cover"] = Pixmap()
		desktop_size = getDesktop(0).size()
		self["Video"] = VideoWindow(decoder=0, fb_width=desktop_size.width(), fb_height=desktop_size.height())
		self["Service"] = MVCServiceEvent(ServiceCenter.getInstance())
		self["list"] = MovieList(self.current_sorting)
		self.cursor_direction = 0
		self.lastservice = None
		self["no_support"] = Label(_("Skin resolution other than Full HD is not supported yet."))
		self["space_info"] = Label("")
		self["sort_mode"] = Label("")
		self["key_red"] = Button()
		self["key_green"] = Button()
		self["key_yellow"] = Button()
		self["key_blue"] = Button()
		self.cover = config.MVC.cover.value
		self.function_key_names = function_key_names
		self.initFunctionKeys()
		self.short_key = True  # used for long / short key press detection
		self.delayTimer = eTimer()
		self.delayTimer_conn = self.delayTimer.timeout.connect(self.updateInfoDelayed)

		self.onShow.append(self.onDialogShow)
		self.onHide.append(self.onDialogHide)
		self["list"].onSelectionChanged.append(self.selectionChanged)

	def onDialogShow(self):
		print("MVC-I: MovieSelection: onDialogShow: self.return_path: %s" % self.return_path)
		self.lastservice = self.lastservice or self.session.nav.getCurrentlyPlayingServiceReference()
		print("MVC-I: MovieSelection: onDialogShow: self.lastservice: %s" % (self.lastservice.toString() if self.lastservice else None))
		self.updateSortMode()
		self["space_info"].setText(config.MVC.disk_space_info.value)

		if not self["list"]:
			current_dir = self.getBookmarks()[0]
			if not config.MVC.list_start_home.value and self.return_path:
				current_dir = os.path.dirname(self.return_path)
			self.reloadList(current_dir)

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

	def getSkin(self):
		#print("MVC: MovieSelection: getSkin: skin_layout: %s" % config.MVC.skin_layout.value)
		width = getDesktop(0).size().width()
		if width == 1920:
			skin = getSkinPath(config.MVC.skin_layout.value)
		else:
			skin = getSkinPath("NoSupport.xml")

		if config.MVC.skin_layout.value == "MovieSelectionPIG.xml":
			config.MVC.mini_tv.value = True
			config.MVC.cover.value = False
		elif config.MVC.skin_layout.value == "MovieSelectionCover.xml":
			config.MVC.cover.value = True
			config.MVC.mini_tv.value = False
		else:
			config.MVC.mini_tv.value = False
			config.MVC.cover.value = False
		return skin

	def createSummary(self):
		return MovieSelectionSummary

	def exit(self):
		print("MVC-I: MovieSelection: exit")
		self.delayTimer.stop()
		self.close()

	def initFunctionKeys(self):
		#print("MVC: MovieSelection: initFunctionKeys")
		self.function_key_functions = [
			self.moveToMovieHome, # KEY_FUNC_HOME
			self.deleteMovies, # KEY_FUNC_DELETE
			self.moveMovies, # KEY_FUNC_MOVE
			self.movieInfoTMDB, # KEY_FUNC_COVER_SEARCH
			self.copyMovies, # KEY_FUNC_COPY
			self.openBookmarks, # KEY_FUNC_BOOKMARKS
			self.toggleSortMode, # KEY_FUNC_SORT_MODE
			self.toggleSortOrder, # KEY_FUNC_SORT_ORDER
			self.movieEventInfo, # KEY_FUNC_EVENT_INFO
			self.movieInfoTMDB, # KEY_FUNC_TMDB_INFO
			self.openTrashcan, # KEY_FUNC_TRASHCAN
			self.disabledFunction, # KEY_FUNC_DISABLED
		]

		self.function_key_assignments = [
			int(config.MVC.key_shortredfunc.value), # KEY_RED_SHORT
			int(config.MVC.key_longredfunc.value), # KEY_RED_LONG'
			int(config.MVC.key_shortgreenfunc.value), # KEY_GREEN_SHORT
			int(config.MVC.key_longgreenfunc.value), # KEY_GREEN_LONG
			int(config.MVC.key_shortyellowfunc.value), # KEY_YELLOW_SHORT
			int(config.MVC.key_longyellowfunc.value), # KEY_YELLOW_LONG
			int(config.MVC.key_shortbluefunc.value), # KEY_BLUE_SHORT
			int(config.MVC.key_longbluefunc.value), # KEY_BLUE_LONG
			int(config.MVC.key_shortinfofunc.value), # KEY_INFO_SHORT
			int(config.MVC.key_longinfofunc.value), # KEY_INFO_LONG
		]

		# set key labels
		self["key_red"].text = self.function_key_names[int(config.MVC.key_shortredfunc.value)]
		self["key_green"].text = self.function_key_names[int(config.MVC.key_shortgreenfunc.value)]
		self["key_yellow"].text = self.function_key_names[int(config.MVC.key_shortyellowfunc.value)]
		self["key_blue"].text = self.function_key_names[int(config.MVC.key_shortbluefunc.value)]

		self["actions"] = HelpableActionMap(
			self,
			"PluginMovieSelectionActions",
			{
				"MVCOK":	(self.entrySelected, 	_("Play")),
				"MVCEXIT":	(self.exit, 		_("Exit")),
				"MVCMENU":	(self.openMenu, 	_("Selection menu")),
				"MVCMENUL":	(self.openMenu, 	_("Selection menu")),
				"MVCINFO":	(boundFunction(self.execFunctionKey, KEY_INFO_SHORT), self.function_key_names[self.function_key_assignments[KEY_INFO_SHORT]]),
				"MVCINFOL":	(boundFunction(self.execFunctionKey, KEY_INFO_LONG), self.function_key_names[self.function_key_assignments[KEY_INFO_LONG]]),
				"MVCRED":	(boundFunction(self.execFunctionKey, KEY_RED_SHORT), self.function_key_names[self.function_key_assignments[KEY_RED_SHORT]]),
				"MVCGREEN":	(boundFunction(self.execFunctionKey, KEY_GREEN_SHORT), self.function_key_names[self.function_key_assignments[KEY_GREEN_SHORT]]),
				"MVCYELLOW":	(boundFunction(self.execFunctionKey, KEY_YELLOW_SHORT), self.function_key_names[self.function_key_assignments[KEY_YELLOW_SHORT]]),
				"MVCBLUE":	(boundFunction(self.execFunctionKey, KEY_BLUE_SHORT), self.function_key_names[self.function_key_assignments[KEY_BLUE_SHORT]]),
				"MVCREDL":	(boundFunction(self.execFunctionKey, KEY_RED_LONG), self.function_key_names[self.function_key_assignments[KEY_RED_LONG]]),
				"MVCGREENL":	(boundFunction(self.execFunctionKey, KEY_GREEN_LONG), self.function_key_names[self.function_key_assignments[KEY_GREEN_LONG]]),
				"MVCYELLOWL":	(boundFunction(self.execFunctionKey, KEY_YELLOW_LONG), self.function_key_names[self.function_key_assignments[KEY_YELLOW_LONG]]),
				"MVCBlueL":	(boundFunction(self.execFunctionKey, KEY_BLUE_LONG), self.function_key_names[self.function_key_assignments[KEY_BLUE_LONG]]),
				"MVCLeft":	(self.pageUp, 		_("Cursor page up")),
				"MVCRight":	(self.pageDown, 	_("Cursor page down")),
				"MVCUp":	(self.moveUp, 		_("Cursor up")),
				"MVCDown":	(self.moveDown, 	_("Cursor down")),
				"MVCBqtPlus":	(self.bqtPlus, 		_("Bouquet up")),
				"MVCbqtMinus":	(self.bqtMinus, 	_("Bouquet down")),
				"MVCVIDEOB":	(self.videoFuncShort, 	_("Selection on/off")),
				"MVCVIDEOL":	(self.videoFuncLong, 	_("Selection off")),
				"MVCAUDIO":	(self.toggleSkin, 	_("Toggle skin")),
				"MVCTV":	(self.openTimerList, 	_("Timer list")),
				"MVCRADIO":	(self.resetProgress, 	_("Reset progress")),
				"MVCTEXT":	(self.toggleDateText, 	_("Date/Mountpoint")),
				"MVCSTOP":	(self.stopRecordings, 	_("Stop recording(s)")),
				"0":		(self.moveToMovieHome, 	_("Home")),
			},
			prio=-3  # give them a little more priority to win over base class buttons
		)
		self["actions"].csel = self

	def execFunctionKey(self, key):
		#print("MVC: MovieSelection: execFunctionKey: key: %s" % key)
		#print("MVC: MovieSelection: execFunctionKey: function: %s" % self.function_key_functions[key])
		if key % 2 == 0:  # short key
			if self.short_key is False:
				self.short_key = True
			else:
				#print("MVC: MovieSelection: execFunctionKey: function_key_assighments[key]: %s" % self.function_key_assignments[key])
				#print("MVC: MovieSeleciton: execFunctionKey: key function: %s" % self.function_key_functions[self.function_key_assignments[key]])
				self.function_key_functions[self.function_key_assignments[key]]()
		else:  # long key
			self.short_key = False
			self.function_key_functions[self.function_key_assignments[key]]()

### Cursor movements

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
		dirlist = self["list"].getDirList()
		if dirlist:
			pos = dirlist[FILE_IDX_PATH].index(self["list"].getCurrentDir()) % len(dirlist)
			pos = pos + 1 if pos < len(dirlist) - 1 else 0
			self.changeDir(dirlist[pos])

	def bqtPrevFolder(self):
		dirlist = self["list"].getDirList()
		if dirlist:
			pos = dirlist[FILE_IDX_PATH].index(self["list"].getCurrentDir()) % len(dirlist)
			pos = pos - 1 if pos > 0 else len(dirlist) - 1
			self.changeDir(dirlist[pos])

	def moveUp(self):
		#print("MVC: MovieSelection: moveUp")
		self.cursor_direction = -1
		self["list"].moveUp()
		self.return_path = self["list"].getCurrentPath()

	def moveDown(self):
		#print("MVC: MovieSelection: moveDown")
		self.cursor_direction = 1
		self["list"].moveDown()
		self.return_path = self["list"].getCurrentPath()

	def pageUp(self):
		self.cursor_direction = 0
		self["list"].pageUp()
		self.return_path = self["list"].getCurrentPath()

	def pageDown(self):
		self.cursor_direction = 0
		self["list"].pageDown()
		self.return_path = self["list"].getCurrentPath()

	def moveTop(self):
		self["list"].moveTop()
		self.return_path = self["list"].getCurrentPath()

	def moveSkipUp(self):
		self.cursor_direction = -1
		for _i in range(int(config.MVC.list_skip_size.value)):
			self["list"].moveUp()
			self.return_path = self["list"].getCurrentPath()

	def moveSkipDown(self):
		self.cursor_direction = 1
		for _i in range(int(config.MVC.list_skip_size.value)):
			self["list"].moveDown()
			self.return_path = self["list"].getCurrentPath()

	def moveEnd(self):
		self["list"].moveEnd()
		self.return_path = self["list"].getCurrentPath()

	def moveToIndex(self, index):
		self["list"].moveToIndex(index)
		self.return_path = self["list"].getCurrentPath()

	def moveToPath(self, path):
		#print("MVC: MovieSelection: moveToPath: path: %s" % path)
		self["list"].moveToPath(path)
		self.return_path = self["list"].getCurrentPath()

	def moveToMovieHome(self):
		self.changeDir(self.getBookmarks()[0])
		self.moveTop()
		self.return_path = self["list"].getCurrentPath()

### Key functions

	def disabledFunction(self):
		return

	def openTimerList(self):
		self.session.open(TimerEditList)

	def toggleDateText(self):
		config.MVC.movie_mountpoints.value = False if config.MVC.movie_mountpoints.value else True
		self.return_path = self["list"].getCurrentPath()
		self.reloadList(self["list"].getCurrentDir())

	def movieEventInfo(self):
		path = self["list"].getCurrentPath()
		#print("MVC: MovieSelection: infoFunc: path: %s" % path)
		epg_available = False
		if self["list"].getEntry4Index(self["list"].getCurrentIndex())[FILE_IDX_EXT] in extVideo:
			service = self["list"].getService4Path(path)
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
		if self["list"].getEntry4Index(self["list"].getCurrentIndex())[FILE_IDX_EXT] in extVideo:
			path = self["list"].getCurrentPath()
			name = self["list"].getEntry4Path(path)[FILE_IDX_NAME]
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
			self.reloadList(target_dir)
			self.moveTop()
			self.return_path = self["list"].getCurrentPath()

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
			current_service = self["list"].getService4Path(path)
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
		self.reloadList(self["list"].getCurrentDir())
		self.updateSortMode()

	def toggleSortOrder(self):
		mode, order = self.current_sorting
		order = not order
		self.current_sorting = mode, order
		self.return_path = self["list"].getCurrentPath()
		self.reloadList(self["list"].getCurrentDir())
		self.updateSortMode()

	def resetProgress(self):
		self.return_path = self["list"].getCurrentPath()
		selection_list = self.getSelectionList()
		for path in selection_list:
			self.resetLastCutList(path)
		self.reloadList(self["list"].getCurrentDir())

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

	def reloadListRecording(self, path, update_disk_space_info=False):
		#print("MVC: MovieSelection: reloadListRecording: path: %s" % path)
		current_dir = self["list"].getCurrentDir()
		if current_dir and current_dir == path:
			self.reloadList(path, update_disk_space_info)

	def reloadList(self, path, update_disk_space_info=False):
		#print("MVC: MovieSelection: reloadList: path: %s" % path)
		#print("MVC: MovieSelection: reloadList: self.return_path: %s" % self.return_path)
		self.resetInfo()
		self["list"].reloadList(path, self.current_sorting)
		self["list"].unselectAll()
		if self.return_path:
			self.moveToPath(self.return_path)
		if update_disk_space_info:
			self.updateSpaceInfo()

### -Selection functions

	def getSelectionList(self, including_current=True):
		selection_list = self["list"].getSelectionList(including_current=including_current)
		return selection_list

	def selectAll(self):
		#print("MVC: MovieSelection: selectAll")
		self["list"].selectAll()

	def unselectAll(self):
		#print("MVC: MovieSelection: unselectAll")
		self["list"].unselectAll()

	def selectionChanged(self):
		#print("MVC: MovieSelection: selectionChanged")
		self.updateInfo()

	def toggleSelection(self, index=-1):
		#print("MVC: MovieSelection: toggleSelection: index: %s" % index)
		if index >= 0:
			path = self["list"].getEntry4Index(index)[FILE_IDX_PATH]
		else:
			path = self["list"].getCurrentPath()

		selection_list = self.getSelectionList(including_current=False)
		#print("MVC: MovieSelection: toggleSelection: selection_list: %s" % selection_list)
		if path in selection_list:
			self["list"].unselectPath(path)
		else:
			self["list"].selectPath(path)

		# Move cursor
		if config.MVC.list_selmove.value != "o":
			if self.cursor_direction == -1 and config.MVC.list_selmove.value == "b":
				index = self["list"].getCurrentIndex() - 1
				if index < 0:
					index = len(self["list"]) - 1
				self.moveToIndex(index)
			else:
				index = self["list"].getCurrentIndex() + 1
				if index > len(self["list"]) - 1:
					index = 0
				self.moveToIndex(index)

	def entrySelected(self):
		path = self["list"].getCurrentPath()
		if path:
			if self["list"].getEntry4Index(self["list"].getCurrentIndex())[FILE_IDX_TYPE] == FILE_TYPE_IS_DIR:
				self.changeDir(path)
			else:
				if config.MVC.mini_tv.value:
					self.pigWorkaround()

				self.openPlayer(path)

### Player

	def playerCallback(self, reload_selection):
		print("MVC-I: MovieSelection: playerCallback: reload_selection: %s" % reload_selection)
		if not reload_selection:
			self.exit()
		else:
			self.return_path = self["list"].getCurrentPath()
			print("MVC-I: MovieSelection: playerCallback: return_path: %s" % self.return_path)
			self.reloadList(self["list"].getCurrentDir())
			self.updateInfo()
		return

	def openPlayer(self, path):
		print("MVC-I: MovieSelection: openPlayer: path: %s" % path)
		self.resetInfo()
		self.return_path = self["list"].getCurrentPath()
		# Start Player
		self.session.openWithCallback(
			self.playerCallback,
			MediaCenter,
			self["list"].getService4Path(path)
		)
		return

### Selection Menu

	def menuCallback(self, function=None):
		print("MVC-I: MovieSelection: menuCallback: function: %s" % function)
		if function == FUNC_MOVIE_HOME:
			self.moveToMovieHome()
		elif function == FUNC_COPY:
			self.copyMovies()
		elif function == FUNC_MOVE:
			self.moveMovies()
		elif function == FUNC_OPEN_TRASHCAN:
			self.openTrashcan()
		elif function == FUNC_DELETE_PERMANENTLY or function == FUNC_DELETE:
			self.deleteMovies(function == FUNC_DELETE_PERMANENTLY)
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
		elif function == FUNC_NOOP:
			pass
		else:
			print("MVC-E: MovieSelection: menuCallback: unknown function: %s" % function)

	def openMenu(self):
		self.return_path = self["list"].getCurrentPath()
		self.session.openWithCallback(
			self.menuCallback,
			MovieSelectionMenu,
			self["list"].getCurrentDir()
		)

### Cache

	def reloadCache(self):
		self.return_path = self["list"].getCurrentPath()
		self.session.openWithCallback(self.reloadCacheCallback, FileCacheLoadProgress)

	def reloadCacheCallback(self):
		#print("MVC: MovieSelection: reloadCacheCallback")
		reload_dir = self.getBookmarks()[0]
		if self.return_path:
			reload_dir = os.path.dirname(self.return_path)
		self.reloadList(reload_dir, update_disk_space_info=True)

### Movie Ops

	### Utils

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

	### Recording

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

	### File I/O functions

	### Utils

	def createMovieList(self, filelist):
		filenames = ""
		movies = len(filelist)
		for i, path in enumerate(filelist):
			if i >= 5 and movies > 5:  # only show first 5 entries in filelist
				filenames += " ..."
				break
			filename = self["list"].getEntry4Path(path)[FILE_IDX_NAME]
			filename, _ext = os.path.splitext(path)
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
			file_type = self["list"].getEntry4Path(path)[FILE_IDX_TYPE]
			directory = os.path.dirname(path)
			if delete_permanently or not config.MVC.trashcan_enable.value or os.path.basename(directory) == "trashcan":
				self.file_ops_list.append((FILE_OP_DELETE, file_type, path, None))
				self.file_delete_list.append(path)
			else:
				trashcan_path = self.getBookmark(path) + "/trashcan"
				self.file_ops_list.append((FILE_OP_MOVE, file_type, path, trashcan_path))

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

	###  Move

	def moveMovies(self):
		self.selectDirectory(
			boundFunction(self.targetDirSelected, FILE_OP_MOVE),
			_("Move file(s)")
		)

	### Copy

	def copyMovies(self):
		self.selectDirectory(
			boundFunction(self.targetDirSelected, FILE_OP_COPY),
			_("Copy file(s)"),
		)

	### Move or Copy

	def targetDirSelected(self, file_op, target_path):
		#print("MVC: MovieSelection: targetDirSelected")
		self.file_ops_list = []
		if target_path:
			selection_list = self.getSelectionList()
			for path in selection_list:
				if not isRecording(path):
					file_type = self["list"].getEntry4Path(path)[FILE_IDX_TYPE]
					self.file_ops_list.append((file_op, file_type, path, os.path.normpath(target_path)))
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

	# Trashcan

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
			Trashcan.getInstance().purgeTrashcan(empty_trash=True, callback=self.emptyTrashcanCallback)
			if os.path.basename(self["list"].getCurrentDir()) == "trashcan":
				self.reloadList(self.getBookmarks()[0] + "/trashcan")

	def emptyTrashcanCallback(self, _op, _path, _target_path, _file_type):
		#print("MVC: MovieSelection: emptyTrashcanCallback")
		if os.path.basename(os.path.dirname(self.return_path)) == "trashcan":
			self.reloadList(os.path.dirname(self.return_path), update_disk_space_info=True)
		else:
			self.updateSpaceInfo()

	### Cutlist

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
		for op, _file_type, path, target_path in selection_list:
			if target_path and self.getMountPoint(path) != self.getMountPoint(target_path):
				exec_progress = True
			if op == FILE_OP_DELETE or op == FILE_OP_MOVE:
				path_list.append(path)
				indexes.append(self["list"].getIndex4Path(path))

		current_path = self["list"].getCurrentPath()
		self.return_path = current_path

		if path_list and current_path in path_list:
			return_path = self["list"].getEntry4Index(0)[FILE_IDX_PATH]  # first service in list
			if indexes:
				indexes.sort()
				for i in range(indexes[0], self["list"].__len__() - 1):
					path = self["list"].getEntry4Index(i)[FILE_IDX_PATH]
					#print("MVC: MovieSelection: execFileOps: checking: %s" % path)
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
		self.reloadList(os.path.dirname(self.return_path), update_disk_space_info=True)

	def execFileOpsWithProgress(self, selection_list):
		print("MVC-I: MovieSelection: execFileOpsWithProgress: selection_list: " + str(selection_list))
		self.session.openWithCallback(self.execFileOpsWithProgressCallback, FileOpsProgress, selection_list)

	def execFileOpCallback(self, _op, _path, _target_path, _file_type):
		print("MVC-I: MovieSelection: execFileOpCallback: self.return_path %s" % self.return_path)
		self.reloadList(os.path.dirname(self.return_path), update_disk_space_info=True)

	def execFileOpsWithoutProgress(self, selection_list):
		print("MVC-I: MovieSelection: execFileOpsWithoutProgress: selection_list: " + str(selection_list))
		for entry in selection_list:
			op, file_type, path, target_path = entry
			print("MVC-I: MovieSelection: execFileOpsWithoutProgress: op: %s, path: %s, target_path: %s, file_type: %s" % (op, path, target_path, file_type))
			if path and not path.endswith(".."):
				self.execFileOp(op, path, target_path, file_type, self.execFileOpCallback)
