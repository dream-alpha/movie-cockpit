#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 by cmikula
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
#
# For example, if you distribute copies of such a program, whether gratis or for a fee, you
# must pass on to the recipients the same freedoms that you received. You must make sure
# that they, too, receive or can get the source code. And you must show them these terms so they know their rights.


from Debug import logger
from Components.config import config, ConfigText


KEYS = ((".", "\s01"), ("=", "\s02"))


def __encodeConfig(value):
	for x in KEYS:
		value = value.replace(x[0], x[1])
	return value


def __decodeConfig(value):
	for x in KEYS:
		value = value.replace(x[1], x[0])
	return value


def encodeConfig(conf, c):
	try:
		for key, item in c.iteritems():
			key = __encodeConfig(key)
			conf[key] = ConfigText()
			conf[key].value = __encodeConfig(item.value)
	except Exception as e:
		logger.error("exception: %s", e)


def storeConfig():
	logger.debug("...")
	p = config.plugins.moviecockpit.preset
	s = config.plugins.moviecockpit.style
	encodeConfig(config.plugins.moviecockpit.preset, p)
	encodeConfig(config.plugins.moviecockpit.style, s)
	config.plugins.moviecockpit.preset.save()
	config.plugins.moviecockpit.style.save()


def loadConfig(conf):
	logger.debug("conf.stored_values: %s", str(conf.stored_values))
	for key, value in conf.stored_values.iteritems():
		logger.debug("key: %s, value: %s", key, value)
		key = __decodeConfig(key)
		conf[key] = ConfigText()
		conf[key].value = __decodeConfig(value)
