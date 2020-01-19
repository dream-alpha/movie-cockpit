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


from __init__ import _
from Components.config import config, ConfigText, ConfigNumber, ConfigSelection, ConfigSelectionNumber, ConfigYesNo, ConfigSubsection,\
	ConfigNothing, NoSave, ConfigSubDict
from Components.Language import language
from Tools.ISO639 import ISO639Language


class Autoselect639Language(ISO639Language):

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
	#print("MVC: ConfigInit: langList: %s" % str(newlist))
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
]


sort_modes = {
	"0": (("date", False),	_("Date sort down")),
	"1": (("date", True), 	_("Date sort up")),
	"2": (("alpha", False),	_("Alpha sort up")),
	"3": (("alpha", True),	_("Alpha sort down"))
}


choices_sort = [(k, v[1]) for k, v in sort_modes.items()]


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


class ConfigInit():

	config = None

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
		config.plugins.moviecockpit                           = ConfigSubsection()
		config.plugins.moviecockpit.fake_entry                = NoSave(ConfigNothing())
		config.plugins.moviecockpit.extmenu_settings          = ConfigYesNo(default=True)
		config.plugins.moviecockpit.extmenu_plugin            = ConfigYesNo(default=True)
		config.plugins.moviecockpit.epglang                   = ConfigSelection(default=language.getActiveLanguage()[:2], choices=langList())
		config.plugins.moviecockpit.sublang1                  = ConfigSelection(default=language.lang[language.getActiveLanguage()][0], choices=langList())
		config.plugins.moviecockpit.sublang2                  = ConfigSelection(default=language.lang[language.getActiveLanguage()][0], choices=langList())
		config.plugins.moviecockpit.sublang3                  = ConfigSelection(default=language.lang[language.getActiveLanguage()][0], choices=langList())
		config.plugins.moviecockpit.audlang1                  = ConfigSelection(default=language.lang[language.getActiveLanguage()][0], choices=langList())
		config.plugins.moviecockpit.audlang2                  = ConfigSelection(default=language.lang[language.getActiveLanguage()][0], choices=langList())
		config.plugins.moviecockpit.audlang3                  = ConfigSelection(default=language.lang[language.getActiveLanguage()][0], choices=langList())
		config.plugins.moviecockpit.autosubs                  = ConfigYesNo(default=False)
		config.plugins.moviecockpit.autoaudio                 = ConfigYesNo(default=False)
		config.plugins.moviecockpit.autoaudio_ac3             = ConfigYesNo(default=False)
		config.plugins.moviecockpit.disable                   = ConfigYesNo(default=False)
		config.plugins.moviecockpit.list_start_home           = ConfigYesNo(default=True)
		config.plugins.moviecockpit.movie_description_delay   = ConfigNumber(default=200)
		config.plugins.moviecockpit.cover_flash               = ConfigYesNo(default=False)
		config.plugins.moviecockpit.cover_bookmark            = ConfigText(default="/data/movie", fixed_size=False, visible_width=22)
		config.plugins.moviecockpit.cover_fallback            = ConfigYesNo(default=False)
		config.plugins.moviecockpit.cover_replace_existing    = ConfigYesNo(default=False)
		config.plugins.moviecockpit.cover_auto_download       = ConfigYesNo(default=False)
		config.plugins.moviecockpit.cover_language            = ConfigSelection(default=language.getActiveLanguage()[:2], choices=langList())
		config.plugins.moviecockpit.cover_size                = ConfigSelection(default="w500", choices=["w92", "w185", "w500", "original"])
		config.plugins.moviecockpit.backdrop_size             = ConfigSelection(default="w1280", choices=["w300", "w780", "w1280", "original"])
		config.plugins.moviecockpit.movie_mountpoints         = ConfigYesNo(default=False)
		config.plugins.moviecockpit.movie_picons_path         = ConfigText(default="/usr/share/enigma2/picon", fixed_size=False, visible_width=35)
		config.plugins.moviecockpit.movie_watching_percent    = ConfigSelectionNumber(0, 30, 1, default=10)
		config.plugins.moviecockpit.movie_finished_percent    = ConfigSelectionNumber(50, 100, 1, default=90)
		config.plugins.moviecockpit.movie_date_format         = ConfigSelection(default="%d.%m.%Y %H:%M", choices=choices_date)
		config.plugins.moviecockpit.movie_ignore_firstcuts    = ConfigYesNo(default=True)
		config.plugins.moviecockpit.movie_jump_first_mark     = ConfigYesNo(default=False)
		config.plugins.moviecockpit.record_eof_zap            = ConfigSelection(default='1', choices=[('0', _("yes, without Message")), ('1', _("yes, with Message")), ('2', _("no"))])
		config.plugins.moviecockpit.trashcan_enable           = ConfigYesNo(default=False)
		config.plugins.moviecockpit.trashcan_show             = ConfigYesNo(default=True)
		config.plugins.moviecockpit.trashcan_info             = ConfigSelection(default="C", choices=choices_dir_info)
		config.plugins.moviecockpit.trashcan_clean            = ConfigYesNo(default=True)
		config.plugins.moviecockpit.trashcan_retention        = ConfigNumber(default=3)
		config.plugins.moviecockpit.directories_show          = ConfigYesNo(default=False)
		config.plugins.moviecockpit.directories_ontop         = ConfigYesNo(default=False)
		config.plugins.moviecockpit.directories_info          = ConfigSelection(default="", choices=choices_dir_info)
		config.plugins.moviecockpit.color                     = ConfigSelection(default="#bababa", choices=choices_color_selection)
		config.plugins.moviecockpit.color_sel                 = ConfigSelection(default="#ffffff", choices=choices_color_selection)
		config.plugins.moviecockpit.recording_color           = ConfigSelection(default="#ff1616", choices=choices_color_recording)
		config.plugins.moviecockpit.recording_color_sel       = ConfigSelection(default="#ff3838", choices=choices_color_recording)
		config.plugins.moviecockpit.selection_color           = ConfigSelection(default="#cccc00", choices=choices_color_mark)
		config.plugins.moviecockpit.selection_color_sel       = ConfigSelection(default="#ffff00", choices=choices_color_mark)
		config.plugins.moviecockpit.list_sort                 = ConfigSelection(default="0", choices=choices_sort)
		config.plugins.moviecockpit.list_selmove              = ConfigSelection(default="d", choices=choices_move)
		config.plugins.moviecockpit.list_style                = ConfigNumber(default=1)
		config.plugins.moviecockpit.timer_autoclean           = ConfigYesNo(default=False)
		config.plugins.moviecockpit.launch_key                = ConfigSelection(default="showMovies", choices=choices_launch_key)
		config.plugins.moviecockpit.list_bouquet_keys         = ConfigSelection(default="", choices=choices_bqt)
		config.plugins.moviecockpit.list_skip_size            = ConfigSelectionNumber(3, 10, 1, default=5)
		config.plugins.moviecockpit.disk_space_info           = ConfigText(default="", fixed_size=False, visible_width=0)
		config.plugins.moviecockpit.debug                     = ConfigYesNo(default=False)
		config.plugins.moviecockpit.debug_log_path            = ConfigText(default="/media/hdd", fixed_size=False, visible_width=35)

		config.plugins.MVC                                    = ConfigSubsection()
		config.plugins.MVC.style                              = ConfigSubDict()
		config.plugins.MVC.preset                             = ConfigSubDict()

		self.checkList(config.plugins.moviecockpit.epglang)
		self.checkList(config.plugins.moviecockpit.sublang1)
		self.checkList(config.plugins.moviecockpit.sublang2)
		self.checkList(config.plugins.moviecockpit.sublang3)
		self.checkList(config.plugins.moviecockpit.audlang1)
		self.checkList(config.plugins.moviecockpit.audlang2)
		self.checkList(config.plugins.moviecockpit.audlang3)

		self.config = config
