#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 cmikula
# Copyright (C) 2019 dream-alpha
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# For more information on the GNU General Public License see:
# <http://www.gnu.org/licenses/>.
#
# For example, if you distribute copies of such a program, whether gratis or for a fee, you
# must pass on to the recipients the same freedoms that you received. You must make sure
# that they, too, receive or can get the source code. And you must show them these terms so they know their rights.
#

import os
from __init__ import _
from Screens.Screen import Screen
from Components.Button import Button
from Components.ActionMap import ActionMap
from Components.config import config, ConfigNothing, ConfigSelection, ConfigSubDict, ConfigText
from Components.ConfigList import ConfigListScreen
from Screens.MessageBox import MessageBox
from Screens.Standby import TryQuitMainloop
from StylesConfigUtils import storeConfig
from StylesOps import writeStyle, loadStyle, restoreSkin
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Components.Pixmap import Pixmap
from Components.config import getConfigListEntry
from PixmapDisplay import PixmapDisplay
from FileUtils import writeFile
from SkinUtils import getSkinPath


class ConfigSelectionEx(ConfigSelection):
	def __init__(self, choices, default):
		ConfigSelection.__init__(self, choices, default)


class StylesScreen(Screen, ConfigListScreen, PixmapDisplay):
	def __init__(self, session):
		#print("MVC: StylesScreen: __init__")
		Screen.__init__(self, session)
		PixmapDisplay.__init__(self)
		self.skinName = "MVCStyles"

		self["setupActions"] = ActionMap(["ColorActions", "OkCancelActions", "MenuActions"],
		{
			"ok": self.keySave,
			"cancel": self.close,
			"red": self.close,
			"green": self.keySave,
			"yellow": self.keyDefault,
			"blue": self.restoreBackupSkin,
		}, -2)
		self["key_red"] = Button(_("Exit"))
		self["key_green"] = Button(_("Apply"))
		self["key_yellow"] = Button(_("Default"))
		self["key_blue"] = Button(_("Reset"))
		self["preview"] = Pixmap()
		self.list = []
		ConfigListScreen.__init__(self, self.list, session)
		self["config"].onSelectionChanged.append(self.onSelectionChanged)
		self.skin_dir = os.path.dirname(getSkinPath("skin.xml"))
		self.onFirstExecBegin.append(self.loadStyle)
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle("MovieCockpit" + _("Styles"))

	def loadStyle(self):
		self.style = loadStyle(getSkinPath("styles.xml"))
		self.style.checkDependency = self.checkDependency
		self.preset = self.style.getPreset()
		self.createConfigListEntries()
		style_errors = self.style.checkPresets()
		if style_errors:
			filename = getSkinPath("styles_error.xml")
			writeFile(filename, style_errors)
			self.session.open(MessageBox, _("Style presets contain errors") + "\n" + filename, MessageBox.TYPE_ERROR)

	def keySave(self):
		config.MVCStyles.preset = ConfigSubDict()
		config.MVCStyles.style = ConfigSubDict()

		for item in self.list:
			if len(item) > 1:
				key = item[0]
				value = item[1].getValue()
				if value:
					#print("MVC: StylesScreen: keySave: key: %s, value: %s" % (key, value))
					if isinstance(item[1], ConfigSelectionEx):
						#print("MVC: StylesScreen: keySave: ConfigSelectionEx")
						config.MVCStyles.preset[key] = ConfigText()
						config.MVCStyles.preset[key].value = value
						continue
					if isinstance(item[1], ConfigSelection):
						#print("MVC: StylesScreen: keySave: ConfigSelection")
						config.MVCStyles.style[key] = ConfigText()
						config.MVCStyles.style[key].value = value

		writeStyle(self.style, config.MVCStyles, getSkinPath("skin.xml"))
		storeConfig()
		self.restartGUI()

	def restartGUI(self):
		dlg = self.session.openWithCallback(
			self.restartGUICallback,
			MessageBox,
			_("GUI restart is required to apply a new style.") + "\n" + _("Restart GUI now?"),
			MessageBox.TYPE_YESNO
		)
		dlg.setTitle(_("Restart GUI now?"))

	def restartGUICallback(self, answer):
		if answer:
			self.session.open(TryQuitMainloop, 3)
		self.close()

	def restoreBackupSkin(self):
		src = getSkinPath("skin_org.xml")
		if os.path.exists(src):
			text = _("Do you really want to reset style?")
			self.session.openWithCallback(self.restoreBackupSkinCallback, MessageBox, text, MessageBox.TYPE_YESNO)
		else:
			self.session.open(MessageBox, _("Backup skin does not exist, restore canceled"), MessageBox.TYPE_INFO)

	def restoreBackupSkinCallback(self, answer):
		if answer:
			restoreSkin()
			self.restartGUICallback(True)

	def keyDefault(self):
		#print("MVC: StylesScreen: key default")
		default = self.style.getDefault()
		for item in self.list:
			if len(item) > 1:
				key = item[0]
				val = item[1].getValue()
				if key and val and key in default:
					item[1].setValue(default[key])
					self["config"].invalidate(item)
		self.onSelectionChanged()

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)

	def keyRight(self):
		ConfigListScreen.keyRight(self)

	def onSelectionChanged(self):
		if len(self.list) > 1:
			current = self["config"].getCurrent()
			if current and len(current) > 1:
				name = current[0]
				value = current[1].getValue()
				# update preview
				self.updatePreview(name, value)

				if isinstance(current[1], ConfigSelectionEx):
					# update selection
					preset = self.preset[name][value]
					for name, value in preset.iteritems():
						for item in self.list:
							if item[0] == name:
								item[1].setValue(value)
								self["config"].invalidate(item)

	def getSelected(self, key, conf_dict):
		if key in conf_dict:
			if isinstance(conf_dict[key], str):
				return conf_dict[key]
			return conf_dict[key].value
		return None

	def getConfigSelection(self, T, _key, entries, selected):
		if not isinstance(entries, list):
			entries = list(entries)
		if selected not in entries:
			selected = None
		return T(entries, selected)

	def checkDependency(self, depend):
		if not depend:
			return True
		return os.path.exists(os.path.join(resolveFilename(SCOPE_PLUGINS), depend))

	def createConfigListEntries(self):
		self.list = []
		if not self.style.hasStyle():
			self.list.append(getConfigListEntry(_("Current skin can not be styled"), ConfigNothing()))
			self["config"].setList(self.list)
		else:
			depends = self.style.getDepends()
			default = self.style.getDefault()
			if self.preset:
				self.list.append(getConfigListEntry(_("PRESET")))
				for key1 in self.style.sort(self.preset):
					if not self.checkDependency(depends.get(key1)):
						continue
					selected = self.getSelected(key1, config.MVCStyles.preset)
					if not selected:
						selected = self.getSelected(key1, default)
					self.list.append(getConfigListEntry(key1, self.getConfigSelection(ConfigSelectionEx, key1, sorted(self.preset[key1]), selected)))
					#self.updatePreview(key1, selected)

			groups = self.style.getGroup()
			for key in self.style.sort(groups):
				#print key
				if not self.checkDependency(depends.get(key)):
					continue
				self.list.append(getConfigListEntry(key.upper()))
				for key1 in self.style.sort(groups[key]):
					#print "  " + key1
					if not self.checkDependency(depends.get(key1)):
						continue
					selected = self.getSelected(key1, config.MVCStyles.style)
					if not selected:
						selected = self.getSelected(key1, default)
					self.list.append(getConfigListEntry(key1, self.getConfigSelection(ConfigSelection, key1, sorted(groups[key][key1]), selected)))

			self["config"].setList(self.list)

	def updatePreview(self, name, value):
		default = ""
		preview = self.style.getPreview(name, value, default)
		#print("MVC: StylesScreen: updatePreview: Preview: %s, %s, %s" % (name, value, preview))
		if not preview:
			#print("MVC: StylesScreen: updatePreview: try to load preview from preset")
			preview = self.style.getPresetPreview(name, value, default)
		if preview is not None:
			filename = os.path.join(self.skin_dir + "/preview", preview)
		else:
			filename = self.skin_dir + "/preview/no_preview.svg"
		self.displayPixmap("preview", filename)
