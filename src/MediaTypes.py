#!/usr/bin/python
# encoding: utf-8
#
# Copyright (C) 2011 by Coolman & Swiss-MAD
#           (C) 2018-2019 by dream-alpha
#
# In case of reuse of this source code please do not remove this copyright.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    For more information on the GNU General Public License see:
#    <http://www.gnu.org/licenses/>.
#

from enigma import eServiceReference

extTS = frozenset([".ts", ".trp"])
extM2ts = frozenset([".m2ts"])
extIfo = frozenset([".ifo"])
extIso = frozenset([".iso", ".img"])
extDvd = extIfo | extIso
extVideo = frozenset([".ts", ".trp", ".avi", ".divx", ".f4v", ".flv", ".img", ".ifo", ".iso", ".m2ts", ".m4v", ".mkv", ".mov", ".mp4", ".mpeg", ".mpg", ".mts", ".vob", ".wmv", ".bdmv", ".asf", ".stream", ".webm"])
extBlu = frozenset([".bdmv"])

# blue disk movie
# mimetype("video/x-bluray") ext (".bdmv")

# Player types
plyDVB = extTS                                   # ServiceDVB
plyM2TS = extM2ts                                # ServiceM2TS
plyDVD = extDvd                                  # ServiceDVD

#plyBLU = extBlu | extIso                        # BludiscPlayer Plugin
plyAll = plyDVB | plyM2TS | plyDVD | extBlu

# Type definitions
# Service ID types for E2 service identification
sidDVB = eServiceReference.idDVB                  # eServiceFactoryDVB::id   enum { id = 0x1 };
sidDVD = 4369                                     # eServiceFactoryDVD::id   enum { id = 0x1111 };
sidM2TS = 3                                       # eServiceFactoryM2TS::id  enum { id = 0x3 };
