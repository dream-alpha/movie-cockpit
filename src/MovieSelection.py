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
from MovieCache import FILE_IDX_PATH
from FileOpsProgress import FileOpsProgress
from ConfigInit import sort_modes, function_key_names, KEY_RED_SHORT, KEY_RED_LONG, KEY_GREEN_SHORT, KEY_GREEN_LONG, KEY_YELLOW_SHORT,\
	KEY_YELLOW_LONG, KEY_BLUE_SHORT, KEY_BLUE_LONG, KEY_INFO_SHORT, KEY_INFO_LONG, KEY_FUNC_TOGGLE_COVER, KEY_FUNC_DISABLED

instance = None


class MovieSelectionSummary(Screen, object):

	def __init__(self, session, parent):
		#print("MVC: MovieSelectionSummary: MovieSelectionSummary: __init__")
		Screen.__init__(self, session, parent)
		self.skinName = ["MVCSelectionSummary"]


class MovieSelection(Screen, HelpableScreen, FileOps, object):

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
	current_sorting = property(fget=attrgetter('_current_sorting', sort_modes.get(config.MVC.movie_sort.value)[0]), fset=attrsetter('_current_sorting'))

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

		desktopSize = getDesktop(0).size()
		self["Video"] = VideoWindow(decoder=0, fb_width=desktopSize.width(), fb_height=desktopSize.height())

		self["Service"] = MVCServiceEvent(ServiceCenter.getInstance())
		self["list"] = MovieList(self.current_sorting)

		self.cursor_direction = 0
		self.lastservice = None

		self["space_info"] = Label("")
		self["sort_mode"] = Label("")

		self["key_red"] = Button()
		self["key_green"] = Button()
		self["key_yellow"] = Button()
		self["key_blue"] = Button()

		self.cover = config.MVC.cover.value

		self.function_key_names = function_key_names
		self.initFunctionKeys()

		# Key press short long handling
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
			if not config.MVC.start_home.value and self.return_path:
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
		desktopSize = getDesktop(0).size()
		self.instance.resize(eSize(*(desktopSize.width(), desktopSize.height())))
		self.session.nav.stopService()
		self["Video"].instance.resize(eSize(*(desktopSize.width(), desktopSize.height())))
		self["Video"].hide()

	def getSkin(self):
		#print("MVC: MovieSelection: getSkin: skin_layout: %s" % config.MVC.skin_layout.value)
		skin = getSkinPath(config.MVC.skin_layout.value)

		if config.MVC.skin_layout.value == "MovieSelectionPIG.xml":
			config.MVC.mini_tv.value = True
		elif config.MVC.skin_layout.value == "MovieSelectionCover.xml":
			config.MVC.cover.value = True
		else:
			config.MVC.mini_tv.value = False
			config.MVC.cover.value = False
		return skin

	def createSummary(self):
		return MovieSelectionSummary

	def exit(self):
		print("MVC-I: MovieSelection: exit")
		self.return_path = self["list"].getCurrentPath()
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
			self.toggleCover, # KEY_FUNC_TOGGLE_COVER
			self.toggleSortMode, # KEY_FUNC_SORT_MODE
			self.toggleSortOrder, # KEY_FUNC_SORT_ORDER
			self.movieEventInfo, # KEY_FUNC_EVENT_INFO
			self.movieInfoTMDB, # KEY_FUNC_TMDB_INFO
			self.openTrashcan, # KEY_FUNC_TRASHCAN
			self.disabledFunction, # KEY_FUNC_DISABLED
		]

		if not config.MVC.cover.value:
			self.function_key_functions[KEY_FUNC_TOGGLE_COVER] = self.function_key_functions[KEY_FUNC_DISABLED]
			self.function_key_names[KEY_FUNC_TOGGLE_COVER] = function_key_names[KEY_FUNC_DISABLED]

		self.function_key_assignments = [
			int(config.MVC.movie_shortredfunc.value), # KEY_RED_SHORT
			int(config.MVC.movie_longredfunc.value), # KEY_RED_LONG'
			int(config.MVC.movie_shortgreenfunc.value), # KEY_GREEN_SHORT
			int(config.MVC.movie_longgreenfunc.value), # KEY_GREEN_LONG
			int(config.MVC.movie_shortyellowfunc.value), # KEY_YELLOW_SHORT
			int(config.MVC.movie_longyellowfunc.value), # KEY_YELLOW_LONG
			int(config.MVC.movie_shortbluefunc.value), # KEY_BLUE_SHORT
			int(config.MVC.movie_longbluefunc.value), # KEY_BLUE_LONG
			int(config.MVC.movie_shortinfofunc.value), # KEY_INFO_SHORT
			int(config.MVC.movie_longinfofunc.value), # KEY_INFO_LONG
		]

		# set key labels
		self["key_red"].text = self.function_key_names[int(config.MVC.movie_shortredfunc.value)]
		self["key_green"].text = self.function_key_names[int(config.MVC.movie_shortgreenfunc.value)]
		self["key_yellow"].text = self.function_key_names[int(config.MVC.movie_shortyellowfunc.value)]
		self["key_blue"].text = self.function_key_names[int(config.MVC.movie_shortbluefunc.value)]

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
				"MVCBqtMnus":	(self.bqtMnus, 		_("Bouquet down")),
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

