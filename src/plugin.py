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

from __init__ import _
from Components.config import config
from Plugins.Plugin import PluginDescriptor
from Screens.InfoBar import InfoBar
from skin import loadSkin
from Tools.BoundFunction import boundFunction
from MovieCache import MovieCache
from ConfigInit import ConfigInit
from RecordingControl import RecordingControl
from Version import VERSION
from SkinUtils import getSkinPath
from Trashcan import Trashcan
from ConfigScreen import ConfigScreen


def openSettings(session):
	print("MVC-I: plugin: openSettings")
	session.open(ConfigScreen)


def openMovieSelection(session):
	print("MVC-I: plugin: openMovieSelection")
	from MovieSelection import MovieSelection
	session.open(MovieSelection)


def autostart(reason, **kwargs):
	print("MVC-I: plugin: autostart: reason: %s" % reason)
	if reason == 0:  # startup
		if "session" in kwargs:
			session = kwargs["session"]
			if not config.MVC.ml_disable.value:
				launch_key = config.MVC.movie_launch.value
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

			print("MVC-I: plugin: +++ Version: " + VERSION + " starts...")
			ConfigScreen.setEPGLanguage()
			MovieCache.getInstance()
			RecordingControl()
			Trashcan.getInstance()
			loadSkin(getSkinPath("MediaCenterLCD.xml"))

	elif reason == 1:  # shutdown
		print("MVC-I: plugin: --- shutdown")
		MovieCache.getInstance().close()
	else:
		#print("MVC: plugin: autostart: reason not handled: %s" % reason)
		pass


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

	if config.MVC.extmenu_plugin.value:
		descriptors.append(
			PluginDescriptor(name="MovieCockpit" + " - " + _("Setup"),
			description=_("Open Setup"),
			icon="MovieCockpit.svg",
			where=[
				PluginDescriptor.WHERE_PLUGINMENU,
				PluginDescriptor.WHERE_EXTENSIONSMENU
			],
			fnc=openSettings))

	if config.MVC.extmenu_list.value and not config.MVC.ml_disable.value:
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
