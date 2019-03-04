# encoding: utf-8
#
# Copyright (C) 2011 by Coolman & Swiss-MAD
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
from Components.config import config, ConfigText, ConfigNumber, ConfigSelection, ConfigSelectionNumber, ConfigYesNo, ConfigSubsection, ConfigNothing, NoSave
from Components.Language import language
from Tools.ISO639 import ISO639Language
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


choices_launch_key = [
	("None",		_("No override")),
	("showMovies",		_("Video-button")),
	("showTv",		_("TV-button")),
	("showRadio",		_("Radio-button")),
	("openQuickbutton",	_("Quick-button")),
	("startTimeshift",	_("Timeshift-button"))
]


# Date format is implemented using datetime.strftime
choices_date = [
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


choices_dir_info = [
	("",	_("off")),
	("D",	_("Description")),	# Description
	("C",	_("(#)")),		# Count
	("CS",	_("(#/GB)")),		# Count/Size
	("S",	_("(GB)"))		# Size
]


choices_move = [
	("d", _("down")),
	("b", _("up/down")),
	("o", _("off"))
]


choices_bqt = [
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


choices_sort = [(k, v[1]) for k, v in sort_modes.items()]
sort_values = [v[0] for v in sort_modes.values()]


choices_skin_layout = [
	("MVCSelection", _("Standard")),
	("MVCSelectionPIG", _("Mini-TV")),
	("MVCSelectionCover", _("Cover"))
]


choices_color_recording = [
	("#ff1616", _("Red")),
	("#ff3838", _("Light red")),
	("#8B0000", _("Dark red"))
]


choices_color_selection = [
	("#ffffff", _("White")),
	("#cccccc", _("Light grey")),
	("#bababa", _("Grey")),
	("#666666", _("Dark grey")),
	("#000000", _("Black"))
]


choices_color_mark = [
	("#cccc00", _("Dark yellow")),
	("#ffff00", _("Yellow"))
] + choices_color_selection


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
		#print("MVC: ConfigInit: __init__")
		config.MVC                           = ConfigSubsection()
		config.MVC.fake_entry                = NoSave(ConfigNothing())
		config.MVC.plugin_extmenu_settings   = ConfigYesNo(default=True)
		config.MVC.plugin_extmenu_plugin     = ConfigYesNo(default=True)
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
		config.MVC.plugin_disable            = ConfigYesNo(default=False)
		config.MVC.list_start_home           = ConfigYesNo(default=True)
		config.MVC.movie_description_delay   = ConfigNumber(default=200)
		config.MVC.cover                     = ConfigYesNo(default=False)
		config.MVC.cover_flash               = ConfigYesNo(default=False)
		config.MVC.cover_bookmark            = ConfigText(default="/data/movie", fixed_size=False, visible_width=22)
		config.MVC.cover_fallback            = ConfigYesNo(default=False)
		config.MVC.cover_replace_existing    = ConfigYesNo(default=False)
		config.MVC.cover_auto_download       = ConfigYesNo(default=False)
		config.MVC.cover_language            = ConfigSelection(default='de', choices=[('en', _('English')), ('de', _('German')), ('it', _('Italian')), ('es', _('Spanish')), ('fr', _('French')), ('pt', _('Portuguese'))])
		config.MVC.cover_size                = ConfigSelection(default="w500", choices=["w92", "w185", "w500", "original"])
		config.MVC.mini_tv                   = ConfigYesNo(default=False)
		config.MVC.movie_mountpoints         = ConfigYesNo(default=False)
		config.MVC.movie_picons_path         = ConfigText(default="/usr/share/enigma2/picon", fixed_size=False, visible_width=35)
		config.MVC.movie_watching_percent    = ConfigSelectionNumber(0, 30, 1, default=10)
		config.MVC.movie_finished_percent    = ConfigSelectionNumber(50, 100, 1, default=90)
		config.MVC.movie_date_format         = ConfigSelection(default="%d.%m.%Y %H:%M", choices=choices_date)
		config.MVC.movie_ignore_firstcuts    = ConfigYesNo(default=True)
		config.MVC.movie_jump_first_mark     = ConfigYesNo(default=False)
		config.MVC.record_eof_zap            = ConfigSelection(default='1', choices=[('0', _("yes, without Message")), ('1', _("yes, with Message")), ('2', _("no"))])
		config.MVC.trashcan_enable           = ConfigYesNo(default=False)
		config.MVC.trashcan_show             = ConfigYesNo(default=True)
		config.MVC.trashcan_info             = ConfigSelection(default="C", choices=choices_dir_info)
		config.MVC.trashcan_clean            = ConfigYesNo(default=True)
		config.MVC.trashcan_retention        = ConfigNumber(default=3)
		config.MVC.directories_show          = ConfigYesNo(default=False)
		config.MVC.directories_ontop         = ConfigYesNo(default=False)
		config.MVC.directories_info          = ConfigSelection(default="", choices=choices_dir_info)
		config.MVC.color                     = ConfigSelection(default="#bababa", choices=choices_color_selection)
		config.MVC.color_sel                 = ConfigSelection(default="#ffffff", choices=choices_color_selection)
		config.MVC.recording_color           = ConfigSelection(default="#ff1616", choices=choices_color_recording)
		config.MVC.recording_color_sel       = ConfigSelection(default="#ff3838", choices=choices_color_recording)
		config.MVC.selection_color           = ConfigSelection(default="#cccc00", choices=choices_color_mark)
		config.MVC.selection_color_sel       = ConfigSelection(default="#ffff00", choices=choices_color_mark)
		config.MVC.list_sort                 = ConfigSelection(default=("D-"), choices=choices_sort)
		config.MVC.list_selmove              = ConfigSelection(default="d", choices=choices_move)
		config.MVC.list_style                = ConfigNumber(default=1)
		config.MVC.timer_autoclean           = ConfigYesNo(default=False)
		config.MVC.plugin_launch_key         = ConfigSelection(default="showMovies", choices=choices_launch_key)
		config.MVC.list_bouquet_keys         = ConfigSelection(default="", choices=choices_bqt)
		config.MVC.list_skip_size            = ConfigSelectionNumber(3, 10, 1, default=5)
		config.MVC.skin_layout               = ConfigSelection(default="MVCSelection", choices=choices_skin_layout)
		config.MVC.disk_space_info           = ConfigText(default="", fixed_size=False, visible_width=0)
		config.MVC.debug                     = ConfigYesNo(default=False)
		config.MVC.debug_log_path            = ConfigText(default="/media/hdd", fixed_size=False, visible_width=35)

		self.checkList(config.MVC.epglang)
		self.checkList(config.MVC.sublang1)
		self.checkList(config.MVC.sublang2)
		self.checkList(config.MVC.sublang3)
		self.checkList(config.MVC.audlang1)
		self.checkList(config.MVC.audlang2)
		self.checkList(config.MVC.audlang3)
