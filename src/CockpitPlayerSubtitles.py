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


from Debug import logger
from Components.config import config
from enigma import iSubtitleType_ENUMS
from Screens.AudioSelection import SUB_FORMATS, GST_SUB_FORMATS
from Screens.InfoBarGenerics import InfoBarSubtitleSupport
from Tools.ISO639 import LanguageCodes as langC


class CockpitPlayerSubtitles(InfoBarSubtitleSupport):

	def __init__(self):
		InfoBarSubtitleSupport.__init__(self)
		self.selected_subtitle = None

	def trySubEnable(self, slist, match):
		for e in slist:
			logger.debug("e: %s", e)
			logger.debug("match %s", langC[match][0])
			if langC[match][0] == e[2]:
				logger.debug("match: %s", e)
				if self.selected_subtitle != e[0]:
					self.subtitles_enabled = False
					self.selected_subtitle = e[0]
					self.subtitles_enabled = True
					return True
			else:
				logger.debug("no match")
		return False

	def setSubtitleState(self, enabled):
		try:
			if not config.plugins.moviecockpit.autosubs.value or not enabled:
				return

			subs = self.getCurrentServiceSubtitle() if isinstance(self, InfoBarSubtitleSupport) else None
			n = (subs.getNumberOfSubtitleTracks() if subs else 0)
			if n == 0:
				return

			self.sub_format_dict = {}
			self.gstsub_format_dict = {}
			for index, (short, _text, rank) in sorted(SUB_FORMATS.items(), key=lambda x: x[1][2]):
				if rank > 0:
					self.sub_format_dict[index] = short
			for index, (short, _text, rank) in sorted(GST_SUB_FORMATS.items(), key=lambda x: x[1][2]):
				if rank > 0:
					self.gstsub_format_dict[index] = short
			lt = []
			alist = []
			for index in range(n):
				info = subs.getSubtitleTrackInfo(index)
				languages = info.getLanguage().split('/')
				logger.debug("lang %s", languages)
				iType = info.getType()
				logger.debug("type %s", iType)
				if iType == iSubtitleType_ENUMS.GST:
					iType = info.getGstSubtype()
# 				codec = self.gstsub_format_dict[iType] if iType in self.gstsub_format_dict else '?'
# 			else:
# 				codec = self.sub_format_dict[iType] if iType in self.sub_format_dict else '?'
# 			logger.debug("codec %s", codec)
				lt.append((index, (iType == 1 and "DVB" or iType == 2 and "TTX" or "???"), languages))
			if lt:
				logger.debug("%s", str(lt))
				for e in lt:
					alist.append((e[0], e[1], e[2][0] in langC and langC[e[2][0]][0] or e[2][0]))
					if alist:
						logger.debug("%s", str(alist))
						for sublang in [config.plugins.moviecockpit.sublang1.value, config.plugins.moviecockpit.sublang2.value, config.plugins.moviecockpit.sublang3.value]:
							if self.trySubEnable(alist, sublang):
								break
		except Exception as e:
			logger.error("exception: %s", e)
