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
from RecordTimer import AFTEREVENT
import NavigationInstance


def isRecording(path):
	logger.debug("path: %s", path)
	timer = None
	for __timer in NavigationInstance.instance.RecordTimer.timer_list:
		if __timer.isRunning() and not __timer.justplay and path == __timer.Filename:
			timer = __timer
			break
	return timer


def stopRecording(path):
	timer = isRecording(path)
	if timer:
		if timer.repeated:
			timer.enable()
			timer_afterEvent = timer.afterEvent
			timer.afterEvent = AFTEREVENT.NONE
			timer.processRepeated(findRunningEvent=False)
			NavigationInstance.instance.RecordTimer.doActivate(timer)
			timer.afterEvent = timer_afterEvent
			NavigationInstance.instance.RecordTimer.timeChanged(timer)
		else:
			timer.afterEvent = AFTEREVENT.NONE
			NavigationInstance.instance.RecordTimer.removeEntry(timer)
		logger.info("path: %s", path)
