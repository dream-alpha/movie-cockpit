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
import os
from __init__ import _
from Components.Button import Button
from Components.Label import Label
from Components.config import config
from Components.ActionMap import HelpableActionMap
from Tools.BoundFunction import boundFunction
from Plugins.SystemPlugins.CacheCockpit.FileCache import FileCache


KEY_RED = 0
KEY_GREEN = 1
KEY_YELLOW = 2
KEY_BLUE = 3


KEY_LABEL = 0
KEY_FUNCTION = 1


class Actions():
	def __init__(self, csel):
		self.csel = csel
		self.csel["key_red"] = Button()
		self.csel["key_green"] = Button()
		self.csel["key_yellow"] = Button()
		self.csel["key_blue"] = Button()
		self.csel["level"] = Label()
		self.initColorActions(self)
		self.setColorButtons()

### color button management functions

	def setColorButtons(self):
		self.csel["level"].setText("<%s>" % (self.color_buttons_level + 1))
		self.csel["key_red"].setText(self.color_buttons_matrix[self.color_buttons_level][KEY_RED][KEY_LABEL])
		self.csel["key_green"].setText(self.color_buttons_matrix[self.color_buttons_level][KEY_GREEN][KEY_LABEL])
		self.csel["key_yellow"].setText(self.color_buttons_matrix[self.color_buttons_level][KEY_YELLOW][KEY_LABEL])
		self.csel["key_blue"].setText(self.color_buttons_matrix[self.color_buttons_level][KEY_BLUE][KEY_LABEL])

	def nextColorButtonsLevel(self):
		self.color_buttons_level = (self.color_buttons_level + 1) % len(self.color_buttons_matrix)
		self.setColorButtons()

	def previousColorButtonsLevel(self):
		self.color_buttons_level = self.color_buttons_level - 1 if self.color_buttons_level > 0 else len(self.color_buttons_matrix) - 1
		self.setColorButtons()

	def resetColorButtonsLevel(self):
		self.color_buttons_level = 0
		self.setColorButtons()

### key init

	def initActions(self, csel, return_path, enable=True):
		if enable:
			keys = {
				"RED":			(boundFunction(self.execColorButton, KEY_RED),  		_("Color key red")),
				"GREEN":		(boundFunction(self.execColorButton, KEY_GREEN), 		_("Color key green")),
				"YELLOW":		(boundFunction(self.execColorButton, KEY_YELLOW), 		_("Color key yellow")),
				"BLUE":			(boundFunction(self.execColorButton, KEY_BLUE), 		_("Color key blue")),
				"OK":			(csel.selectedEntry, 		 				_("Play")),
				"EXIT":			(csel.exit, 	 						_("Exit")),
				"MENUS":		(csel.openContextMenu,				 		_("Context menu")),
				"MENUL":		(csel.openPluginsMenu,				 		_("Plugins menu")),
				"INFOS":		(csel.showMovieInfoEPG, 					_("EPG info")),
				"INFOL":		(csel.showMovieInfoTMDB,					_("TMDB info")),
				"LEFT":			(csel.movie_list.pageUp, 					_("Cursor page up")),
				"RIGHT":		(csel.movie_list.pageDown, 					_("Cursor page down")),
				"UP":			(csel.movie_list.moveUp, 					_("Cursor up")),
				"DOWN":			(csel.movie_list.moveDown, 					_("Cursor down")),
				"CHANNELUP":		(csel.movie_list.moveBouquetPlus, 				_("Bouquet up")),
				"CHANNELDOWN":		(csel.movie_list.moveBouquetMinus, 				_("Bouquet down")),
				"VIDEOS":		(csel.toggleSelection,						_("Selection on/off")),
				"VIDEOL":		(csel.unselectAll, 						_("Selection off")),
				"STOP":			(csel.stopRecordings, 						_("Stop recording(s)")),
				"NEXT":			(csel.nextColorButtonsLevel,					_("Color buttons next")),
				"PREVIOUS":		(csel.previousColorButtonsLevel,				_("Color buttons previous")),
				"0":			(csel.goHome,							_("Home")),
				"8":			(csel.showFileOpManagerProgress, 				_("File operations progress")),
			}
		else:
			keys = {
				"EXIT":		(csel.exit,							_("Exit")),
			}

		actions = HelpableActionMap(
			csel,
			"CockpitActions",
			keys,
			prio=-3  # give them a little more priority to win over base class buttons
		)
		actions.csel = csel
		self.setTrashcanActions(csel, return_path)
		return actions

	def initColorActions(self, csel):
		logger.debug("...")
		self.color_buttons_matrix = [
			[								# level 0
				[_("Delete"), csel.deleteMovies],				# red
				[_("Sort mode"), csel.movie_list.toggleSortMode],		# green
				[_("Move"), csel.moveMovies],					# yellow
				[_("Home"), boundFunction(csel.changeDir, FileCache.getInstance().getHomeDir())]	# blue
			],
			[								# level 1
				[_("Delete"), csel.deleteMovies],				# red
				[_("Sort order"), csel.movie_list.toggleSortOrder],		# green
				[_("Copy"), csel.copyMovies],					# yellow
				[_("Home"), boundFunction(csel.changeDir, FileCache.getInstance().getHomeDir())]	# blue
			],
			[								# level 2
				[_("Reload cache"), csel.reloadCache],				# red
				[_("List type"), csel.movie_list.toggleListStyle],		# green
				[_("Archive"), csel.archiveFiles],				# yellow
				[_("Bookmarks"), csel.openBookmarks]				# blue
			],
			[								# level 3
				[_("Reset progress"), csel.resetProgress],			# red
				[_("Date/Mount"), csel.toggleDateMount],			# green
				[_("Timer list"), csel.openTimerList],				# yellow
				[_("Open setup"), csel.openConfigScreen],			# blue
			],
		]
		if config.plugins.moviecockpit.trashcan_enable.value:
			self.color_buttons_matrix[1][KEY_RED] = [_("Empty trashcan"), csel.emptyTrashcan]
		if config.plugins.moviecockpit.archive_enable.value:
			self.color_buttons_matrix[2][KEY_YELLOW] = [_("Archive"), csel.archiveFiles]

	def setTrashcanActions(self, csel, path):
		if path and os.path.basename(path) == "trashcan":
			self.color_buttons_matrix[0][KEY_YELLOW] = [_("Restore"), csel.restoreMovies]
			self.color_buttons_matrix[0][KEY_BLUE] = [_("Home"), boundFunction(csel.changeDir, FileCache.getInstance().getHomeDir())]
		else:
			self.color_buttons_matrix[0][KEY_YELLOW] = [_("Move"), csel.moveMovies]
			if config.plugins.moviecockpit.trashcan_enable.value:
				self.color_buttons_matrix[0][KEY_BLUE] = [_("Trashcan"), csel.openTrashcan]
			else:
				self.color_buttons_matrix[0][KEY_BLUE] = [_("Home"), boundFunction(csel.changeDir, FileCache.getInstance().getHomeDir())]
		self.setColorButtons()

### color key exection function

	def execColorButton(self, key):
		self.color_buttons_matrix[self.color_buttons_level][key][KEY_FUNCTION]()
		self.resetColorButtonsLevel()
