#!/usr/bin/python
# encoding: utf-8
#
# Copyright (C) 2018 by dream-alpha
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
from MovieCache import MovieCache
from ConfigInit import ConfigInit
from RecordingControl import RecordingControl
from Version import VERSION
from SkinUtils import getSkinPath
from Trashcan import Trashcan
from ConfigScreen import ConfigScreen

gSession = None


def startup():
	print("MVC: plugin: +++")
	print("MVC: plugin: +++ Version: " + VERSION + " starts...")
	print("MVC: plugin: +++")

	ConfigScreen.setEPGLanguage()
	MovieCache.getInstance()
	RecordingControl()
	Trashcan.getInstance()
	loadSkin(getSkinPath("MediaCenterLCD.xml"))


def shutdown():
	print("MVC: plugin: ---")
	print("MVC: plugin: --- shutdown")
	print("MVC: plugin: ---")

	MovieCache.getInstance().close()


def showMovieSelection(*__):
	from MovieSelection import MovieSelection
	gSession.openWithCallback(showMovieSelectionCallback, MovieSelection)


def showMediaCenter(*args):
	from MediaCenter import MediaCenter
	gSession.openWithCallback(showMediaCenterCallback, MediaCenter, *args)


def showMovieSelectionCallback(*args):
	if args:
		showMediaCenter(*args)


def showMediaCenterCallback(reopen, *args):
	if reopen:
		showMovieSelection(*args)


def openSettings(session):
	session.open(ConfigScreen)


def openMovieSelection(session):
	from MovieSelection import MovieSelection
	session.openWithCallback(showMovieSelectionCallback, MovieSelection)


def autostart(reason, **kwargs):
	if reason == 0:  # start
		if "session" in kwargs:
			global gSession
			gSession = kwargs["session"]
			startup()

			if not config.MVC.ml_disable.value:
				launch_key = config.MVC.movie_launch.value
				if launch_key == "showMovies":
					InfoBar.showMovies = showMovieSelection
				elif launch_key == "showTv":
					InfoBar.showTv = showMovieSelection
				elif launch_key == "showRadio":
					InfoBar.showRadio = showMovieSelection
				elif launch_key == "openQuickbutton":
					InfoBar.openQuickbutton = showMovieSelection
				elif launch_key == "startTimeshift":
					InfoBar.startTimeshift = showMovieSelection
	elif reason == 1:  # shutdown
		shutdown()
	else:
		print("MVC: plugin: autostart: reason not handled: %s" % reason)


def Plugins(**__):
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
