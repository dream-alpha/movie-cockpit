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
from Components.config import config, ConfigText, ConfigSubDict
from Tools.Directories import fileExists
from Styles import Skin, Style
from StylesConfigUtils import loadConfig
from shutil import copy2
from SkinUtils import getSkinPath


def applyPluginStyle():
	print("MVC-I: StylesOps: applyPluginStyle")
	config.plugins.MVC.style = ConfigSubDict()
	config.plugins.MVC.preset = ConfigSubDict()
	if isSkinStyled():
		loadStyleConfigFromSkin()
	else:
		loadConfig(config.plugins.MVC.style)
		loadConfig(config.plugins.MVC.preset)
		style = loadStyle(getSkinPath("styles.xml"))
		writeStyle(style, getSkinPath("skin.xml"))


def loadStyleConfigFromSkin():
	print("MVC-I: StylesOps: loadStyleConfigFromSkin")
	conf = getSkinConfig(getSkinPath("skin.xml"))
#	for key1 in sorted(conf):
#		for key2 in sorted(conf[key1]):
#			#print("MVC: StylesOps: loadStyleConfigFromSkin: %s, %s, %s" % (key1, key2, str(conf[key1][key2])))
#			pass
	config.plugins.MVC.style = ConfigSubDict()
	for key, value in conf["preset"].iteritems():
		config.plugins.MVC.preset[key] = ConfigText()
		config.plugins.MVC.preset[key].value = value
	for key, value in conf["style"].iteritems():
		config.plugins.MVC.style[key] = ConfigText()
		config.plugins.MVC.style[key].value = value
	config.plugins.MVC.save()


def isSkinStyled():
	return Skin.checkStyled(getSkinPath("skin.xml"))


def getSkinConfig(filename):
	#print("MVC: StylesOps: getSkinConfig: filename: %s" % filename)
	if Skin.checkStyled(filename):
		skin = Skin(filename)
		return skin.getConfig()
	return dict()


def backupSkin():
	src = getSkinPath("skin.xml")
	dst = getSkinPath("skin_org.xml")
	#print("MVC: StylesOps: backupSkin: src: %s" % src)
	#print("MVC: StylesOps: backupSkin: dst: %s" % dst)
	dst_path = os.path.dirname(dst)
	if not os.path.exists(dst_path):
		os.makedirs(dst_path)

	if not fileExists(dst) or not Skin.checkStyled(src):
		#print("MVC: StylesOps: backupSkin: backing up...")
		copy2(src, dst)

	return dst


def restoreSkin():
	dst = getSkinPath("skin.xml")
	src = getSkinPath("skin_org.xml")
	#print("MVC: StylesOps: restorebackupSkinCallback: src: %s" % src)
	#print("MVC: StylesOps: restoreBackupSkinCallback: dst: %s" % dst)
	config.plugins.MVC.preset.clear()
	config.plugins.MVC.style.clear()
	copy2(src, dst)


def loadStyle(filename):
	style = Style(filename)
	style.printInfo()
	return style


def writeStyle(style, filename):
	#print("MVC: StylesOps: writeStyle: filename %s" % filename)
	#print("MVC: StylesOps: writeStyle: " + str("#" * 80))

	nodes, style_info = style.getSkinComponents()
	for _x in style_info:
		#print("MVC: StylesOps: writeStyle: %s" % str(_x))
		pass

	#print("MVC: StylesOps: writeStyle: " + str("-" * 80))

	backup = backupSkin()

	skin = Skin(backup)
#	skin.user_mtime = getStyleUserFileMTime()

	comparing = config.plugins.moviecockpit.debug.value
	if comparing:
		skin.write(filename.replace(".xml", "_src.xml"))

	skin.style_info = style_info
	skin.applyNodes(nodes)
	skin.write(filename)

	if comparing:
		skin.write(filename.replace(".xml", "_dst.xml"))
	#print("MVC: StylesOps: writeStyle: " + str("#" * 80))
