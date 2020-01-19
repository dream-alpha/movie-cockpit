#!/usr/bin/python
# coding=utf-8
#
# Copyright (C) 2018-2020 by dream-alpha
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


import os
from __init__ import _
from Components.config import config
from Components.ActionMap import HelpableActionMap
from Components.Sources.List import List
from Components.PluginComponent import plugins
from Screens.Screen import Screen
from Components.Sources.StaticText import StaticText
from Bookmarks import isBookmark
from MovieList import MovieList
from Screens.HelpMenu import HelpableScreen
from Plugins.Plugin import PluginDescriptor
from Tools.BoundFunction import boundFunction


MENU_FUNCTIONS = 1
MENU_PLUGINS = 2


class MovieSelectionContextMenu(Screen, HelpableScreen):
	def __init__(self, session, csel, menu_mode, current_dir, service=None):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self.menu_mode = menu_mode
		self.service = service
		self.skinName = "MVCSelectionContextMenu"
		self["title"] = StaticText()

		self["actions"] = HelpableActionMap(
			self,
			"ContextMenuActions",
			{
				"MVCEXIT":	(self.close,		_("Exit")),
				"MVCOK":	(self.ok,		_("Select function")),
				"MVCRED":	(self.close,		_("Cancel")),
				"MVCMENU":	(csel.openConfigScreen,	_("Open setup")),
			},
			-1
		)

		menu = []

		if menu_mode == MENU_FUNCTIONS:
			self.setTitle(_("Movie list menu"))

			if current_dir and not isBookmark(os.path.realpath(current_dir)):
				menu.append((_("Movie home"), (csel.moveToMovieHome, True)))
				menu.append((_("Directory up"), (boundFunction(csel.changeDir, current_dir + "/.."), True)))

			menu.append((_("Select all"), (csel.selectAll, True)))

			menu.append((_("Delete"), (csel.deleteMovies, True)))
			menu.append((_("Move"), (csel.moveMovies, True)))
			menu.append((_("Copy"), (csel.copyMovies, True)))

			if config.plugins.moviecockpit.trashcan_enable.value:
				menu.append((_("Empty trashcan"), (csel.emptyTrashcan, False)))
				menu.append((_("Open trashcan"), (csel.openTrashcan, True)))

			menu.append((_("Remove cutlist marker"), (csel.removeCutListMarker, True)))
			menu.append((_("Delete cutlist file"), (csel.deleteCutListFile, True)))

			menu.append((_("Bookmarks"), (csel.openBookmarks, False)))

			for list_style in range(len(MovieList.list_styles)):
				menu.append((_(MovieList.list_styles[list_style][1]), (boundFunction(csel.setListStyle, list_style), True)))

			menu.append((_("Reload cache"), (csel.reloadCache, False)))
			menu.append((_("Styles"), (csel.openStyles, False)))
			menu.append((_("Setup"), (csel.openConfigScreen, False)))
		elif menu_mode == MENU_PLUGINS:
			self.setTitle(_("Select plugin"))
			if service is not None:
				for plugin in plugins.getPlugins(PluginDescriptor.WHERE_MOVIELIST):
					menu.append((plugin.description, boundFunction(self.execPlugin, plugin)))

		self["menu"] = List(menu)

	def execPlugin(self, plugin):
		plugin(session=self.session, service=self.service)

	def ok(self):
		current_entry = self["menu"].getCurrent()
		if self.menu_mode == MENU_FUNCTIONS:
			current_entry[1][0]()  # execute function
			if current_entry[1][1]:
				self.close()
		else:
			current_entry[1]()  # execute plugin
