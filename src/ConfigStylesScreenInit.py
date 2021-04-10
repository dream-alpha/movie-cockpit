#!/usr/bin/python
# -*- coding: utf-8 -*-
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
#
# For example, if you distribute copies of such a program, whether gratis or for a fee, you
# must pass on to the recipients the same freedoms that you received. You must make sure
# that they, too, receive or can get the source code. And you must show them these terms so they know their rights.


from Debug import logger
import os
from __init__ import _
from Components.config import config, ConfigText, ConfigSelection
from Screens.MessageBox import MessageBox
from StyleOps import loadStyle, writeStyle
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from FileUtils import writeFile
from SkinUtils import getSkinPath
from ConfigStylesSelection import ConfigStylesSelection


class ConfigSelectionPreset(ConfigSelection):
	type = "preset"

	def __init__(self, key, choices, default):
		logger.debug("key: %s, choices: %s, default: %s", key, choices, default)
		ConfigSelection.__init__(self, choices, default)


class ConfigSelectionStyle(ConfigSelection):
	type = "style"

	def __init__(self, key, choices, default):
		logger.debug("key: %s, choices: %s, default: %s", key, choices, default)
		self.conf_key = key
		self.choices = choices
		self.default = default
		ConfigSelection.__init__(self, choices, default)


class ConfigStylesScreenInit():
	def __init__(self, session):
		logger.debug("...")
		self.session = session
		self.list = []
		self.skin_dir = os.path.dirname(getSkinPath("skin.xml"))
		self.loadStyle()

	def loadStyle(self):
		logger.debug("...")
		self.style = loadStyle(getSkinPath("styles.xml"))
		logger.debug("style: %s", str(self.style))
		self.style.checkDependency = self.checkDependency
		self.preset = self.style.getPreset()
		logger.debug("preset: %s", str(self.preset))
		style_errors = self.style.checkPresets()
		logger.debug("errors: %s", str(style_errors))
		if style_errors:
			file_name = getSkinPath("styles_error.xml")
			writeFile(file_name, style_errors)
			self.session.open(MessageBox, _("Style presets contain errors") + "\n" + file_name, MessageBox.TYPE_ERROR)

	def getSelected(self, key, conf_dict):
		logger.info("...")
		if key in conf_dict:
			if isinstance(conf_dict[key], str):
				logger.debug("key: %s, conf_dict[key]: %s", key, conf_dict[key])
				return conf_dict[key]
			logger.debug("key: %s, conf_dict[key].value: %s", key, conf_dict[key].value)
			return conf_dict[key].value
		logger.debug("None")
		return None

	def checkDependency(self, depend):
		if depend:
			return os.path.exists(os.path.join(resolveFilename(SCOPE_PLUGINS), depend))
		return True

	def createConfigListEntries(self):
		logger.info("...")
		self.section = 400 * "¯"
		self.list = []
		if self.style.hasStyle():
			depends = self.style.getDepends()
			logger.debug("depends: %s", str(depends))
			default = self.style.getDefault()
			logger.debug("default: %s", str(default))
			if self.preset:
				self.list.append((self.section, _("PRESET"), None, None, 0, [], ""))
				for key1 in self.style.sort(self.preset):
					if not self.checkDependency(depends.get(key1)):
						continue
					selected = self.getSelected(key1, config.plugins.moviecockpit.preset)
					if not selected:
						selected = self.getSelected(key1, default)
						logger.debug("key1: %s, selected: %s", key1, selected)
					self.list.append(
						(
							_(key1),
							ConfigSelectionPreset(key1, sorted(self.preset[key1]), selected),
							None, None, 0, [], ""
						)
					)

			groups = self.style.getGroup()
			logger.debug("stored_values: %s", str(config.plugins.moviecockpit.style.stored_values))
			logger.debug("groups: %s", str(groups))
			for key in self.style.sort(groups):
				logger.debug("key: %s", key)
				if not self.checkDependency(depends.get(key)):
					logger.debug("no dependency: %s", key)
					continue
				self.list.append((self.section, _(key).upper(), None, None, 0, [], ""))
				for key1 in self.style.sort(groups[key]):
					logger.debug("  %s", key1)
					choices = []
					for choice in sorted(groups[key][key1]):
						choices.append((choice, _(choice)))
					logger.debug("choices: %s", str(choices))
					if not self.checkDependency(depends.get(key1)):
						continue
					selected = self.getSelected(key1, config.plugins.moviecockpit.style)
					logger.debug("selected: %s", str(selected))
					if not selected:
						selected = self.getSelected(key1, default)
					self.list.append(
						(
							_(key1), ConfigSelectionStyle(key1, choices, selected),
							self.needsStyleUpdate, self.selectStyle, 0, [], _("Select an option for") + ": " + _(key1) + "\n" + _("Press OK for previews")
						)
					)
		return self.list

	def restartGUI(self):
		logger.error("...")

	def needsRestart(self, _element):
		logger.error("...")

	def needsStyleUpdate(self, _element):
		logger.error("...")
		return True

	def selectStyle(self, element):
		self.session.openWithCallback(self.selectStyleCallback, ConfigStylesSelection, element, self.style)

	def selectStyleCallback(self, key, value):
		logger.debug("saving key: %s, value: %s", key, value)
		if value and value != config.plugins.moviecockpit.style[key].value:
			logger.debug("saved key: %s", config.plugins.moviecockpit.style[key].value)
			config.plugins.moviecockpit.style[key] = ConfigText()
			config.plugins.moviecockpit.style[key].value = value
			config.plugins.moviecockpit.style.save()
			self.updateStyle()
			self.reloadConfig()

	def updateStyle(self):
		logger.info("...")
		writeStyle(self.style, getSkinPath("skin.xml"))
		self.needsStyleUpdate(None)

	def reloadConfig(self):
		logger.error("...")
