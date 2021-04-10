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


import os
from Debug import logger
from enigma import eTimer, eConsoleAppContainer
from MountManagerUtils import parseFstab, getBookmarkSpaceInfo
from MountManagerInit import MountManagerInit
from AutoMount import iAutoMount
from DelayTimer import DelayTimer
from ConfigInit import getConfig


instance = None
POLL_TIME = 5000


class MountManager(MountManagerInit):

	def __init__(self):
		MountManagerInit.__init__(self)
		self.ping_timer = eTimer()
		self.ping_timer_conn = self.ping_timer.timeout.connect(self.executePing)
		self.ping_container = eConsoleAppContainer()
		self.ping_stdoutAvail_conn = self.ping_container.stdoutAvail.connect(self.stdoutPingData)
		self.ping_stderrAvail_conn = self.ping_container.stderrAvail.connect(self.stderrPingData)
		self.ping_container_appClosed_conn = self.ping_container.appClosed.connect(self.finishedPing)
		self.config = getConfig()
		self.bookmarks = []
		self.mounts_table = {}
		self.ping_commands = ""
		self.shares_changed = []
		self.init_counter = 0
		self.init_complete = False
		self.init_complete_callback = None
		self.onMountsChange()
		self.config.bookmarks.addNotifier(self.onMountsChange, initial_call=False)
		self.config.mount_manager_enabled.addNotifier(self.onMountManagerEnabledChange, initial_call=False)
		if self.config.mount_manager_enabled:
			self.startPolling()

	@staticmethod
	def getInstance():
		global instance
		if instance is None:
			instance = MountManager()
		return instance

	def onMountManagerEnabledChange(self):
		if self.config.mount_manager_enabled.value:
			self.startPolling()
		else:
			self.stopPolling()

	def onInitComplete(self, callback):
		self.init_complete_callback = callback
		if self.init_complete:
			self.init_complete_callback()

	def check4InitComplete(self):
		self.init_counter += 1
		logger.debug("init_counter: %s", self.init_counter)
		if self.init_counter == 2:
			logger.debug("initialization complete")
			self.init_complete = True
			if self.init_complete_callback:
				DelayTimer(1000, self.init_complete_callback)

	def initPingCommands(self):
		logger.debug("iAutoMount.mounts: %s", str(iAutoMount.mounts))
		ping_ips = []
		self.ping_commands = ""
		for sharename in iAutoMount.mounts:
			ip = iAutoMount.mounts[sharename]["ip"]
			if ip not in ping_ips:
				ping_ips.append(ip)
				if self.ping_commands:
					self.ping_commands += ";"
				self.ping_commands += "ping -c1 -w1 " + ip
		if not self.ping_commands:
			self.init_complete = True
		logger.debug("ping_commands: %s", self.ping_commands)

	def onMountsChange(self, _reason=None):
		logger.info("...")
		self.shares_changed = []
		mount_points = parseFstab()
		self.mounts_table = {}
		self.bookmarks = self.config.bookmarks.value
		if not self.bookmarks:
			self.bookmarks = self.initBookmarks()
		for __bookmark in self.bookmarks:
			__bookmark = os.path.normpath(__bookmark)
			mount_point = None
			for __mount_point in mount_points:
				if os.path.realpath(__bookmark).startswith(__mount_point):
					mount_point = __mount_point
					break
			if mount_point is not None:
				self.mounts_table[__bookmark] = mount_point
		logger.info("bookmarks: %s", self.bookmarks)
		logger.info("mounts_table: %s", self.mounts_table.keys())
		self.initPingCommands()
		self.check4InitComplete()

#### ping loop

	def stdoutPingData(self, data):
		logger.info("...")
		#logger.info("data: %s", data)
		lines = data.splitlines()
		ip = packets = None
		for line in lines:
			line = " ".join(line.split())
			words = line.split(" ")
			if not ip and "PING" in line:
				ip = words[1]
			elif "packets received" in line:
				packets = int(words[3])
			if ip is not None and packets is not None:
				for sharename in iAutoMount.mounts:
					if iAutoMount.mounts[sharename]["ip"] == ip:
						if packets == 0:
							#logger.debug("%s (%s) is offline", sharename, ip)
							if iAutoMount.mounts[sharename]["active"]:
								iAutoMount.mounts[sharename]["active"] = False
								self.shares_changed.append(sharename)
						else:
							#logger.debug("%s (%s) is online", sharename, ip)
							if not iAutoMount.mounts[sharename]["active"]:
								iAutoMount.mounts[sharename]["active"] = True
								self.shares_changed.append(sharename)
				ip = packets = None
		for sharename in iAutoMount.mounts:
			logger.debug("sharename: %s, ip: %s, active: %s", sharename, iAutoMount.mounts[sharename]["ip"], iAutoMount.mounts[sharename]["active"])

	def stderrPingData(self, data):
		logger.info("data: %s", data)

	def executePing(self):
		if self.ping_commands:
			logger.debug("ping_commands: %s", self.ping_commands)
			self.ping_container.execute(self.ping_commands)

	def finishedPing(self, _ret_val=None):
		logger.debug("shares_changed: %s", self.shares_changed)
		if self.shares_changed:
			iAutoMount.apply(self.shares_changed, self.onMountsChange)
			iAutoMount.save()
		else:
			self.check4InitComplete()

### polling

	def startPolling(self):
		self.executePing()
		self.ping_timer.stop()
		self.ping_timer.start(POLL_TIME)

	def stopPolling(self):
		self.ping_container.kill()
		self.ping_timer.stop()

### mount point

	def getMountPoint(self, path):
		mount_point = None
		bookmark = self.getBookmark(path)
		if bookmark in self.mounts_table:
			mount_point = self.mounts_table[bookmark]
		#logger.debug("path: %s, mount_point: %s", path, mount_point)
		return mount_point

### bookmark

	def isBookmark(self, path):
		answer = path in self.mounts_table
		logger.debug("path: %s, answer: %s", path, answer)
		return answer

	def getBookmark(self, path):
		bookmark = None
		for __bookmark in self.bookmarks:
			__bookmark = os.path.normpath(__bookmark)
			if path.startswith(__bookmark):
				bookmark = __bookmark
				break
		#logger.debug("path: %s, bookmark: %s", path, bookmark)
		return bookmark

	def getMountedBookmarks(self):
		mounted_bookmarks = self.mounts_table.keys()
		logger.debug("mounted_bookmarks: %s", mounted_bookmarks)
		return mounted_bookmarks

	def getBookmarksSpaceInfo(self):
		space_info = ""
		for __bookmark in self.getMountedBookmarks():
			used_percent, used, available = getBookmarkSpaceInfo(__bookmark)
			if used >= 0 and available >= 0:
				if space_info != "":
					space_info += ", "
				space_info += os.path.dirname(__bookmark)[len("/media/"):] + (": %.1f" % used_percent) + "%"
		return space_info
