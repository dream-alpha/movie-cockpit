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


from __init__ import _
from Components.Button import Button
from Components.Label import Label
from Components.config import config
from Components.ActionMap import HelpableActionMap
from Tools.BoundFunction import boundFunction

KEY_RED = 0
KEY_GREEN = 1
KEY_YELLOW = 2
KEY_BLUE = 3

KEY_LABEL = 0
KEY_FUNCTION = 1


class KeyFunctions():
	def __init__(self, csel):
		self.csel = csel
		self.csel["key_red"] = Button()
		self.csel["key_green"] = Button()
		self.csel["key_yellow"] = Button()
		self.csel["key_blue"] = Button()
		self.csel["level"] = Label()
		self.initColorKeyFunctions(self)
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

	def initActions(self, csel):
		actions = HelpableActionMap(
			csel,
			"PluginMovieSelectionActions",
			{
				"MVCRED":		(boundFunction(self.execColorButton, KEY_RED),  	_("Color key red")),
				"MVCGREEN":		(boundFunction(self.execColorButton, KEY_GREEN), 	_("Color key green")),
				"MVCYELLOW":		(boundFunction(self.execColorButton, KEY_YELLOW), 	_("Color key yellow")),
				"MVCBLUE":		(boundFunction(self.execColorButton, KEY_BLUE), 	_("Color key blue")),
				"MVCOK":		(csel.entrySelected, 		 			_("Play")),
				"MVCEXIT":		(csel.exit, 	 					_("Exit")),
				"MVCMENU":		(csel.openContextMenu,				 	_("Context menu")),
				"MVCMENUL":		(csel.openPluginsMenu,				 	_("Plugins menu")),
				"MVCINFO":		(csel.showMovieInfoEPG, 				_("EPG info")),
				"MVCINFOL":		(csel.showMovieInfoTMDB,				_("TMDB info")),
				"MVCLEFT":		(csel.pageUp, 						_("Cursor page up")),
				"MVCRIGHT":		(csel.pageDown, 					_("Cursor page down")),
				"MVCUP":		(csel.moveUp, 						_("Cursor up")),
				"MVCDOWN":		(csel.moveDown, 					_("Cursor down")),
				"MVCBQTPLUS":		(csel.bqtPlus, 						_("Bouquet up")),
				"MVCBQTMINUS":		(csel.bqtMinus, 					_("Bouquet down")),
				"MVCVIDEOB":		(csel.videoFuncShort, 					_("Selection on/off")),
				"MVCVIDEOL":		(csel.videoFuncLong, 					_("Selection off")),
				"MVCSTOP":		(csel.stopRecordings, 					_("Stop recording(s)")),
				"MVCARROWNEXT":		(csel.nextColorButtonsLevel,				_("Color buttons next")),
				"MVCARROWPREVIOUS":	(csel.previousColorButtonsLevel,			_("Color buttons previous")),
				"0":			(csel.moveToMovieHome, 					_("Home")),
			},
			prio=-3  # give them a little more priority to win over base class buttons
		)
		return actions

	def initColorKeyFunctions(self, csel):
		#print("MVC: MovieSelection: initKeyFunctions")
		self.color_buttons_matrix = [
			[							# level 0
				[_("Delete"), csel.deleteMovies],		# red
				[_("Sort mode"), csel.toggleSortMode],		# green
				[_("Move"), csel.moveMovies],			# yellow
				[_("Home"), csel.moveToMovieHome]		# blue
			],
			[							# level 1
				[_("Delete"), csel.deleteMovies],		# red
				[_("Sort order"), csel.toggleSortOrder],	# green
				[_("Copy"), csel.copyMovies],			# yellow
				[_("Home"), csel.moveToMovieHome]		# blue
			],
			[							# level 2
				[_("Reload cache"), csel.reloadCache],		# red
				[_("List type"), csel.toggleListType],		# green
				[_("Styles"), csel.openStyles],			# yellow
				[_("Bookmarks"), csel.openBookmarks]		# blue
			],
			[							# level 3
				[_("Reset progress"), csel.resetProgress],	# red
				[_("Date/Mount"), csel.toggleDateMount],	# green
				[_("Timer list"), csel.openTimerList],		# yellow
				[_("Open setup"), csel.openConfigScreen],	# blue
			],
		]
		if config.plugins.moviecockpit.trashcan_enable.value:
			self.color_buttons_matrix[1][KEY_RED] = [_("Empty Trashcan"), csel.emptyTrashcan]
			self.color_buttons_matrix[0][KEY_BLUE] = [_("Trashcan"), csel.openTrashcan]

### color key exection function

	def execColorButton(self, key):
		self.color_buttons_matrix[self.color_buttons_level][key][KEY_FUNCTION]()
		self.resetColorButtonsLevel()
