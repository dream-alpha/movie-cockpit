#!/usr/bin/python
# coding=utf-8
#
# Copyright (C) 2011 by Coolman & Swiss-MAD
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
from __init__ import _
from Components.config import config, getConfigListEntry, configfile, ConfigText, ConfigPassword
from Components.Button import Button
from Components.Sources.StaticText import StaticText
from Screens.Screen import Screen
from Screens.LocationBox import LocationBox
from Screens.MessageBox import MessageBox
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.ActionMap import ActionMap
from enigma import eTimer, ePoint
from Components.ConfigList import ConfigListScreen
from enigma import eServiceEvent
from Screens.Standby import TryQuitMainloop
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Version import VERSION
from Trashcan import Trashcan
from StylesScreen import StylesScreen


class ConfigScreen(ConfigListScreen, Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = "MVCConfigScreen"

		self["actions"] = ActionMap(
			["OkCancelActions", "MVCConfigActions"],
			{
				"cancel": self.keyCancel,
				"MVCRED": self.keyCancel,
				"MVCGREEN": self.keySaveNew,
				"MVCYELLOW": self.loadDefaultSettings,
				"MVCBLUE": self.openStyles,
				"MVCBQTPLUS": self.bouquetPlus,
				"MVCBQTMINUS": self.bouquetMinus,
			},
			-2  # higher priority
		)

		self["VirtualKB"] = ActionMap(
			["VirtualKeyboardActions"],
			{
				"showVirtualKeyboard": self.keyText,
			},
			-2  # higher priority
		)

		self["VirtualKB"].setEnabled(False)

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("Save"))
		self["key_yellow"] = Button(_("Defaults"))
		self["key_blue"] = Button(_("Styles"))
		self["help"] = StaticText()

		self.list = []
		self.MVCConfig = []
		ConfigListScreen.__init__(self, self.list, session=self.session, on_change=self.changedEntry)
		self.needs_restart_flag = False
		self.defineConfig()
		self.createConfig()

		self.reloadTimer = eTimer()
		self.reloadTimer_conn = self.reloadTimer.timeout.connect(self.createConfig)

		# Override selectionChanged because our config tuples have a size bigger than 2
		def selectionChanged():
			current = self["config"].getCurrent()
			if self["config"].current != current:
				if self["config"].current:
					try:
						self["config"].current[1].onDeselect()
					except Exception:
						pass
				if current:
					try:
						current[1].onSelect()
					except Exception:
						pass
				self["config"].current = current
			for x in self["config"].onSelectionChanged:
				try:
					x()
				except Exception:
					pass
		self["config"].selectionChanged = selectionChanged
		self["config"].onSelectionChanged.append(self.updateHelp)
		self["config"].onSelectionChanged.append(self.handleInputHelpers)

	def defineConfig(self):
		self.section = 400 * "¯"
		#        config list entry
		#                                                           , config element
		#                                                           ,                                                       , function called on save
		#                                                           ,                                                       ,                       , function called if user has pressed OK
		#                                                           ,                                                       ,                       ,                       , usage setup level from E2
		#                                                           ,                                                       ,                       ,                       ,   0: simple+
		#                                                           ,                                                       ,                       ,                       ,   1: intermediate+
		#                                                           ,                                                       ,                       ,                       ,   2: expert+
		#                                                           ,                                                       ,                       ,                       ,       , depends on relative parent entries
		#                                                           ,                                                       ,                       ,                       ,       ,   parent config value < 0 = true
		#                                                           ,                                                       ,                       ,                       ,       ,   parent config value > 0 = false
		#                                                           ,                                                       ,                       ,                       ,       ,             , context sensitive help text
		#                                                           ,                                                       ,                       ,                       ,       ,             ,
		#        0                                                  , 1                                                     , 2                     , 3                     , 4     , 5           , 6
		self.MVCConfig = [
			(self.section                                       , _("GENERAL")                                          , None                  , None                  , 0     , []          , ""),
			(_("About")                                         , config.plugins.moviecockpit.fake_entry                , None                  , self.showInfo         , 0     , []          , _("HELP About")),
			(_("Disable plugin")                                , config.plugins.moviecockpit.disable                   , self.needsRestart     , None                  , 1     , []          , _("Help Disable Plugin")),
			(_("Start plugin with key")                         , config.plugins.moviecockpit.launch_key                , self.needsRestart     , None                  , 0     , []          , _("Help Start plugin with key")),
			(_("Show settings in extensions menu")              , config.plugins.moviecockpit.extmenu_settings          , self.needsRestart     , None                  , 0     , []          , _("Help Show plugin config in extensions menu")),
			(_("Show plugin in extensions menu")                , config.plugins.moviecockpit.extmenu_plugin            , self.needsRestart     , None                  , 0     , []          , _("Help Show plugin in extensions menu")),
			(_("Movie home at start")                           , config.plugins.moviecockpit.list_start_home           , None                  , None                  , 0     , []          , _("Help Movie home at start")),
			(_("Default sort mode")                             , config.plugins.moviecockpit.list_sort                 , None                  , None                  , 0     , []          , _("Help Sort mode at startup")),
			(self.section                                       , _("KEY-MAPPING")                                      , None                  , None                  , 0     , []          , ""),
			(_("Bouquet buttons behavior")                      , config.plugins.moviecockpit.list_bouquet_keys         , None                  , None                  , 0     , []          , _("Help Bouquet buttons behavior")),
			(_("List entries to skip")                          , config.plugins.moviecockpit.list_skip_size            , None                  , None                  , 0     , []          , _("Help List entries to skip")),
			(self.section                                       , _("PLAYBACK")                                         , None                  , None                  , 0     , []          , ""),
			(_("No resume below 10 seconds")                    , config.plugins.moviecockpit.movie_ignore_firstcuts    , None                  , None                  , 1     , []          , _("Help No resume below 10 seconds")),
			(_("Jump to first mark when playing movie")         , config.plugins.moviecockpit.movie_jump_first_mark     , None                  , None                  , 1     , []          , _("Help Jump to first mark when playing movie")),
			(_("Zap to live TV of recording")                   , config.plugins.moviecockpit.record_eof_zap            , None                  , None                  , 1     , []          , _("Help Zap to Live TV of recording")),
			(_("Automatic timers list cleaning")                , config.plugins.moviecockpit.timer_autoclean           , None                  , None                  , 1     , []          , _("Help Automatic timers list cleaning")),
			(self.section                                       , _("DISPLAY-SETTINGS")                                 , None                  , None                  , 0     , []          , ""),
			(_("Show directories")                              , config.plugins.moviecockpit.directories_show          , None                  , None                  , 0     , []          , _("Help Show directories")),
			(_("Show directories within movie list")            , config.plugins.moviecockpit.directories_ontop         , None                  , None                  , 0     , [-1]        , _("Help Show directories within movielist")),
			(_("Show directories information")                  , config.plugins.moviecockpit.directories_info          , None                  , None                  , 0     , [-2]        , _("Help Show directories information")),
			(_("Cursor predictive move after selection")        , config.plugins.moviecockpit.list_selmove              , None                  , None                  , 0     , []          , _("Help Cursor predictive move after selection")),
			(self.section                                       , _("SKIN-SETTINGS")                                    , None                  , None                  , 0     , []          , ""),
			(_("Show mountpoints")                              , config.plugins.moviecockpit.movie_mountpoints         , None                  , None                  , 0     , []          , _("Help Show mountpoints")),
			(_("Date format")                                   , config.plugins.moviecockpit.movie_date_format         , None                  , None                  , 0     , []          , _("Help Date format")),
			(_("Path to movie picons")                          , config.plugins.moviecockpit.movie_picons_path         , self.validatePath     , self.openLocationBox  , 0     , []          , _("Help Path to movie picons")),
			(_("Watching in progress percent")                  , config.plugins.moviecockpit.movie_watching_percent    , None                  , None                  , 0     , []          , _("Help Short watching percent")),
			(_("Finished watching percent")                     , config.plugins.moviecockpit.movie_finished_percent    , None                  , None                  , 0     , []          , _("Help Finished watching percent")),
			(_("Default color for movie")                       , config.plugins.moviecockpit.color                     , None                  , None                  , 0     , []          , _("Help Default color")),
			(_("Default color for highlighted movie")           , config.plugins.moviecockpit.color_sel                 , None                  , None                  , 0     , []          , _("Help Default color highlighted")),
			(_("Default color for recording movie")             , config.plugins.moviecockpit.recording_color           , None                  , None                  , 0     , []          , _("Help Default color recording")),
			(_("Default color for highlighted recording movie") , config.plugins.moviecockpit.recording_color_sel       , None                  , None                  , 0     , []          , _("Help Default color recording highlighted")),
			(_("Default color for selected movie")              , config.plugins.moviecockpit.selection_color           , None                  , None                  , 0     , []          , _("Help Default color selected")),
			(_("Default color for highlighted selected movie")  , config.plugins.moviecockpit.selection_color_sel       , None                  , None                  , 0     , []          , _("Help Default color selected highlighted")),
			(self.section                                       , _("MOVIE-COVER")                                      , None                  , None                  , 0     , []          , ""),
			(_("Show fallback cover")                           , config.plugins.moviecockpit.cover_fallback            , None                  , None                  , 0     , []          , _("Help Cover fallback")),
			(_("Search cover language")                         , config.plugins.moviecockpit.cover_language            , None                  , None                  , 0     , []          , _("Help Cover language")),
			(_("Search cover size")                             , config.plugins.moviecockpit.cover_size                , None                  , None                  , 0     , []          , _("Help Cover size")),
			(_("Search backdrop size")                          , config.plugins.moviecockpit.backdrop_size             , None                  , None                  , 0     , []          , _("Help Backdrop size")),
			(_("Download replace existing cover")               , config.plugins.moviecockpit.cover_replace_existing    , None                  , None                  , 0     , []          , _("Help Cover replace existing cover")),
			(_("Download cover to flash")                       , config.plugins.moviecockpit.cover_flash               , None                  , None                  , 0     , []          , _("Help Cover in flash")),
			(_("Download cover bookmark")                       , config.plugins.moviecockpit.cover_bookmark            , self.validatePath     , self.openLocationBox  , 0     , [-1]        , _("Help Cover bookmark")),
			(_("Download cover automatically for recording")    , config.plugins.moviecockpit.cover_auto_download       , None                  , None                  , 0     , []          , _("Help Cover auto download")),
			(self.section                                       , _("TRASHCAN")                                         , None                  , None                  , 0     , []          , ""),
			(_("Enable trashcan")                               , config.plugins.moviecockpit.trashcan_enable           , self.activateTrashcan , None                  , 0     , []          , _("Help Trashcan enable")),
			(_("Show trashcan directory")                       , config.plugins.moviecockpit.trashcan_show             , None                  , None                  , 0     , [-1]        , _("Help Show trashcan directory")),
			(_("Show trashcan information")                     , config.plugins.moviecockpit.trashcan_info             , None                  , None                  , 0     , [-2, -1]    , _("Help Trashcan info")),
			(_("Enable auto trashcan cleanup")                  , config.plugins.moviecockpit.trashcan_clean            , None                  , None                  , 0     , [-3]        , _("Help Enable auto trashcan cleanup")),
			(_("File retention period in trashcan")             , config.plugins.moviecockpit.trashcan_retention        , None                  , None                  , 0     , [-4, -1]    , _("Help How many days files may remain in trashcan")),
			(self.section                                       , _("LANGUAGE")                                         , None                  , None                  , 1     , []          , ""),
			(_("Preferred EPG language")                        , config.plugins.moviecockpit.epglang                   , ConfigScreen.setEPGLanguage, None             , 1     , []          , _("Help Preferred EPG language")),
			(_("Enable playback auto-subtitling")               , config.plugins.moviecockpit.autosubs                  , None                  , None                  , 1     , []          , _("Help Enable playback auto-subtitling")),
			(_("Primary playback subtitle language")            , config.plugins.moviecockpit.sublang1                  , None                  , None                  , 1     , [-1]        , _("Help Primary playback subtitle language")),
			(_("Secondary playback subtitle language")          , config.plugins.moviecockpit.sublang2                  , None                  , None                  , 1     , [-2]        , _("Help Secondary playback subtitle language")),
			(_("Tertiary playback subtitle language")           , config.plugins.moviecockpit.sublang3                  , None                  , None                  , 1     , [-3]        , _("Help Tertiary playback subtitle language")),
			(_("Enable playback auto-language selection")       , config.plugins.moviecockpit.autoaudio                 , None                  , None                  , 1     , []          , _("Help Enable playback auto-language selection")),
			(_("Enable playback AC3-track first")               , config.plugins.moviecockpit.autoaudio_ac3             , None                  , None                  , 1     , [-1]        , _("Help Enable playback AC3-track first")),
			(_("Primary playback audio language")               , config.plugins.moviecockpit.audlang1                  , None                  , None                  , 1     , [-2]        , _("Help Primary playback audio language")),
			(_("Secondary playback audio language")             , config.plugins.moviecockpit.audlang2                  , None                  , None                  , 1     , [-3]        , _("Help Secondary playback audio language")),
			(_("Tertiary playback audio language")              , config.plugins.moviecockpit.audlang3                  , None                  , None                  , 1     , [-4]        , _("Help Tertiary playback audio language")),
			(self.section                                       , _("DEBUG")                                            , None                  , None                  , 1     , []          , ""),
			(_("Debug log")                                     , config.plugins.moviecockpit.debug                     , self.setDebugMode     , None                  , 0     , []          , _("Help Debug")),
			(_("Log file path")                                 , config.plugins.moviecockpit.debug_log_path            , self.validatePath     , self.openLocationBox  , 0     , [-1]        , _("Help Log file path")),
		]

	def handleInputHelpers(self):
		self["VirtualKB"].setEnabled(False)
		if self["config"].getCurrent():
			if isinstance(self['config'].getCurrent()[1], (ConfigPassword, ConfigText)):
				self["VirtualKB"].setEnabled(True)
				if hasattr(self, "HelpWindow"):
					if self["config"].getCurrent()[1].help_window.instance:
						helpwindowpos = self["HelpWindow"].getPosition()
						self["config"].getCurrent()[1].help_window.instance.move(ePoint(helpwindowpos[0], helpwindowpos[1]))

	def keyText(self):
		self.session.openWithCallback(self.VirtualKeyBoardCallback, VirtualKeyBoard, title=self["config"].getCurrent()[0], text=self["config"].getCurrent()[1].getValue())

	def VirtualKeyBoardCallback(self, callback=None):
		if callback:
			self["config"].getCurrent()[1].setValue(callback)
			self["config"].invalidate(self["config"].getCurrent())

	def keySave(self):
		for x in self["config"].list:
			if len(x) > 1:
				x[1].save()
		self.close()

	def cancelConfirm(self, answer):
		if answer:
			for x in self["config"].list:
				if len(x) > 1:
					x[1].cancel()
			self.close()

	def keyCancel(self):
		if self["config"].isChanged():
			self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"))
		else:
			self.close()

	def bouquetPlus(self):
		self["config"].jumpToPreviousSection()

	def bouquetMinus(self):
		self["config"].jumpToNextSection()

	def createConfig(self):
		self.list = []
		for i, conf in enumerate(self.MVCConfig):
			# 0 entry text
			# 1 variable
			# 2 validation
			# 3 pressed ok
			# 4 setup level
			# 5 parent entries
			# 6 help text
			# Config item must be valid for current usage setup level
			if config.usage.setup_level.index >= conf[4]:
				# Parent entries must be true
				for parent in conf[5]:
					if parent < 0:
						if not self.MVCConfig[i + parent][1].value:
							break
					elif parent > 0:
						if self.MVCConfig[i - parent][1].value:
							break
				else:
					# Loop fell through without a break
					if conf[0] == self.section:
						if len(self.list) > 1:
							self.list.append(getConfigListEntry("", config.plugins.moviecockpit.fake_entry, None, None, 0, [], ""))
						if conf[1] == "":
							self.list.append(getConfigListEntry("<DUMMY CONFIGSECTION>",))
						else:
							self.list.append(getConfigListEntry(conf[1],))
					else:
						self.list.append(getConfigListEntry(conf[0], conf[1], conf[2], conf[3], conf[4], conf[5], conf[6]))
		self["config"].setList(self.list)
		self.setTitle(_("Setup"))

	def loadDefaultSettings(self):
		self.session.openWithCallback(
			self.loadDefaultSettingsCallback,
			MessageBox,
			_("Loading default settings will overwrite all settings, really load them?"),
			MessageBox.TYPE_YESNO
		)

	def loadDefaultSettingsCallback(self, answer):
		if answer:
			# Refresh is done implicitly on change
			for conf in self.MVCConfig:
				if len(conf) > 1 and conf[0] != self.section:
					conf[1].value = conf[1].default
			self.createConfig()

	def changedEntry(self, _addNotifier=None):
		if self.reloadTimer.isActive():
			self.reloadTimer.stop()
		self.reloadTimer.start(50, True)

	def updateHelp(self):
		cur = self["config"].getCurrent()
		self["help"].text = (cur[6] if cur else '')

	def dirSelected(self, res):
		if res:
			res = os.path.normpath(res)
			self["config"].getCurrent()[1].value = res

	def keyOK(self):
		try:
			current = self["config"].getCurrent()
			if current:
				current[3](current[1])
		except Exception:
			print("MVC-E: ConfigScreen: keyOK: function execution failed")

	def keySaveNew(self):
		for i, entry in enumerate(self.list):
			if len(entry) > 1:
				if entry[1].isChanged():
					if entry[2]:
						# execute value changed -function
						if not entry[2](entry[1]):
							print("MVC-E: ConfigScreen: keySaveNew: function called on save failed")
							# Stop exiting, user has to correct the config
							return
					# Check parent entries
					for parent in entry[5]:
						try:
							if self.list[i + parent][2]:
								# execute parent value changed -function
								if self.list[i + parent][2](self.MVCConfig[i + parent][1]):
									# Stop exiting, user has to correct the config
									return
						except Exception as e:
							print("MVC-E: ConfigScreen: keySaveNew: i: %s, exception: %s" % (i, e))
							continue
					entry[1].save()
		configfile.save()

		if self.needs_restart_flag:
			self.restartGUI()
		else:
			self.close(True)

	def restartGUI(self):
		self.session.openWithCallback(self.restartGUIConfirmed, MessageBox, _("Some changes require a GUI restart") + "\n" + _("Restart GUI now?"), MessageBox.TYPE_YESNO)

	def restartGUIConfirmed(self, answer):
		if answer:
			self.session.open(TryQuitMainloop, 3)
		else:
			self.close(True)

	def setDebugMode(self, element):
		#print("MVC: ConfigScreen: setDebugMode: element: %s" % element.value)
		py_files = resolveFilename(SCOPE_PLUGINS, "Extensions/MovieCockpit/*.py")
		if element.value:
			cmd = "sed -i 's/#print(\"MVC:/print(\"MVC:/g' " + py_files
			#print("MVC: ConfigScreen: setDebugMode: cmd: %s" % cmd)
			os.system(cmd)
		else:
			cmd = "sed -i 's/print(\"MVC:/#print(\"MVC:/g' " + py_files
			#print("MVC: ConfigScreen: setDebugMode: cmd: %s" % cmd)
			os.system(cmd)
			cmd = "sed -i 's/##print(\"MVC:/#print(\"MVC:/g' " + py_files
			#print("MVC: ConfigScreen: setDebugMode: cmd: %s" % cmd)
			os.system(cmd)
		self.needsRestart()

	@staticmethod
	def setEPGLanguage(_element=None):
		if config.plugins.moviecockpit.epglang.value:
			#print("MVC: ConfigScreen: setEPGLanguage: %s" % config.plugins.moviecockpit.epglang.value)
			eServiceEvent.setEPGLanguage(config.plugins.moviecockpit.epglang.value)
		return True

	def activateTrashcan(self, element):
		if element.value:
			rc = Trashcan.getInstance().enableTrashcan()
			if rc:
				msg = _("Cannot create trashcan") + "\n" + _("Check mounts and permissions")
				self.session.open(MessageBox, msg, MessageBox.TYPE_INFO, 10)
				return False
			config.plugins.moviecockpit.trashcan_enable.save()
		return True

	def needsRestart(self, _element=None):
		self.needs_restart_flag = True
		return True

	def openLocationBox(self, element):
		if element:
			path = os.path.normpath(element.value)
			self.session.openWithCallback(
				self.dirSelected,
				LocationBox,
				windowTitle=_("Select location"),
				text=_("Select directory"),
				currDir=path + "/",
				bookmarks=config.movielist.videodirs,
				autoAdd=False,
				editDir=True,
				inhibitDirs=["/bin", "/boot", "/dev", "/etc", "/lib", "/proc", "/sbin", "/sys", "/var"],
				minFree=100
			)

	def showInfo(self, _element=None):
		self.session.open(MessageBox, "MovieCockpit" + ": Version " + VERSION, MessageBox.TYPE_INFO)

	def validatePath(self, element):
		element.value = os.path.normpath(element.value)
		if not os.path.exists(element.value):
			self.session.open(MessageBox, _("Path does not exist") + ": " + str(element.value), MessageBox.TYPE_ERROR)
			return False
		return True

	def openStyles(self):
		self.session.open(StylesScreen)
