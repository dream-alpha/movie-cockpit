# encoding: utf-8
#
# Copyright (C) 2011 by Coolman & Swiss-MAD
#               2018 by dream-alpha
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
from Components.config import config, ConfigText, ConfigSelection, ConfigSelectionNumber, ConfigYesNo, ConfigSubsection, ConfigNothing, NoSave
from Components.Language import language
from Tools.ISO639 import ISO639Language
from enigma import RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER
from MountPoints import MountPoints


class Autoselect639Language(ISO639Language, object):

	def __init__(self):
		ISO639Language.__init__(self, self.TERTIARY)

	def getTranslatedChoicesDictAndSortedListAndDefaults(self):
		syslang = language.getLanguage()[:2]
		choices_dict = {}
		choices_list = []
		defaults = []
		for lang, id_list in self.idlist_by_name.iteritems():
			if syslang not in id_list and 'en' not in id_list:
				name = _(lang)
				short_id = sorted(id_list, key=len)[0]
				choices_dict[short_id] = name
				choices_list.append((short_id, name))
		choices_list.sort(key=lambda x: x[1])
		syslangname = _(self.name_by_shortid[syslang])
		choices_list.insert(0, (syslang, syslangname))
		choices_dict[syslang] = syslangname
		defaults.append(syslang)
		if syslang != "en":
			enlangname = _(self.name_by_shortid["en"])
			choices_list.insert(1, ("en", enlangname))
			choices_dict["en"] = enlangname
			defaults.append("en")
		return (choices_dict, choices_list, defaults)


def langList():
	iso639 = Autoselect639Language()
	newlist = iso639.getTranslatedChoicesDictAndSortedListAndDefaults()[1]
	return newlist


def langListSel():
	iso639 = Autoselect639Language()
	newlist = iso639.getTranslatedChoicesDictAndSortedListAndDefaults()[0]
	return newlist


launch_choices = [
	("None",		_("No override")),
	("showMovies",		_("Video-button")),
	("showTv",		_("TV-button")),
	("showRadio",		_("Radio-button")),
	("openQuickbutton",	_("Quick-button")),
	("startTimeshift",	_("Timeshift-button"))
]


# Date format is implemented using datetime.strftime
date_choices = [
	("%d.%m.%Y",		_("DD.MM.YYYY")),
	("%a %d.%m.%Y",		_("WD DD.MM.YYYY")),

	("%d.%m.%Y %H:%M",	_("DD.MM.YYYY HH:MM")),
	("%a %d.%m.%Y %H:%M",	_("WD DD.MM.YYYY HH:MM")),

	("%d.%m. %H:%M",	_("DD.MM. HH:MM")),
	("%a %d.%m. %H:%M",	_("WD DD.MM. HH:MM")),

	("%Y/%m/%d",		_("YYYY/MM/DD")),
	("%a %Y/%m/%d",		_("WD YYYY/MM/DD")),

	("%Y/%m/%d %H:%M",	_("YYYY/MM/DD HH:MM")),
	("%a %Y/%m/%d %H:%M",	_("WD YYYY/MM/DD HH:MM")),

	("%m/%d %H:%M",		_("MM/DD HH:MM")),
	("%a %m/%d %H:%M",	_("WD MM/DD HH:MM"))
]


dirinfo_choices = [
	("",	_("off")),
	("D",	_("Description")),	# Description
	("C",	_("(#)")),		# Count
	("CS",	_("(#/GB)")),		# Count/Size
	("S",	_("(GB)"))		# Size
]


progress_choices = [
	("PB",	_("Progress Bar")),
	("P",	_("Percent (%)")),
	("",	_("off"))
]


# key indexes
KEY_RED_SHORT = 0
KEY_RED_LONG = 1
KEY_GREEN_SHORT = 2
KEY_GREEN_LONG = 3
KEY_YELLOW_SHORT = 4
KEY_YELLOW_LONG = 5
KEY_BLUE_SHORT = 6
KEY_BLUE_LONG = 7
KEY_INFO_SHORT = 8
KEY_INFO_LONG = 9

# indexes for function_key_choices
KEY_FUNC_HOME = 0
KEY_FUNC_DELETE = 1
KEY_FUNC_MOVE = 2
KEY_FUNC_COVER_SEARCH = 3
KEY_FUNC_COPY = 4
KEY_FUNC_BOOKMARKS = 5
KEY_FUNC_TOGGLE_COVER = 6
KEY_FUNC_SORT_MODE = 7
KEY_FUNC_SORT_ORDER = 8
KEY_FUNC_EVENT_INFO = 9
KEY_FUNC_TMDB_INFO = 10
KEY_FUNC_DISABLED = 11