###
### Cursor movements
###

	def bqtPlus(self):
		if config.MVC.bqt_keys.value == "":
			self.moveTop()
		elif config.MVC.bqt_keys.value == "Skip":
			self.moveSkipUp()
		elif config.MVC.bqt_keys.value == "Folder":
			self.bqtNextFolder()

	def bqtMnus(self):
		if config.MVC.bqt_keys.value == "":
			self.moveEnd()
		elif config.MVC.bqt_keys.value == "Skip":
			self.moveSkipDown()
		elif config.MVC.bqt_keys.value == "Folder":
			self.bqtPrevFolder()

	def bqtNextFolder(self):
		dirlist = self["list"].bqtListFolders()
		if dirlist:
			pos = dirlist[FILE_IDX_PATH].index(self["list"].getCurrentDir()) % len(dirlist)
			pos = pos + 1 if pos < len(dirlist) else 0
			self.changeDir(dirlist[pos])

	def bqtPrevFolder(self):
		dirlist = self["list"].bqtListFolders()
		if dirlist:
			pos = dirlist[FILE_IDX_PATH].index(self["list"].getCurrentDir()) % len(dirlist)
			pos = pos - 1 if pos >= 0 else len(dirlist) - 1
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
		if self["list"].getCurrentDir() not in self.getBookmarks():
			self.changeDir(self.getBookmarks()[0])
		self.moveTop()
		self.return_path = self["list"].getCurrentPath()
