#!/usr/bin/python
# coding=utf-8
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
from Components.config import config, ConfigText, ConfigSubDict
from Tools.Directories import fileExists
from Styles import Skin, Style  #, StyleUser
from StylesConfigUtils import loadConfig
from shutil import copy2
from SkinUtils import getSkinPath


def applyStyle():
	print("MVC-I: style_ops: applyStyle")
	config.MVCStyles.style = ConfigSubDict()
	config.MVCStyles.preset = ConfigSubDict()
	if isSkinStyled():
		loadStyleConfigFromSkin()
	else:
		loadConfig(config.MVCStyles.style)
		loadConfig(config.MVCStyles.preset)
		style = loadStyle(getSkinPath("styles.xml"))
		writeStyle(style, config.MVCStyles, getSkinPath("skin.xml"))

# def checkSkin4Update():
# 	mtime1 = getStyleUserFileMTime()
# 	mtime2 = getStyleUserFileMTimeFromSkin()
# 	if not isSkinChanged() and (not isSkinStyled() or mtime1 != mtime2):
# 		#print("MVC: style_ops: checkSkin4Update: perform update...")
# 		style = loadStyle(getSkinPath("styles.xml"))
# 		writeStyle(style, config.MVCStyles, getSkinPath("skin.xml"))

def loadStyleConfigFromSkin():
	print("MVC-I: style_ops: loadStyleConfigFromSkin")
	conf = getSkinConfig(getSkinPath("skin.xml"))
	for key1 in sorted(conf):
		for _key2 in sorted(conf[key1]):
			#print("MVC: style_ops: loadStyleConfigFromSkin: %s, %s, %s" % (key1, _key2, str(conf[key1][key2])))
			pass
	config.MVCStyles.style = ConfigSubDict()
	for key, value in conf["preset"].iteritems():
		config.MVCStyles.preset[key] = ConfigText()
		config.MVCStyles.preset[key].value = value
	for key, value in conf["style"].iteritems():
		config.MVCStyles.style[key] = ConfigText()
		config.MVCStyles.style[key].value = value
	config.MVCStyles.save()

def isSkinStyled():
	return Skin.checkStyled(getSkinPath("skin.xml"))

# def getStyleUserFile():
# 	return resolveFilename(SCOPE_CONFIG, STYLES_USER_FILENAME)
#
# def getStyleUserFileMTime():
# 	filename = getStyleUserFile()
# 	if os.path.exists(filename):
# 		stat = os.stat(filename)
# 		return str(stat.st_mtime)
# 	return None
#
# def getStyleUserFileMTimeFromSkin():
# 	return Skin.readUserMTime(getSkinPath("skin.xml"))

def getSkinConfig(filename):
	#print("MVC: style_ops: getSkinConfig: filename: %s" % filename)
	if Skin.checkStyled(filename):
		skin = Skin(filename)
		return skin.getConfig()
	return dict()

def backupSkin():
	src = getSkinPath("skin.xml")
	dst = getSkinPath("skin_org.xml")
	#print("MVC: style_ops: backupSkin: src: %s" % src)
	#print("MVC: style_ops: backupSkin: dst: %s" % dst)
	dst_path = os.path.dirname(dst)
	if not os.path.exists(dst_path):
		os.makedirs(dst_path)

	if not fileExists(dst) or not Skin.checkStyled(src):
		#print("MVC: style_ops: backupSkin: backing up...")
		copy2(src, dst)

	return dst

def restoreSkin():
	dst = getSkinPath("skin.xml")
	src = getSkinPath("skin_org.xml")
	#print("MVC: Styles: restorebackupSkinCallback: src: %s" % src)
	#print("MVC: Styles: restoreBackupSkinCallback: dst: %s" % dst)
	config.MVCStyles.preset.clear()
	config.MVCStyles.style.clear()
	copy2(src, dst)

def loadStyle(filename):
	style = Style(filename)
# 	user = StyleUser()
# 	if user.read(getStyleUserFile()) and user.isUsable4Skin("skin.xml"):
# 		user.loadToStyle(style, "skin.xml")
	style.printInfo()
	return style

def writeStyle(style, config_MVCStyles, filename):
	#print("MVC: style_ops: writeStyle: filename %s" % filename)
	#print("MVC: style_ops: writeStyle: " + str("#" * 80))

	nodes, style_info = style.getSkinComponents(config_MVCStyles)
	for _x in style_info:
		#print("MVC: style_ops: writeStyle: %s" % str(_x))
		pass

	#print("MVC: style_ops: writeStyle: " + str("-" * 80))

	backup = backupSkin()

	skin = Skin(backup)
#	skin.user_mtime = getStyleUserFileMTime()

	comparing = config.MVC.debug.value
	if comparing:
		skin.write(filename.replace(".xml", "_src.xml"))

	skin.style_info = style_info
	skin.applyNodes(nodes)
	skin.write(filename)

	if comparing:
		skin.write(filename.replace(".xml", "_dst.xml"))
	#print("MVC: style_ops: writeStyle: " + str("#" * 80))
