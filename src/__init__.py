#!/usr/bin/python
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


from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from os import environ
from Version import PLUGIN
import gettext
from Debug import initLogging


def initLocale():
	lang = language.getLanguage()[:2]
	environ["LANGUAGE"] = lang
	gettext.bindtextdomain(PLUGIN, resolveFilename(SCOPE_PLUGINS, "Extensions/" + PLUGIN + "/locale"))


def _(txt):
	translation = gettext.dgettext(PLUGIN, txt)
	return translation


initLogging()
initLocale()
language.addCallback(initLocale)
