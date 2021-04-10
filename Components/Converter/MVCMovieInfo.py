#!/usr/bin/python
# encoding: utf-8
#
# Copyright (C) 2011 betonme
# Copyright (C) 2018-2021 dream-alpha
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


from Components.Converter.MovieInfo import MovieInfo
from Components.Element import cached
from enigma import iServiceInformation
from ServiceReference import ServiceReference


class MVCMovieInfo(MovieInfo):
	def __init__(self, ptype):
		MovieInfo.__init__(self, ptype)

	@cached
	def getText(self):
		text = ""
		service = self.source.service
		info = self.source.info
		if info and service:
			if self.type == self.MOVIE_SHORT_DESCRIPTION:
				event = self.source.event
				if event:
					text = info.getInfoString(service, iServiceInformation.sDescription)
					if text == "":
						text = event.getShortDescription()
			elif self.type == self.MOVIE_META_DESCRIPTION:
				text = info.getInfoString(service, iServiceInformation.sDescription)
			elif self.type == self.MOVIE_REC_SERVICE_NAME:
				rec_ref_str = info.getInfoString(service, iServiceInformation.sServiceref)
				text = ServiceReference(rec_ref_str).getServiceName()
			elif self.type == self.MOVIE_REC_FILESIZE:
				filesize = info.getInfoObject(service, iServiceInformation.sFileSize)
				if filesize is not None:
					filesize /= 1024 * 1024
					if filesize > 0:
						if filesize < 1000:
							text = "%d MB" % filesize
						text = "%d GB" % (filesize / 1024)
		return text

	text = property(getText)