###
### Key functions
###

	def disabledFunction(self):
		return

	def openTimerList(self):
		self.session.open(TimerEditList)

	def toggleDateText(self):
		config.MVC.movie_mountpoints.value = False if config.MVC.movie_mountpoints.value else True
		self.return_path = self["list"].getCurrentPath()
		self.reloadList(self["list"].getCurrentDir())

	def movieEventInfo(self):
		from MovieInfoEPG import MovieInfoEPG
		path = self["list"].getCurrentPath()
		#print("MVC: MovieSelection: infoFunc: path: %s" % path)
		if self["list"].currentSelIsPlayable():
			evt = self["list"].getCurrentEvent()
			if evt:
				service = self["list"].getServiceOfPath(path)
				self.session.open(MovieInfoEPG, evt, ServiceReference(service))

	def movieInfoTMDB(self):
		from MovieInfoTMDB import MovieInfoTMDB
		if self["list"].currentSelIsPlayable():
			path = self["list"].getCurrentPath()
			name = self["list"].getNameOfService(path)
			self.session.openWithCallback(self.movieInfoTMDBCallback, MovieInfoTMDB, path, name)

	def movieInfoTMDBCallback(self):
		self.updateInfo()

	def changeDir(self, path):
		#print("MVC: MovieSelection: changeDir: path: %s" % path)
		if path:
			target_dir = path
			if path.endswith(".."):
				# open parent folder
				target_dir = os.path.abspath(path)
			self.return_path = None
			self.reloadList(target_dir)
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
		if self.short_key is False:
			self.short_key = True
		else:
			self.toggleSelection()

	def videoFuncLong(self):
		self.short_key = False
		self.resetSelectionList()

	def updateInfo(self):
		#print("MVC: MovieSelection: updateInfo")
		self.resetInfo()
		self.updateTitle()
		self.delayTimer.start(int(config.MVC.movie_description_delay.value), True)

	def updateInfoDelayed(self):
		#print("MVC: MovieSelection: updateInfoDelayed")
		path = self["list"].getCurrentPath()
		if path:
			current_service = self["list"].getServiceOfPath(path)
			self["Service"].newService(current_service)

		if self.cover:
			self.showCover(path)

	def resetInfo(self):
		#print("MVC: MovieSelection: resetInfo")
		self.delayTimer.stop()
		self["Service"].newService(None)

	def resetReturnPath(self):
		#print("MVC: MovieSelection: resetReturnPath")
		self.return_path = None

	def updateSpaceInfo(self):
		disk_space_info = self.getMountPointsSpaceUsedPercent()
		#print("MVC: MovieSelection: updateSpaceInfo: disk_space_info: %s" % disk_space_info)
		self["space_info"].setText(disk_space_info)

	def updateTitle(self):
		title = "MovieCockpit - "
		# Display the current path
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

	def toggleCover(self):
		#print("MVC: MovieSelection: toggleCover")
		if config.MVC.cover.value:
			self.cover = False if self.cover else True
		self.updateInfo()

	def toggleSortMode(self):
		from ConfigInit import sort_values
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
			CutList(path).resetLastCutList()
		self.reloadList(self["list"].getCurrentDir())

	def toggleSkin(self):
		from ConfigInit import skin_layout_choices
		skin_index = 0
		for skin_index, layout in enumerate(skin_layout_choices):
			if layout[0] == config.MVC.skin_layout.value:
				break
		skin_index = (skin_index + 1) % len(skin_layout_choices)
		config.MVC.skin_layout.value = skin_layout_choices[skin_index][0]
		#print("MVC: MovieSelection: toggleSkin: skin_layout: %s" % config.MVC.skin_layout.value)
		self.return_path = self["list"].getCurrentPath()
		self.close(self.session, True)

	def reloadList(self, path, update_disk_space_info=False):
		#print("MVC: MovieSelection: reloadList: path: %s" % path)
		#print("MVC: MovieSelection: reloadList: self.return_path: %s" % self.return_path)
		self.resetInfo()
		self["list"].reloadList(path, self.current_sorting)
		self["list"].resetSelectionList()
		if self.return_path:
			self.moveToPath(self.return_path)
		if update_disk_space_info:
			self.updateSpaceInfo()

###
### -Selection functions
###

	def getSelectionList(self, including_current=True):
		selection_list = self["list"].getSelectionList(including_current=including_current)
		return selection_list

	def selectSelectionList(self):
		#print("MVC: MovieSelection: selectSelectionList")
		self["list"].selectSelectionList()

	def resetSelectionList(self):
		#print("MVC: MovieSelection: resetSelectionList")
		self["list"].resetSelectionList()

	def selectionChanged(self):
		#print("MVC: MovieSelection: selectionChanged")
		self.updateInfo()

	def toggleSelection(self, index=-1):
		#print("MVC: MovieSelection: toggleSelection: index: %s" % index)
		if index >= 0:
			path = self["list"].getPathOfIndex(index)
		else:
			path = self["list"].getCurrentPath()

		selection_list = self.getSelectionList(including_current=False)
		#print("MVC: MovieSelection: toggleSelection: selection_list: %s" % selection_list)
		if path in selection_list:
			self["list"].unselectService(path)
		else:
			self["list"].selectService(path)

		# Move cursor
		if config.MVC.moviecenter_selmove.value != "o":
			if self.cursor_direction == -1 and config.MVC.moviecenter_selmove.value == "b":
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
			if self["list"].currentSelIsVirtual():
				# Open folder and reload movielist
				self.changeDir(path)
			else:
				if config.MVC.mini_tv.value:
					self.pigWorkaround()

				self.openPlayer(path)

