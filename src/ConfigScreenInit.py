# coding=utf-8
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

from Debug import logger
from __init__ import _
from enigma import eServiceEvent
from Components.config import config, ConfigText
from ConfigStylesScreenInit import ConfigStylesScreenInit


class ConfigScreenInit(ConfigStylesScreenInit):
	def __init__(self, session):
		logger.info("...")
		ConfigStylesScreenInit.__init__(self, session)

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
		self.config_list = [
			(self.section                                       , _("GENERAL")                                          , None                  , None                  , 0     , []          , ""),
			(_("Start plugin with key")                         , config.plugins.moviecockpit.launch_key                , self.needsRestart     , None                  , 0     , []          , _("Select the key that will invoke the plugin.")),
			(_("Show settings in extensions menu")              , config.plugins.moviecockpit.extmenu_settings          , self.needsRestart     , None                  , 0     , []          , _("Select whether to show the configuration screen in the extensions menu.")),
			(_("Show plugin in extensions menu")                , config.plugins.moviecockpit.extmenu_plugin            , self.needsRestart     , None                  , 0     , []          , _("Select whether the plugin is to be shown in the extensions menu.")),
			(_("Video home at start")                           , config.plugins.moviecockpit.list_start_home           , None                  , None                  , 0     , []          , _("Select whether Video home is to be displayed at plugin start or the last directory.")),
			(_("Default sort mode")                             , config.plugins.moviecockpit.list_sort                 , None                  , None                  , 0     , []          , _("Select the start mode to be used at startup.")),
			(self.section                                       , _("KEYS")                                             , None                  , None                  , 0     , []          , ""),
			(_("Bouquet buttons behavior")                      , config.plugins.moviecockpit.list_bouquet_keys         , None                  , None                  , 0     , []          , _("Select the behavior of the bouquet buttons in the configuration menu.")),
			(_("List entries to skip")                          , config.plugins.moviecockpit.list_skip_size            , None                  , None                  , 0     , []          , _("Select the number of list entries to be skipped.")),
			(self.section                                       , _("PLAYBACK")                                         , None                  , None                  , 0     , []          , ""),
			(_("No resume below 10 seconds")                    , config.plugins.moviecockpit.movie_ignore_first_marks  , None                  , None                  , 1     , []          , _("Select whether whether the resume dialog should be displayed for elapse times smaller than 10 seconds.")),
			(_("Resume video at last position")                 , config.plugins.moviecockpit.movie_resume_at_last_pos  , None                  , None                  , 1     , []          , _("Select whether video should be resumed at last stop position.")),
			(_("Video start at")                                , config.plugins.moviecockpit.movie_start_position      , None                  , None                  , 1     , []          , _("Select at which position video is started at.")),
			(_("Zap to live TV of recording")                   , config.plugins.moviecockpit.record_eof_zap            , None                  , None                  , 1     , []          , _("Select whether to switch to TV channel when a time-shifted video reaches the end.")),
			(_("Automatic timers list cleaning")                , config.plugins.moviecockpit.timer_autoclean           , None                  , None                  , 1     , []          , _("Select whether covers should be downloaded automatically for recordings.")),
			(self.section                                       , _("DISPLAY")                                          , None                  , None                  , 0     , []          , ""),
			(_("Show directories")                              , config.plugins.moviecockpit.directories_show          , None                  , None                  , 0     , []          , _("Select whether directories should be displayed.")),
			(_("Show directories within video list")            , config.plugins.moviecockpit.directories_ontop         , None                  , None                  , 0     , [-1]        , _("Select whether directories should be displayed within video list.")),
			(_("Show directories information")                  , config.plugins.moviecockpit.directories_info          , None                  , None                  , 0     , [-2]        , _("Select which information should be displayed for directories.")),
			(self.section                                       , _("SKIN")                                             , None                  , None                  , 0     , []          , ""),
			(_("Show mount points")                             , config.plugins.moviecockpit.movie_mount_points        , None                  , None                  , 0     , []          , _("Select whether to show mount_points or not.")),
			(_("Date format")                                   , config.plugins.moviecockpit.movie_date_format         , None                  , None                  , 0     , []          , _("Select the date format.")),
			(_("Path to recording picons")                      , config.plugins.moviecockpit.movie_picons_path         , self.validatePath     , None                  , 0     , []          , _("Select the recording picon path.")),
			(_("Watching in progress percent")                  , config.plugins.moviecockpit.movie_watching_percent    , None                  , None                  , 0     , []          , _("Select percentage for videos that areconsidered being watched.")),
			(_("Finished watching percent")                     , config.plugins.moviecockpit.movie_finished_percent    , None                  , None                  , 0     , []          , _("Select percentage for videos that areconsidered finished.")),
			(_("Default color for video")                       , config.plugins.moviecockpit.color                     , None                  , None                  , 0     , []          , _("Select the color for video.")),
			(_("Default color for highlighted video")           , config.plugins.moviecockpit.color_sel                 , None                  , None                  , 0     , []          , _("Select the color for videos that are highlighted.")),
			(_("Default color for recording")                   , config.plugins.moviecockpit.recording_color           , None                  , None                  , 0     , []          , _("Select the color for recording.")),
			(_("Default color for highlighted recording")       , config.plugins.moviecockpit.recording_color_sel       , None                  , None                  , 0     , []          , _("Select the color for highlighted recording.")),
			(_("Default color for selected video")              , config.plugins.moviecockpit.selection_color           , None                  , None                  , 0     , []          , _("Select the color for selected video.")),
			(_("Default color for highlighted selected video")  , config.plugins.moviecockpit.selection_color_sel       , None                  , None                  , 0     , []          , _("Select the color for selected and highlighted video.")),
		]
		self.config_list += self.createConfigListEntries()
		self.config_list += [
			(self.section                                       , _("VIDEO-COVER")                                      , None                  , None                  , 0     , []          , ""),
			(_("Show fallback cover")                           , config.plugins.moviecockpit.cover_fallback            , None                  , None                  , 0     , []          , _("Select whether a \"no cover available\" cover should be displayed when no cover is available.")),
			(_("Search cover language")                         , config.plugins.moviecockpit.cover_language            , None                  , None                  , 0     , []          , _("Select the preferred language for cover search.")),
			(_("Search cover size")                             , config.plugins.moviecockpit.cover_size                , None                  , None                  , 0     , []          , _("Select the size that should be used for cover download.")),
			(_("Search backdrop size")                          , config.plugins.moviecockpit.backdrop_size             , None                  , None                  , 0     , []          , _("Select the size for backdrop download.")),
			(_("Download replace existing cover")               , config.plugins.moviecockpit.cover_replace_existing    , None                  , None                  , 0     , []          , _("Select whether existing covers should be replaced or not.")),
			(_("Download cover to flash")                       , config.plugins.moviecockpit.cover_flash               , None                  , None                  , 0     , []          , _("Select whether covers should be stored in flash storage.")),
			(_("Download cover bookmark")                       , config.plugins.moviecockpit.cover_bookmark            , self.validatePath     , None                  , 0     , [-1]        , _("Select the mount point where the covers are to be stored.")),
			(_("Download cover automatically for recording")    , config.plugins.moviecockpit.cover_auto_download       , None                  , None                  , 0     , []          , _("Select whether a cover should be automatically downloaded when recording a movie.")),
			(self.section                                       , _("TRASHCAN")                                         , None                  , None                  , 0     , []          , ""),
			(_("Enable trashcan")                               , config.plugins.moviecockpit.trashcan_enable           , None                  , None                  , 0     , []          , _("Select whether the trashcan should be activated.")),
			(_("Show trashcan directory")                       , config.plugins.moviecockpit.trashcan_show             , None                  , None                  , 0     , [-1]        , _("Select whether the trashcan should be displayed in the video list.")),
			(_("Show trashcan information")                     , config.plugins.moviecockpit.trashcan_info             , None                  , None                  , 0     , [-2, -1]    , _("Select the trashcan information to be shown.")),
			(_("Enable auto trashcan cleanup")                  , config.plugins.moviecockpit.trashcan_clean            , None                  , None                  , 0     , [-3]        , _("Select whether the trashcan should be cleaned automatically .")),
			(_("File retention period in trashcan")             , config.plugins.moviecockpit.trashcan_retention        , None                  , None                  , 0     , [-4, -1]    , _("Select how many days the files should be kept in the trashcan before they are cleaned automatically.")),
			(self.section                                       , _("ARCHIVE")                                          , None                  , None                  , 0     , []          , ""),
			(_("Enable")                                        , config.plugins.moviecockpit.archive_enable            , None                  , None                  , 0     , []          , _("Select whether archiving should be activated.")),
			(_("Source")                                        , config.plugins.moviecockpit.archive_source_dir        , self.validatePath     , self.openLocationBox  , 0     , [-1]        , _("Select the source bookmark for archiving.")),
			(_("Target")                                        , config.plugins.moviecockpit.archive_target_dir        , self.validatePath     , self.openLocationBox  , 0     , [-2]        , _("Select the target bookmark for archiving.")),
			(self.section                                       , _("LANGUAGE")                                         , None                  , None                  , 1     , []          , ""),
			(_("Preferred EPG language")                        , config.plugins.moviecockpit.epglang                   , self.setEPGLanguage, None                     , 1     , []          , _("Select the preferred EPG language.")),
			(_("Enable playback auto-subtitling")               , config.plugins.moviecockpit.autosubs                  , None                  , None                  , 1     , []          , _("Select whether playback auto-subtitling should be enabled.")),
			(_("Primary playback subtitle language")            , config.plugins.moviecockpit.sublang1                  , None                  , None                  , 1     , [-1]        , _("Select the primary playback subtitle language.")),
			(_("Secondary playback subtitle language")          , config.plugins.moviecockpit.sublang2                  , None                  , None                  , 1     , [-2]        , _("Select the secondary playback subtitle language.")),
			(_("Tertiary playback subtitle language")           , config.plugins.moviecockpit.sublang3                  , None                  , None                  , 1     , [-3]        , _("Select the tertiary subtitle language.")),
			(_("Enable playback auto-language selection")       , config.plugins.moviecockpit.autoaudio                 , None                  , None                  , 1     , []          , _("Select whether auto-language selection should be enabled for playback.")),
			(_("Enable playback AC3-track first")               , config.plugins.moviecockpit.autoaudio_ac3             , None                  , None                  , 1     , [-1]        , _("Select whether select the AC3 audio track first.")),
			(_("Primary playback audio language")               , config.plugins.moviecockpit.audlang1                  , None                  , None                  , 1     , [-2]        , _("Select the primary language for audio.")),
			(_("Secondary playback audio language")             , config.plugins.moviecockpit.audlang2                  , None                  , None                  , 1     , [-3]        , _("Select the secondary language for audio.")),
			(_("Tertiary playback audio language")              , config.plugins.moviecockpit.audlang3                  , None                  , None                  , 1     , [-4]        , _("Select the tertiary language for audio.")),
			(self.section                                       , _("MOUNT MANAGER")                                    , None                  , None                  , 2     , []          , ""),
			(_("Enable mount manager")                          , config.plugins.moviecockpit.mount_manager_enabled     , None                  , None                  , 2     , []          , _("Select whether mount manager should be enabled.")),
			(self.section                                       , _("DEBUG")                                            , None                  , None                  , 2     , []          , ""),
			(_("Log level")                                     , config.plugins.moviecockpit.debug_log_level           , self.setLogLevel      , None                  , 2     , []          , _("Select debug log level.")),
			(_("Log file path")                                 , config.plugins.moviecockpit.debug_log_path            , self.validatePath     , None                  , 2     , []          , _("Select the path to be used for the debug log file.")),
		]

	def needsRestart(self, _element):
		return True

	def validatePath(self, _element):
		return True

	def openLocationBox(self, _element):
		return True

	def setLogLevel(self, _element):
		return True

	@staticmethod
	def save(conf):
		if conf.type == "preset":
			config.plugins.moviecockpit.preset = ConfigText()
			config.plugins.moviecockpit.preset.value = conf.value
			config.plugins.moviecockpit.preset.save()
		if conf.type == "style":
			logger.debug("saving key: %s, value: %s", conf.conf_key, conf.value)
			config.plugins.moviecockpit.style[conf.conf_key] = ConfigText()
			config.plugins.moviecockpit.style[conf.conf_key].value = conf.value
			logger.debug("stored_values: %s", str(config.plugins.moviecockpit.style.stored_values))
			config.plugins.moviecockpit.style.save()

	@staticmethod
	def setEPGLanguage(element):
		logger.debug("epglang: %s", element.value)
		eServiceEvent.setEPGLanguage(element.value)
		return True
