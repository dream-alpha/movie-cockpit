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

from Components.Button import Button
from Components.Label import Label

KEY_RED = 0
KEY_GREEN = 1
KEY_YELLOW = 2
KEY_BLUE = 3

KEY_LABEL = 0
KEY_FUNCTION = 1


class KeyFunctions(object):
	def __init__(self, color_buttons_matrix):
		self["key_red"] = Button()
		self["key_green"] = Button()
		self["key_yellow"] = Button()
		self["key_blue"] = Button()
		self["level"] = Label()
		self.color_buttons_matrix = color_buttons_matrix
		self.setColorButtons()

### color button management functions

	def setColorButtons(self):
		self["level"].setText("<%s>" % (self.level + 1))
		self["key_red"].setText(self.color_buttons_matrix[self.level][KEY_RED][KEY_LABEL])
		self["key_green"].setText(self.color_buttons_matrix[self.level][KEY_GREEN][KEY_LABEL])
		self["key_yellow"].setText(self.color_buttons_matrix[self.level][KEY_YELLOW][KEY_LABEL])
		self["key_blue"].setText(self.color_buttons_matrix[self.level][KEY_BLUE][KEY_LABEL])

	def nextColorButtonsLevel(self):
		self.level = (self.level + 1) % len(self.color_buttons_matrix)
		self.setColorButtons()

	def previousColorButtonsLevel(self):
		self.level = self.level - 1 if self.level > 0 else len(self.color_buttons_matrix) - 1
		self.setColorButtons()

	def resetColorButtonsLevel(self):
		self.level = 0
		self.setColorButtons()

### key exection functions

	def execColorButton(self, key):
		self.color_buttons_matrix[self.level][key][KEY_FUNCTION]()