function_key_names = [
	_("Home"),
	_("Delete"),
	_("Move"),
	_("Cover Search"),
	_("Copy"),
	_("Bookmarks"),
	_("Cover on/off"),
	_("Sort Mode"),
	_("Sort Order"),
	_("EPG info"),
	_("TMDB info"),
	_("disabled"),
]


function_key_choices = [(str(i), key_name) for i, key_name in enumerate(function_key_names)]


move_choices = [
	("d", _("down")),
	("b", _("up/down")),
	("o", _("off"))
]


bqt_choices = [
	("", 		_("Home/End")),
	("Skip", 	_("Skip")),
	("Folder", 	_("Change Folder"))
]


sort_modes = {
	("D-"): (("D", False),	_("Date sort down")),
	("AZ"): (("A", False),	_("Alpha sort up")),
	("D+"): (("D", True), 	_("Date sort up")),
	("ZA"): (("A", True),	_("Alpha sort down"))
}


sort_choices = [(k, v[1]) for k, v in sort_modes.items()]
sort_values = [v[0] for v in sort_modes.values()]


class ConfigInit(MountPoints, object):

	def checkList(self, cfg):
		for choices in cfg.choices.choices:
			if cfg.value == choices[0]:
				return
		for choices in cfg.choices.choices:
			if cfg.default == choices[0]:
				cfg.value = cfg.default
				return
		cfg.value = cfg.choices.choices[0][0]

	def __init__(self):
		print("MVC: ConfigInit: __init__")
		config.MVC                           = ConfigSubsection()
		config.MVC.fake_entry                = NoSave(ConfigNothing())
		config.MVC.extmenu_plugin            = ConfigYesNo(default=True)
		config.MVC.extmenu_list              = ConfigYesNo(default=True)
		config.MVC.epglang                   = ConfigSelection(default=language.getActiveLanguage(), choices=langList())
		config.MVC.sublang1                  = ConfigSelection(default=language.lang[language.getActiveLanguage()][0], choices=langList())
		config.MVC.sublang2                  = ConfigSelection(default=language.lang[language.getActiveLanguage()][0], choices=langList())
		config.MVC.sublang3                  = ConfigSelection(default=language.lang[language.getActiveLanguage()][0], choices=langList())
		config.MVC.audlang1                  = ConfigSelection(default=language.lang[language.getActiveLanguage()][0], choices=langList())
		config.MVC.audlang2                  = ConfigSelection(default=language.lang[language.getActiveLanguage()][0], choices=langList())
		config.MVC.audlang3                  = ConfigSelection(default=language.lang[language.getActiveLanguage()][0], choices=langList())
		config.MVC.autosubs                  = ConfigYesNo(default=False)
		config.MVC.autoaudio                 = ConfigYesNo(default=False)
		config.MVC.autoaudio_ac3             = ConfigYesNo(default=False)
		config.MVC.ml_disable                = ConfigYesNo(default=False)
		config.MVC.movie_shortredfunc        = ConfigSelection(default=str(KEY_FUNC_DELETE), choices=function_key_choices)
		config.MVC.movie_shortgreenfunc      = ConfigSelection(default=str(KEY_FUNC_SORT_MODE), choices=function_key_choices)
		config.MVC.movie_shortyellowfunc     = ConfigSelection(default=str(KEY_FUNC_MOVE), choices=function_key_choices)
		config.MVC.movie_shortbluefunc       = ConfigSelection(default=str(KEY_FUNC_HOME), choices=function_key_choices)
		config.MVC.movie_longgreenfunc       = ConfigSelection(default=str(KEY_FUNC_SORT_ORDER), choices=function_key_choices)
		config.MVC.movie_longredfunc         = ConfigSelection(default=str(KEY_FUNC_DELETE), choices=function_key_choices)
		config.MVC.movie_longyellowfunc      = ConfigSelection(default=str(KEY_FUNC_MOVE), choices=function_key_choices)
		config.MVC.movie_longbluefunc        = ConfigSelection(default=str(KEY_FUNC_HOME), choices=function_key_choices)
		config.MVC.movie_longinfofunc        = ConfigSelection(default=str(KEY_FUNC_TMDB_INFO), choices=function_key_choices)
		config.MVC.movie_shortinfofunc       = ConfigSelection(default=str(KEY_FUNC_EVENT_INFO), choices=function_key_choices)
		config.MVC.start_home                = ConfigYesNo(default=True)
		config.MVC.movie_description_delay   = ConfigSelectionNumber(50, 60000, 50, default=200)
		config.MVC.cover                     = ConfigYesNo(default=False)
		config.MVC.cover_flash               = ConfigYesNo(default=False)
		config.MVC.cover_bookmark            = ConfigText(default="/data/movie", fixed_size=False, visible_width=22)
		config.MVC.cover_fallback            = ConfigYesNo(default=False)
		config.MVC.cover_replace_existing    = ConfigYesNo(default=False)
		config.MVC.cover_auto_download       = ConfigYesNo(default=False)
		config.MVC.cover_language            = ConfigSelection(default='de', choices=[('en', _('English')), ('de', _('German')), ('it', _('Italian')), ('es', _('Spanish')), ('fr', _('French')), ('pt', _('Portuguese'))])
		config.MVC.cover_size                = ConfigSelection(default="w185", choices=["w92", "w185", "w500", "original"])
		config.MVC.mini_tv                   = ConfigYesNo(default=False)
		config.MVC.movie_icons               = ConfigYesNo(default=True)
		config.MVC.link_icons                = ConfigYesNo(default=True)
		config.MVC.movie_mountpoints         = ConfigYesNo(default=False)
		config.MVC.movie_picons              = ConfigYesNo(default=False)
		config.MVC.movie_picons_path         = ConfigText(default="/usr/share/enigma2/picon", fixed_size=False, visible_width=35)
		config.MVC.movie_progress            = ConfigSelection(default="PB", choices=progress_choices)
		config.MVC.movie_watching_percent    = ConfigSelectionNumber(0, 30, 1, default=10)
		config.MVC.movie_finished_percent    = ConfigSelectionNumber(50, 100, 1, default=90)
		config.MVC.movie_date_format         = ConfigSelection(default="%d.%m.%Y %H:%M", choices=date_choices)
		config.MVC.movie_ignore_firstcuts    = ConfigYesNo(default=True)
		config.MVC.movie_jump_first_mark     = ConfigYesNo(default=False)
		config.MVC.movie_rewind_finished     = ConfigYesNo(default=True)
		config.MVC.record_eof_zap            = ConfigSelection(default='1', choices=[('0', _("yes, without Message")), ('1', _("yes, with Message")), ('2', _("no"))])
		config.MVC.movie_real_path           = ConfigYesNo(default=True)
		config.MVC.movie_homepath            = ConfigText(default="/media/hdd/movie", fixed_size=False, visible_width=22)
		config.MVC.movie_trashcan_enable     = ConfigYesNo(default=True)
		config.MVC.movie_trashcan_show       = ConfigYesNo(default=True)
		config.MVC.movie_trashcan_info       = ConfigSelection(default="C", choices=dirinfo_choices)
		config.MVC.movie_trashcan_clean      = ConfigYesNo(default=True)
		config.MVC.movie_trashcan_retention   = ConfigSelectionNumber(1, 99, 1, default=3)
		config.MVC.movie_delete_validation   = ConfigYesNo(default=True)
		config.MVC.directories_show          = ConfigYesNo(default=False)
		config.MVC.directories_ontop         = ConfigYesNo(default=False)
		config.MVC.directories_info          = ConfigSelection(default="", choices=dirinfo_choices)
		config.MVC.datetext_alignment        = ConfigSelection(default=RT_HALIGN_CENTER, choices=[(RT_HALIGN_CENTER, _("center")), (RT_HALIGN_RIGHT, _("right")), (RT_HALIGN_LEFT, _("left"))])
		config.MVC.color_recording           = ConfigSelection(default="#ff0000", choices=[("#ffff00", _("Yellow")), ("#ff0000", _("Red")), ("#ff9999", _("Light red")), ("#990000", _("Dark red"))])
		config.MVC.color_highlight           = ConfigSelection(default="#ffffff", choices=[("#ffffff", _("White")), ("#cccccc", _("Light grey")), ("#bababa", _("Grey")), ("#666666", _("Dark grey")), ("#000000", _("Black"))])
		config.MVC.bookmarks                 = ConfigYesNo(default=False)
		config.MVC.movie_hide_move           = ConfigYesNo(default=False)
		config.MVC.movie_hide_delete         = ConfigYesNo(default=False)
		config.MVC.movie_hide_copy           = ConfigYesNo(default=False)
		config.MVC.movie_sort                = ConfigSelection(default=("D-"), choices=sort_choices)
		config.MVC.moviecenter_selmove       = ConfigSelection(default="d", choices=move_choices)
		config.MVC.timer_autoclean           = ConfigYesNo(default=False)
		config.MVC.movie_launch              = ConfigSelection(default="showMovies", choices=launch_choices)
		config.MVC.bqt_keys                  = ConfigSelection(default="", choices=bqt_choices)
		config.MVC.list_skip_size            = ConfigSelectionNumber(3, 10, 1, default=5)
		config.MVC.disk_space_info           = ConfigText(default="", fixed_size=False, visible_width=0)

		self.checkList(config.MVC.epglang)
		self.checkList(config.MVC.sublang1)
		self.checkList(config.MVC.sublang2)
		self.checkList(config.MVC.sublang3)
		self.checkList(config.MVC.audlang1)
		self.checkList(config.MVC.audlang2)
		self.checkList(config.MVC.audlang3)
