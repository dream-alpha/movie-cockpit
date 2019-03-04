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
from Components.ActionMap import ActionMap
from Components.Sources.List import List
from Screens.Screen import Screen
from Tools.BoundFunction import boundFunction
from Components.Sources.StaticText import StaticText
from Bookmarks import Bookmarks
from MovieList import MovieList

FUNC_MOVIE_HOME = 0
FUNC_DIR_UP = 1
FUNC_RELOAD_CACHE = 2
FUNC_DELETE = 3
FUNC_DELETE_PERMANENTLY = 4
FUNC_EMPTY_TRASHCAN = 5
FUNC_OPEN_TRASHCAN = 6
FUNC_SELECT_ALL = 7
FUNC_COPY = 8
FUNC_MOVE = 9
FUNC_OPEN_SETUP = 10
FUNC_REMOVE_MARKER = 11
FUNC_DELETE_CUTLIST = 12
FUNC_OPEN_BOOKMARKS = 13
FUNC_RELOAD_MOVIE_SELECTION = 14
FUNC_SET_LISTTYPE = 15
FUNC_NOOP = 99


class MovieSelectionContextMenu(Screen, Bookmarks, object):
	def __init__(self, session, current_dir):
		Screen.__init__(self, session)
		self.skinName = "MVCSelectionContextMenu"
		self["title"] = StaticText()
		self.reload_movie_selection = False

		self["actions"] = ActionMap(
			["OkCancelActions", "ColorActions"],
			{"ok": self.ok, "cancel": self.close, "red": self.close}
		)

		self.setTitle(_("Select function"))
		menu = []

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

		for list_style in range(len(MovieList.LIST_STYLES)):
			menu.append((MovieList.LIST_STYLES[list_style][1], boundFunction(self.close, FUNC_SET_LISTTYPE, list_style)))

		self["menu"] = List(menu)

	def ok(self):
		self["menu"].getCurrent()[1]()
