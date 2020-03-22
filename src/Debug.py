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
import time
from Components.config import config


LOG_FILE = "enigma2_mvc"


def createLogFile():
	log_file = os.path.join(config.plugins.moviecockpit.debug_log_path.value, LOG_FILE + "_" + time.strftime("%Y%m%d_%H%M%S" + ".log"))
	print("MVC-I: Debug: createLogFile: %s" % log_file)
	os.system("journalctl | grep MVC > " + log_file)
	# clear journalctl buffer
	os.system("journalctl --rotate")
	os.system("journalctl --vacuum-time=1seconds")
