#!/usr/bin/python
# encoding: utf-8
#
# Copyright (C) 2011 by Coolman & Swiss-MAD
#               2018 by dream-alpha
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
from Components.PluginComponent import plugins
from Plugins.Plugin import PluginDescriptor
from FileUtils import readFile
from Bookmarks import Bookmarks
from SkinUtils import getSkinPath
from ConfigScreen import ConfigScreen

FUNC_MOVIE_HOME = 0
FUNC_DIR_UP = 1
FUNC_RELOAD_WITHOUT_CACHE = 2
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


class MovieSelectionMenu(Screen, Bookmarks, object):
	skin = readFile(getSkinPath("MovieSelectionMenu.xml"))

	def __init__(self, session, menu_mode, service, selections, current_dir):
		Screen.__init__(self, session)
		self["title"] = StaticText()
		self.service = service
		self.selections = selections

		self["actions"] = ActionMap(
			["OkCancelActions", "ColorActions"],
			{"ok": self.okButton, "cancel": self.close, "red": self.close}
		)

		self.menu = []
		if menu_mode == "functions":
			self.setTitle(_("Select function"))

			if not self.isBookmark(os.path.realpath(current_dir)):
				self.menu.append((_("Movie home"), boundFunction(self.close, FUNC_MOVIE_HOME)))

			if not self.isBookmark(current_dir):
				self.menu.append((_("Directory up"), boundFunction(self.close, FUNC_DIR_UP)))

			self.menu.append((_("Select all"), boundFunction(self.close, FUNC_SELECT_ALL)))

			self.menu.append((_("Delete"), boundFunction(self.close, FUNC_DELETE)))
			self.menu.append((_("Move"), boundFunction(self.close, FUNC_MOVE)))
			self.menu.append((_("Copy"), boundFunction(self.close, FUNC_COPY)))

			if config.MVC.movie_trashcan_enable.value and os.path.exists(config.MVC.movie_trashcan_path.value):
				self.menu.append((_("Delete permanently"), boundFunction(self.close, FUNC_DELETE_PERMANENTLY)))
				self.menu.append((_("Empty trashcan"), boundFunction(self.close, FUNC_EMPTY_TRASHCAN)))
				self.menu.append((_("Open trashcan"), boundFunction(self.close, FUNC_OPEN_TRASHCAN)))

			self.menu.append((_("Remove cutlist marker"), boundFunction(self.close, FUNC_REMOVE_MARKER)))
			self.menu.append((_("Delete cutlist file"), boundFunction(self.close, FUNC_DELETE_CUTLIST)))

			self.menu.append((_("Reload cache"), boundFunction(self.close, FUNC_RELOAD_WITHOUT_CACHE)))
			self.menu.append((_("Setup"), boundFunction(session.open, ConfigScreen)))

		elif menu_mode == "plugins":
			self.setTitle(_("Select plugin"))
			if service:
				for p in plugins.getPlugins(PluginDescriptor.WHERE_MOVIELIST):
					self.menu.append((p.description, boundFunction(self.execPlugin, p)))

		self["menu"] = List(self.menu)

	def okButton(self):
		self["menu"].getCurrent()[1]()

	def execPlugin(self, plugin):
		# Very bad but inspect.getargspec won't work
		# Plugins should always be designed to accept additional parameters!
		try:
			plugin(self.session, self.service, self.selections)
		except Exception:
			plugin(session=self.session, service=self.service)
