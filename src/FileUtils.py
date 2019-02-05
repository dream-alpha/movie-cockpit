#!/usr/bin/python
# encoding: utf-8
#
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

import os

def readFile(path):
	try:
		return file(path).read()
	except (IOError, TypeError) as e:
		print("MVC-E: FileUtils: readFile: path: %s, exception: %s" % (path, e))
		return ""

def writeFile(path, data):
	try:
		file(path, "w").write(data)
		file(path).close()
	except (IOError, TypeError) as e:
		print("MVC_E: FileUtils: writeFile: path: %s, excpetion: %s" % (path, e))

def deleteFile(path):
	try:
		os.remove(path)
	except (IOError, TypeError) as e:
		print("MVC-E: FileUtils: deleteFile: exception: path: %s, exception: %s" % (path, e))
