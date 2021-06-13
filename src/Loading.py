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
from enigma import eTimer
from SkinUtils import getSkinPath
from Tools.LoadPixmap import LoadPixmap
import glob


ACTIVITY_TIMER_DELAY = 125


class Loading():

	def __init__(self, pic):
		logger.debug("...")
		self.activity_timer = eTimer()
		self.activity_timer_conn = self.activity_timer.timeout.connect(self.doActivityTimer)
		self.pic_index = 0
		self.pic = pic
		self.pics = len(glob.glob(getSkinPath("images/spinner/*.png")))
		logger.debug("self.pics: %s", self.pics)

	def start(self):
		logger.debug("...")
		self.pic.show()
		self.activity_timer.start(ACTIVITY_TIMER_DELAY, False)

	def stop(self):
		logger.debug("...")
		self.pic.hide()
		self.activity_timer.stop()

	def doActivityTimer(self):
		logger.debug("...")
		self.pic_index += 1
		pic = "wait%s.png" % (self.pic_index + 1)
		self.pic.instance.setPixmap(LoadPixmap(getSkinPath("images/spinner/" + pic), cached=False))
		self.pic_index = (self.pic_index + 1) % self.pics
