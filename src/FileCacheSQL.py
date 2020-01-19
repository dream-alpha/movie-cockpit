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


from sqlite3 import dbapi2 as sqlite


SQL_DB_NAME = "/etc/enigma2/moviecockpit.db"


class FileCacheSQL():
	def __init__(self):
		print("MVC-I: FileCacheSQL: __init__")
		self.sql_conn = sqlite.connect(SQL_DB_NAME)
		self.sqlCreateTable()

	def sqlCreateTable(self):
		self.sql_conn.execute(
			'''CREATE TABLE IF NOT EXISTS recordings (directory TEXT, filetype INTEGER, path TEXT, fileName TEXT, fileExt TEXT, name TEXT, event_start_time INTEGER, recording_start_time INTEGER, recording_stop_time INTEGER, length INTEGER,\
			description TEXT, extended_description TEXT, service_reference TEXT, size INTEGER, cuts TEXT, tags TEXT)'''
		)
		self.sql_conn.text_factory = str
		self.cursor = self.sql_conn.cursor()

	def sqlClearTable(self):
		self.cursor.execute("DELETE FROM recordings")
		self.sql_conn.commit()

	def sqlSelect(self, where):
		sql = "SELECT * FROM recordings WHERE " + where
		#print("MVC: FileCacheSQL: sqlSelect: sql: %s" % sql)
		self.cursor.execute(sql)
		filelist = self.cursor.fetchall()
		self.sql_conn.commit()
		return filelist

	def sqlDelete(self, where):
		sql = "DELETE FROM recordings WHERE " + where
		#print("MVC: FileCacheSQL: sqlDelete: sql: %s" % sql)
		self.cursor.execute(sql)
		self.sql_conn.commit()

	def sqlInsert(self, filedata):
		self.cursor.execute("INSERT INTO recordings VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", filedata)
		self.sql_conn.commit()

	def sqlClose(self):
		self.sql_conn.commit()
		self.sql_conn.close()