###
### Player
###

	def playerCallback(self, reload_selection):
		print("MVC-I: MovieSelection: playerCallback: reload_selection: %s" % reload_selection)
		if not reload_selection:
			self.exit()
		else:
			self.return_path = self["list"].getCurrentPath()
			self.reloadList(self["list"].getCurrentDir())
			self.updateInfo()
		return

	def openPlayer(self, path):
		print("MVC-I: MovieSelection: openPlayer: path: %s" % path)
		self.resetInfo()
		self.return_path = self["list"].getCurrentPath()
		# Start Player
		from MediaCenter import MediaCenter
		self.session.openWithCallback(
			self.playerCallback,
			MediaCenter,
			self["list"].getServiceOfPath(path)
		)
		return

###
### Selection Menu
###

	def menuCallback(self, function=None):
		from MovieSelectionMenu import FUNC_MOVIE_HOME, FUNC_DIR_UP, FUNC_RELOAD_WITHOUT_CACHE, FUNC_DELETE,\
			FUNC_DELETE_PERMANENTLY, FUNC_EMPTY_TRASHCAN, FUNC_OPEN_TRASHCAN, FUNC_SELECT_ALL,\
			FUNC_COPY, FUNC_MOVE, FUNC_REMOVE_MARKER, FUNC_DELETE_CUTLIST, FUNC_OPEN_BOOKMARKS,\
			FUNC_RELOAD_MOVIE_SELECTION, FUNC_NOOP
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
			self.selectSelectionList()
		elif function == FUNC_EMPTY_TRASHCAN:
			self.emptyTrashcan()
		elif function == FUNC_RELOAD_WITHOUT_CACHE:
			self["list"].reloadListWithoutCache(self["list"].getCurrentDir())
		elif function == FUNC_REMOVE_MARKER:
			self.removeCutListMarker()
		elif function == FUNC_DELETE_CUTLIST:
			self.deleteCutListFile()
		elif function == FUNC_OPEN_BOOKMARKS:
			self.openBookmarks()
		elif function == FUNC_RELOAD_MOVIE_SELECTION:
			self.return_path = self["list"].getCurrentPath()
			self.close(self.session, True)
		elif function == FUNC_NOOP:
			pass
		else:
			print("MVC-E: MovieSelection: menuCallback: unknown function: %s" % function)

	def openMenu(self):
		self.session.openWithCallback(
			self.menuCallback,
			MovieSelectionMenu,
			self["list"].getCurrentDir()
		)

