#!/usr/bin/python
# coding=utf-8
#
# Copyright (C) 2018-2021 by dream-alpha
#
# In case of reuse of this source code please do not remove this copyright.
#
#      This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#      GNU General Public License for more details.
#
#      For more information on the GNU General Public License see:
#      <http://www.gnu.org/licenses/>.


import os
from __init__ import _
from Debug import logger
from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Button import Button
from Components.ActionMap import HelpableActionMap
from SkinUtils import getSkinPath
from Tools.LoadPixmap import LoadPixmap


class ConfigStylesSelection(Screen, HelpableScreen):

	def __init__(self, session, element, style):
		Screen.__init__(self, session)
		self.element = element
		self.style = style

		HelpableScreen.__init__(self)
		self.skinName = "ConfigStylesSelection"

		self["actions"] = HelpableActionMap(
			self,
			"CockpitActions",
			{
				"OK":		(self.exit,	_("Exit")),
				"RIGHTR":	(self.right,	_("Next style")),
				"LEFTR":	(self.left,	_("Previous style")),
				"EXIT":		(self.exit,	_("Exit")),
				"RED":		(self.red,	_("Exit")),
				"GREEN":	(self.green,	_("Selection")),
				"BLUE":		(self.blue,	"")
			},
			prio=-1
		)

		logger.debug("element.value: %s", element.value)
		for choice in element.choices:
			logger.debug("choice: %s", str(choice))
		logger.debug("element.default: %s", element.default)

		self.skin_dir = os.path.dirname(getSkinPath("skin.xml"))
		self.choices = element.choices
		self.index = self.choices.index(element.default)
		self.setTitle(_("Style Selection"))
		self["style"] = Label()
		self["preview"] = Pixmap()
		self["key_green"] = Button(_("Selection"))
		self["key_red"] = Button(_("Cancel"))
		self["key_yellow"] = Button()
		self["key_blue"] = Button()
		self.onLayoutFinish.append(self.firstStart)

	def firstStart(self):
		self.updatePreview(self.choices[self.index])

	def left(self):
		self.index -= 1
		if self.index < 0:
			self.index = len(self.choices) - 1
		self.updatePreview(self.choices[self.index])

	def right(self):
		self.index += 1
		if self.index > len(self.choices) - 1:
			self.index = 0
		self.updatePreview(self.choices[self.index])

	def exit(self):
		self.close(self.element.conf_key, None)

	def red(self):
		self.close(self.element.conf_key, None)

	def green(self):
		self.close(self.element.conf_key, self.choices[self.index])

	def yellow(self):
		return

	def blue(self):
		return

	def updatePreview(self, value):
		name = self.element.conf_key
		self["style"].setText(_(name) + ": " + _(value))
		default = ""
		preview = self.style.getPreview(name, value, default)
		logger.debug("Preview: %s, %s, %s", name, value, preview)
		if not preview:
			logger.debug("try to load preview from preset")
			preview = self.style.getPresetPreview(name, value, default)
		if preview is not None:
			file_name = os.path.join(self.skin_dir + "/preview", preview)
		else:
			file_name = self.skin_dir + "/preview/no_preview.svg"
		self.showPreview(file_name)

	def showPreview(self, path):
		logger.debug("path: %s", path)
		if os.path.exists(path):
			ptr = LoadPixmap(path, cached=False)
			self["preview"].instance.setPixmap(ptr)
