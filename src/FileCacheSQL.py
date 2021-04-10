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
from sqlite3 import dbapi2 as sqlite


SQL_DB_NAME = "/etc/enigma2/moviecockpit.db"


# file indexes
FILE_IDX_DIR = 0
FILE_IDX_TYPE = 1
FILE_IDX_PATH = 2
FILE_IDX_FILENAME = 3
FILE_IDX_EXT = 4
FILE_IDX_NAME = 5
FILE_IDX_EVENT_START_TIME = 6
FILE_IDX_RECORDING_START_TIME = 7
FILE_IDX_RECORDING_STOP_TIME = 8
FILE_IDX_LENGTH = 9
FILE_IDX_DESCRIPTION = 10
FILE_IDX_EXTENDED_DESCRIPTION = 11
FILE_IDX_SERVICE_REFERENCE = 12
FILE_IDX_SIZE = 13
FILE_IDX_CUTS = 14
FILE_IDX_TAGS = 15


class FileCacheSQL():

	def __init__(self):
		logger.info("...")
		self.sql_conn = sqlite.connect(SQL_DB_NAME)
		self.sqlCreateTable()

	def sqlCreateTable(self):
		self.sql_conn.execute(
			"""CREATE TABLE IF NOT EXISTS recordings (directory TEXT, file_type INTEGER, path TEXT, file_name TEXT, file_ext TEXT, name TEXT, event_start_time INTEGER, recording_start_time INTEGER, recording_stop_time INTEGER, length INTEGER,\
			description TEXT, extended_description TEXT, service_reference TEXT, size INTEGER, cuts BLOB, tags TEXT)"""
		)
		self.sql_conn.text_factory = str
		self.cursor = self.sql_conn.cursor()

	def sqlClearTable(self):
		self.cursor.execute("DELETE FROM recordings")
		self.sql_conn.commit()

	def sqlSelect(self, where):
		sql = """SELECT * FROM recordings WHERE %s""" % where
		logger.debug("sql: %s", sql)
		self.cursor.execute(sql)
		file_list = self.cursor.fetchall()
		self.sql_conn.commit()
		return file_list

	def sqlDelete(self, where):
		sql = """DELETE FROM recordings WHERE %s""" % where
		logger.debug("sql: %s", sql)
		self.cursor.execute(sql)
		self.sql_conn.commit()

	def sqlInsert(self, file_data):
		data = list(file_data)
		data[FILE_IDX_CUTS] = sqlite.Binary(data[FILE_IDX_CUTS])
		file_data = tuple(data)
		self.cursor.execute("INSERT INTO recordings VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", file_data)
		self.sql_conn.commit()

	def sqlClose(self):
		self.sql_conn.commit()
		self.sql_conn.close()
