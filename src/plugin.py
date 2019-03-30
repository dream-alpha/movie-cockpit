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
from Plugins.Plugin import PluginDescriptor
from Screens.InfoBar import InfoBar
from Tools.BoundFunction import boundFunction
from FileCacheLoad import FileCacheLoad
from ConfigInit import ConfigInit
from RecordingControl import RecordingControl
from Version import VERSION
from SkinUtils import getSkinPath
from Trashcan import Trashcan
from ConfigScreen import ConfigScreen
from FileCacheSQL import SQL_DB_NAME
from Debug import initLogFile, createLogFile
from FileUtils import deleteFile
from skin import loadSkin, loadSingleSkinData, dom_skins
from StylesOps import applyStyle
from enigma import getDesktop
from Tools.Directories import resolveFilename, SCOPE_SKIN, SCOPE_CURRENT_SKIN, SCOPE_PLUGINS


def loadPluginSkin(skin_file):
	default_skin = resolveFilename(SCOPE_SKIN, "Default-FHD/MovieCockpit")
	current_skin = resolveFilename(SCOPE_CURRENT_SKIN, "MovieCockpit")
	plugin_skin = resolveFilename(SCOPE_PLUGINS, "Extensions/MovieCockpit")
	print("MVC-I: plugin: loadPluginSkin: current_skin: %s" % current_skin)
	print("MVC-I: plugin: loadPluginSkin: default_skin: %s" % default_skin)
	print("MVC-I: plugin: loadPluginSkin: plugin_skin: %s" % plugin_skin)
	if not (os.path.islink(default_skin) or os.path.isdir(default_skin)):
		print("MVC-I: plugin: loadPluginSkin: ln -s " + plugin_skin + " " + resolveFilename(SCOPE_SKIN, "Default-FHD"))
		os.system("ln -s " + plugin_skin + " " + resolveFilename(SCOPE_SKIN, "Default-FHD"))
	# apply style first
	applyStyle()
	# then load styled skin
	loadSkin(getSkinPath(skin_file), "")
	path, dom_skin = dom_skins[-1:][0]
	loadSingleSkinData(getDesktop(0), dom_skin, path)


def openSettings(session, **__):
	print("MVC-I: plugin: openSettings")
	session.open(ConfigScreen)


def openMovieSelection(session, **__):
	print("MVC-I: plugin: openMovieSelection")
	from MovieSelection import MovieSelection
	session.openWithCallback(reloadMovieSelection, MovieSelection)


def reloadMovieSelection(session=None, reload_movie_selection=False):
	if reload_movie_selection:
		print("MVC-I: plugin: reloadMovieSelection")
		openMovieSelection(session)


def autostart(reason, **kwargs):
	if reason == 0:  # startup
		if "session" in kwargs:
			if config.MVC.debug.value:
				initLogFile()
			print("MVC-I: plugin: +++ Version: " + VERSION + " starts...")
			print("MVC-I: plugin: autostart: reason: %s" % reason)
			session = kwargs["session"]
			if not config.MVC.plugin_disable.value:
				launch_key = config.MVC.plugin_launch_key.value
				if launch_key == "showMovies":
					InfoBar.showMovies = boundFunction(openMovieSelection, session)
				elif launch_key == "showTv":
					InfoBar.showTv = boundFunction(openMovieSelection, session)
				elif launch_key == "showRadio":
					InfoBar.showRadio = boundFunction(openMovieSelection, session)
				elif launch_key == "openQuickbutton":
					InfoBar.openQuickbutton = boundFunction(openMovieSelection, session)
				elif launch_key == "startTimeshift":
					InfoBar.startTimeshift = boundFunction(openMovieSelection, session)
			ConfigScreen.setEPGLanguage()
			RecordingControl()
			if not os.path.exists(SQL_DB_NAME) or os.path.exists("/etc/enigma2/.moviecockpit"):
				print("MVC-I: plugin: loading database...")
				deleteFile("/etc/enigma2/.moviecockpit")
				config.MVC.debug.value = False
				config.MVC.debug.save()
				FileCacheLoad.getInstance().loadDatabase(sync=True)
			else:
				print("MVC-I: plugin: database is already loaded.")
			Trashcan.getInstance()
			loadPluginSkin("skin.xml")
	elif reason == 1:  # shutdown
		print("MVC-I: plugin: --- shutdown")
		FileCacheLoad.getInstance().closeDatabase()
		if config.MVC.debug.value:
			createLogFile()
	else:
		print("MVC-I: plugin: autostart: reason not handled: %s" % reason)


def Plugins(**__):
	print("MVC-I: plugin: +++ Plugins")
	ConfigInit()

	descriptors = []
	descriptors.append(
		PluginDescriptor(
			where=[
				PluginDescriptor.WHERE_SESSIONSTART,
				PluginDescriptor.WHERE_AUTOSTART
			],
			fnc=autostart))

	if config.MVC.plugin_extmenu_settings.value:
		descriptors.append(
			PluginDescriptor(name="MovieCockpit" + " - " + _("Setup"),
			description=_("Open setup"),
			icon="MovieCockpit.svg",
			where=[
				PluginDescriptor.WHERE_PLUGINMENU,
				PluginDescriptor.WHERE_EXTENSIONSMENU
			],
			fnc=openSettings))

	if config.MVC.plugin_extmenu_plugin.value and not config.MVC.plugin_disable.value:
		descriptors.append(
			PluginDescriptor(name="MovieCockpit",
			description=_("Manage recordings"),
			icon="MovieCockpit.svg",
			where=[
				PluginDescriptor.WHERE_PLUGINMENU,
				PluginDescriptor.WHERE_EXTENSIONSMENU
			],
			fnc=openMovieSelection))
	return descriptors
