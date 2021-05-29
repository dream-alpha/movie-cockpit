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
from Tools.ISO639 import LanguageCodes as langC
from Components.Language import language


class CockpitPlayerAudio():

	def __init__(self, session):
		self.session = session

	def getServiceInterface(self, interface):
		service = self.session.nav.getCurrentService()
		if service:
			attr = getattr(service, interface, None)
			if callable(attr):
				return attr()
		return None

	def setAudioTrack(self):
		try:
			logger.debug("audio")
			if not config.plugins.moviecockpit.autoaudio.value:
				return
			service = self.session.nav.getCurrentService()
			tracks = service and self.getServiceInterface("audioTracks")
			nTracks = tracks.getNumberOfTracks() if tracks else 0
			if not nTracks:
				return
			index = 0
			trackList = []
			for i in range(nTracks):
				audioInfo = tracks.getTrackInfo(i)
				lang = audioInfo.getLanguage()
				logger.debug("lang %s", lang)
				desc = audioInfo.getDescription()
				logger.debug("desc %s", desc)
# 			audio_type = audioInfo.getType()
				track = index, lang, desc, type
				index += 1
				trackList += [track]
			seltrack = tracks.getCurrentTrack()
			# we need default selected language from image
			# to set the audio track if "config.plugins.moviecockpit.autoaudio.value" are not set
			syslang = language.getLanguage()[:2]
			if config.plugins.moviecockpit.autoaudio.value:
				audiolang = [config.plugins.moviecockpit.audlang1.value, config.plugins.moviecockpit.audlang2.value, config.plugins.moviecockpit.audlang3.value]
			else:
				audiolang = syslang
			useAc3 = config.plugins.moviecockpit.autoaudio_ac3.value
			if useAc3:
				matchedAc3 = self.tryAudioTrack(tracks, audiolang, trackList, seltrack, useAc3)
				if matchedAc3:
					return
				matchedMpeg = self.tryAudioTrack(tracks, audiolang, trackList, seltrack, False)
				if matchedMpeg:
					return
				tracks.selectTrack(0)  # fallback to track 1(0)
			else:
				matchedMpeg = self.tryAudioTrack(tracks, audiolang, trackList, seltrack, False)
				if matchedMpeg:
					return
				matchedAc3 = self.tryAudioTrack(tracks, audiolang, trackList, seltrack, useAc3)
				if matchedAc3:
					return
				tracks.selectTrack(0)  # fallback to track 1(0)
			logger.debug("audio1")
		except Exception as e:
			logger.error("exception: %s", e)

	def tryAudioTrack(self, tracks, audiolang, trackList, seltrack, useAc3):
		for entry in audiolang:
			entry = langC[entry][0]
			logger.debug("audio2")
			for x in trackList:
				try:
					x1val = langC[x[1]][0]
				except Exception:
					x1val = x[1]
				logger.debug(x1val)
				logger.debug("entry %s", entry)
				logger.debug(x[0])
				logger.debug("seltrack %s", seltrack)
				logger.debug(x[2])
				logger.debug(x[3])
				if entry == x1val and seltrack == x[0]:
					if useAc3:
						logger.debug("audio3")
						if x[3] == 1 or x[2].startswith('AC'):
							logger.debug("audio track is current selected track: %s", str(x))
							return True
					else:
						logger.debug("audio4")
						logger.debug("currently selected track: %s", str(x))
						return True
				elif entry == x1val and seltrack != x[0]:
					if useAc3:
						logger.debug("audio5")
						if x[3] == 1 or x[2].startswith('AC'):
							logger.debug("match: %s", str(x))
							tracks.selectTrack(x[0])
							return True
					else:
						logger.debug("audio6")
						logger.debug("match: %s", str(x))
						tracks.selectTrack(x[0])
						return True
		return False
