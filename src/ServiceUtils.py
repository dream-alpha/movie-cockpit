#!/usr/bin/python
# coding=utf-8
#
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
from enigma import eServiceReference

# DVB types
sidDVB = eServiceReference.idDVB	# eServiceFactoryDVB::id   enum { id = 0x1 };
sidDVD = 4369				# eServiceFactoryDVD::id   enum { id = 0x1111 };
sidM2TS = 3				# eServiceFactoryM2TS::id  enum { id = 0x3 };
sidDefault = 4097			# eServiceFactoryGST::id   enum { id = 0x1001 };

# ext types
extTS = frozenset([".ts", ".trp"])
extM2ts = frozenset([".m2ts"])
extIfo = frozenset([".ifo"])
extIso = frozenset([".iso", ".img"])
extDvd = extIfo | extIso
extVideo = frozenset([".ts", ".trp", ".avi", ".divx", ".f4v", ".flv", ".img", ".ifo", ".iso", ".m2ts", ".m4v", ".mkv", ".mov", ".mp4", ".mpeg", ".mpg", ".mts", ".vob", ".wmv", ".bdmv", ".asf", ".stream", ".webm"])
extBlu = frozenset([".bdmv"])

# Player types
plyDVB = extTS				# ServiceDVB
plyM2TS = extM2ts			# ServiceM2TS
plyDVD = extDvd				# ServiceDVD
plyAll = plyDVB | plyM2TS | plyDVD | extBlu


def getService(path, name=""):
	service = None
	ext = os.path.splitext(path)[1].lower()
	if path:
		if ext in plyDVB:
			service = eServiceReference(sidDVB, 0, path)
		elif ext in plyDVD:
			service = eServiceReference(sidDVD, 0, path)
		elif ext in plyM2TS:
			service = eServiceReference(sidM2TS, 0, path)
		else:
			DEFAULT_VIDEO_PID = 0x44
			DEFAULT_AUDIO_PID = 0x45
			service = eServiceReference(sidDefault, 0, path)
			service.setData(0, DEFAULT_VIDEO_PID)
			service.setData(1, DEFAULT_AUDIO_PID)
		service.setName(name)
	return service
