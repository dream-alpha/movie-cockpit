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
from Components.Sources.List import List
from Components.PluginComponent import plugins
from Screens.Screen import Screen
from Tools.BoundFunction import boundFunction
from Components.Sources.StaticText import StaticText
from Bookmarks import Bookmarks
from MovieList import MovieList
from Screens.HelpMenu import HelpableScreen
from ConfigScreen import ConfigScreen
from Plugins.Plugin import PluginDescriptor

FUNC_MOVIE_HOME = 0
FUNC_DIR_UP = 1
FUNC_RELOAD_CACHE = 2
FUNC_DELETE = 3
FUNC_EMPTY_TRASHCAN = 4
FUNC_OPEN_TRASHCAN = 5
FUNC_SELECT_ALL = 6
FUNC_COPY = 7
FUNC_MOVE = 8
FUNC_OPEN_SETUP = 9
FUNC_REMOVE_MARKER = 10
FUNC_DELETE_CUTLIST = 11
FUNC_OPEN_BOOKMARKS = 12
FUNC_RELOAD_MOVIE_SELECTION = 13
FUNC_SET_LISTTYPE = 14
FUNC_NOOP = 99

MENU_FUNCTIONS = 1
MENU_PLUGINS = 2


class MovieSelectionContextMenu(Screen, HelpableScreen, Bookmarks, object):
	def __init__(self, session, menu_mode, current_dir, service):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self.service = service
		self.skinName = "MVCSelectionContextMenu"
		self["title"] = StaticText()
		self.reload_movie_selection = False

		self["actions"] = HelpableActionMap(
			self,
			"ContextMenuActions",
			{
				"MVCEXIT":	(self.close,		_("Exit")),
				"MVCOK":	(self.ok,		_("Select function")),
				"MVCRED":	(self.close,		_("Cancel")),
				"MVCMENU":	(self.openConfigScreen,	_("Open setup")),
			},
			-1
		)

		menu = []

		if menu_mode == MENU_FUNCTIONS:
			self.setTitle(_("Select function"))

			if current_dir and not self.isBookmark(os.path.realpath(current_dir)):
				menu.append((_("Movie home"), boundFunction(self.close, FUNC_MOVIE_HOME)))
				menu.append((_("Directory up"), boundFunction(self.close, FUNC_DIR_UP)))

			menu.append((_("Select all"), boundFunction(self.close, FUNC_SELECT_ALL)))

			menu.append((_("Delete"), boundFunction(self.close, FUNC_DELETE)))
			menu.append((_("Move"), boundFunction(self.close, FUNC_MOVE)))
			menu.append((_("Copy"), boundFunction(self.close, FUNC_COPY)))

			if config.MVC.trashcan_enable.value:
				menu.append((_("Empty trashcan"), boundFunction(self.close, FUNC_EMPTY_TRASHCAN)))
				menu.append((_("Open trashcan"), boundFunction(self.close, FUNC_OPEN_TRASHCAN)))

			menu.append((_("Remove cutlist marker"), boundFunction(self.close, FUNC_REMOVE_MARKER)))
			menu.append((_("Delete cutlist file"), boundFunction(self.close, FUNC_DELETE_CUTLIST)))

			menu.append((_("Bookmarks"), boundFunction(self.close, FUNC_OPEN_BOOKMARKS)))

			for list_style in range(len(MovieList.list_styles)):
				menu.append((_(MovieList.list_styles[list_style][1]), boundFunction(self.close, FUNC_SET_LISTTYPE, list_style)))

			menu.append((_("Setup"), self.openConfigScreen))
		elif menu_mode == MENU_PLUGINS:
			self.setTitle(_("Select plugin"))
			if service is not None:
				for plugin in plugins.getPlugins(PluginDescriptor.WHERE_MOVIELIST):
					menu.append((plugin.description, boundFunction(self.execPlugin, plugin)))

		self["menu"] = List(menu)

	def execPlugin(self, plugin):
		plugin(session=self.session, service=self.service)


	def openConfigScreen(self):
		self.session.openWithCallback(self.openConfigScreenCallback, ConfigScreen)

	def openConfigScreenCallback(self, reload_movie_selection=False):
		#print("MVC: MovieSelectionMenu: configScrenCallback: reload_movie_selection: %s" % reload_movie_selection)
		function = FUNC_RELOAD_MOVIE_SELECTION if reload_movie_selection else FUNC_NOOP
		self.close(function)

	def ok(self):
		self["menu"].getCurrent()[1]()