###
### Movie Ops
###

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
		filenames = ""
		for path in self.recordings_to_stop:
			filenames += "\n" + path.split("/")[-1][:-3]
		self.session.openWithCallback(
			self.stopRecordingsConfirmed,
			MessageBox,
			_("Stop recording(s)") + "?" + filenames,
			MessageBox.TYPE_YESNO
		)

	### File I/O functions
	### Delete

	def deleteMovies(self, delete_permanently=False):

		def deletePermanently(path, delete_permanently):
			if path:
				directory = os.path.dirname(path)
				delete_permanently |= not config.MVC.movie_trashcan_enable.value
				delete_permanently |= os.path.basename(directory) == "trashcan"
				delete_permanently |= not os.path.exists(self.getBookmark(path) + "/trashcan")
			return delete_permanently

		self.recordings_to_stop = []
		selection_list = self.getSelectionList()
		self.file_ops_list = []
		for path in selection_list:
			#print("MVC: MovieSelection: deleteFile: %s" % path)
			file_type = self["list"].getTypeOfPath(path)
			if deletePermanently(path, delete_permanently):
				self.file_ops_list.append((FILE_OP_DELETE, file_type, path, None))
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

		def movieList(delete_list):
			names = ""
			movies = len(delete_list)
			for i, path in enumerate(delete_list):
				if i >= 5 and movies > 5:  # show only 5 entries in the file list
					names += "..."
					break
				name = self["list"].getNameOfService(path)
				if len(name) > 48:
					name = name[:48] + "..."  # limit the name string
				names += name + "\n" * (i < movies)
			return names

		delete_list = []
		for entry in self.file_ops_list:
			op, _file_type, path, _target_path = entry
			if op == FILE_OP_DELETE:
				delete_list.append(path)

		delete_permanently = len(delete_list) > 0
		if (config.MVC.movie_trashcan_enable.value and config.MVC.movie_delete_validation.value) or delete_permanently:
			msg = _('Permanently delete') if delete_permanently else _('Delete')
			names = movieList(delete_list)
			msg += " " + _("the selected video file(s), dir(s), link(s)") + "?\n" + names
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
		self.resetSelectionList()
		if answer:
			self.execFileOps(self.file_ops_list)

	###  Move

	def moveMovies(self):
		self.selectDirectory(
			self.moveTargetDirSelected,
			_("Move file(s)")
		)

	def moveTargetDirSelected(self, target_path):
		#print("MVC: MovieSelection: moveTargetDirSelected: target_path: %s" % target_path)
		self.file_ops_list = []
		if target_path:
			selection_list = self.getSelectionList()
			for path in selection_list:
				#print("MVC: MovieSelection: moveTargetDirSelected: path: %s" % path)
				file_type = self["list"].getTypeOfPath(path)
				#print("MVC: MovieSelection: moveTargetDirSelected: file_type: %s" % file_type)
				self.file_ops_list.append((FILE_OP_MOVE, file_type, path, os.path.normpath(target_path)))

		self.resetSelectionList()
		self.execFileOps(self.file_ops_list)

	### Copy

	def copyMovies(self):
		self.selectDirectory(
			self.copyTargetDirSelected,
			_("Copy file(s)"),
		)

	def copyTargetDirSelected(self, target_path):
		#print("MVC: MovieSelection: copyTargetDirSelected")
		self.file_ops_list = []
		if target_path:
			selection_list = self.getSelectionList()
			for path in selection_list:
				file_type = self["list"].getTypeOfPath(path)
				self.file_ops_list.append((FILE_OP_COPY, file_type, path, os.path.normpath(target_path)))
		self.resetSelectionList()
		self.execFileOps(self.file_ops_list)

	# Trashcan

	def openTrashcan(self):
		#print("MVC: MovieSelection: openTrashcan")
		self.changeDir(self.getBookmarks()[0] + "/trashcan")

	def emptyTrashcan(self):
		self.session.openWithCallback(
			self.emptyTrashcanConfirmed,
			MessageBox,
			_("Permanently delete all files in trashcan?"),
			MessageBox.TYPE_YESNO
		)

	def emptyTrashcanConfirmed(self, answer):
		from Trashcan import Trashcan
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
			cuts = CutList(path)
			cuts.removeMarksCutList()
		self.resetSelectionList()
		#print("MVC: MovieSelection: removeCutListMarker: removed marker")

	def deleteCutListFile(self):
		selection_list = self.getSelectionList()
		for path in selection_list:
			cuts = CutList(path)
			cuts.deleteFileCutList()
		self.resetSelectionList()
		#print("MVC: MovieSelection: deleteCutListFile: deleted file")

	### execute movie ops (including progress display)/file ops (without progress display)

	def execFileOps(self, selection_list):
		#print("MVC: MovieSelection: execFileOps: selection_list: " + str(selection_list))
		exec_progress = False
		path_list = []
		indexes = []
		for op, _file_type, path, target_path in selection_list:
			if target_path and self.isMountPoint(path) != self.isMountPoint(target_path):
				exec_progress = True
			if op == FILE_OP_DELETE or op == FILE_OP_MOVE:
				path_list.append(path)
				indexes.append(self["list"].getIndexOfPath(path))

		current_path = self["list"].getCurrentPath()
		self.return_path = current_path

		if path_list and current_path in path_list:
			return_path = self["list"].getPathOfIndex(0)  # first service in list
			if indexes:
				indexes.sort()
				for i in range(indexes[0], self["list"].__len__() - 1):
					path = self["list"].getPathOfIndex(i)
					print("MVC: MovieSelection: execFileOps: checking: %s" % path)
					if path not in path_list:
						return_path = path
						break
			print("MVC: MovieSelection: execFileOps: return_path: %s" % return_path)
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
