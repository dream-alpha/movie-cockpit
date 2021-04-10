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


class StyleItem():
	def __init__(self, node, parent):
		self.node = node
		self.parent = parent

	def getParentName(self):
		if self.parent is not None:
			name = self.parent.attrib.get('name', '')
			if not name:
				return self.parent.tag
			return name
		return self.node[0].tag if self.node else ""

	def getName(self):
		g = self.node.attrib.get('name', '')
		if not g:
			return self.parent.tag
		return g

	def getValue(self):
		return self.node.attrib.get('value', '')

	def getPreview(self):
		return self.node.attrib.get('preview', '')

	def getDepend(self):
		return self.node.attrib.get('depend', '')

	def getSkinNode(self):
		return self.node
