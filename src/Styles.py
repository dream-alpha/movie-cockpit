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
from xml.etree import ElementTree
from datetime import datetime

class TreeBase(object):
	def __init__(self, filename=None):
		self.read(filename)

	def read(self, filename):
		#print("MVC: style: TreeBase: read: filename: %s" % filename)
		self.tree = None
		self.root = None
		if filename and os.path.exists(filename):
			self.tree = ElementTree.parse(filename)
			self.root = self.tree.getroot()
			return True
		else:
			print("MVC-E: style: TreeBase: read: file does not exist: %s" % filename)
		return False

	def indent(self, elem, level=0, more_sibs=False):
		t = "	"
		i = "\n"
		if level:
			i += (level - 1) * t
		num_kids = len(elem)
		if num_kids:
			if not elem.text or not elem.text.strip():
				elem.text = i + t
				if level:
					elem.text += t
			count = 0
			for kid in elem:
				self.indent(kid, level + 1, count < num_kids - 1)
				count += 1
			if not elem.tail or not elem.tail.strip():
				elem.tail = i
				if more_sibs:
					elem.tail += t
		else:
			if level and (not elem.tail or not elem.tail.strip()):
				elem.tail = i
				if more_sibs:
					elem.tail += t

	def write(self, filename):
		#print("MVC: style: TreeBase: write: %s" % filename)
		self.indent(self.root)
		self.tree.write(filename, encoding="utf-8")


class Skin(TreeBase, object):
	def __init__(self, filename=None):
		TreeBase.__init__(self, filename)
#		self.read(filename)

	@staticmethod
	def checkStyled(filename):
		line_count = 0
		with open(filename, "r") as f:
			for line in f:
				if "<style " in line:
					return True
				line_count += 1
				if line_count > 10:
					break
		return False

#	@staticmethod
#	def readUserMTime(filename):
#		line_count = 0
#		with open(filename, "r") as f:
#			for line in f:
#				items = line.split("user_mtime")
#				if len(items) > 1:
#					values = items[1].split('"')
#					if len(values) > 1:
#						return values[1]
#					return ""
#				line_count += 1
#				if line_count > 10:
#					break
#		return ""

	def isStyled(self):
		return self.style_node is not None

	def read(self, filename):
		self.replaces = []
		self.style_info = []
		self.style_node = None
		self.style_name = ""
		self.user_mtime = ""
		result = TreeBase.read(self, filename)
		if result:
			test = self.root.findall("style")
			if len(test) == 1:
				self.style_node = test[0]
				self.style_name = self.style_node.attrib.get("name", "")
		return result

	def write(self, filename):
		#print("MVC: style: Skin: write: filename: %s, self.root: %s" % (filename, self.root))
		if self.root is not None:
			self.applyAttributes(self.replaces)
			#print("MVC: style: Skin: write: filename: %s, self.replaces: %s" % (filename, self.replaces))
			self.updateStyleInfo()
			TreeBase.write(self, filename + "~")
			#print("MVC: style: Skin: write: filename: %s" % filename)
			os.rename(filename + "~", filename)

	def updateStyleInfo(self):
		if self.style_node is None:
			self.style_node = ElementTree.Element("style")
# 			self.root.insert(0, ElementTree.Comment("Auto generated from Styles {0}.{1} (c)cmikula".format(__version__, __revision__)))
# 			self.root.insert(1, ElementTree.Comment("Do NOT deliver this informations with any skin update!"))
			self.root.insert(0, self.style_node)

		self.style_node.clear()
		self.style_node.attrib["name"] = self.style_name if self.style_name else ""
#		self.style_node.attrib["revision"] = __revision__
		self.style_node.attrib["time_stamp"] = str(datetime.now())
#		self.style_node.attrib["user_mtime"] = str(self.user_mtime)
		#print("MVC: style: Skin: updateStyleInfo: self.style_info: %s" % self.style_info)
		for tag, key, value in self.style_info:
			elem = ElementTree.Element(tag)
			elem.attrib["name"] = key
			elem.attrib["value"] = value
			self.style_node.append(elem)

	def applyNodes(self, nodes):
		for node in nodes:
			self.applyNode(node)

	def __replaceNode(self, root, node, _tag, _name, _id):
		for index, child in enumerate(root):
			if child.tag == _tag:
				if child.attrib.get("name", "") == _name and child.attrib.get("id", "") == _id:
					#print("MVC: style: Skin: __replaceNode: replace tag: %s, name: %s, id: %s, index: %s" % (_tag, _name, _id, index))
					root[index] = node
					return True
		return False

	def applyNode(self, nodes):
		#print("MVC: style: Skin: applyNode: nodes: %s" % str(nodes))
		if nodes is not None:
			for node in nodes:
				_tag = node.tag
				_name = node.attrib.get("name", "")
				_id = node.attrib.get("id", "")
				#print("MVC: style: Skin: applyNode: _tag: %s, _name: %s, _id: %s" % (_tag, _name, _id))
				if _tag == "attributes":
					self.replaces.extend(node)
					continue

				if _tag == "layout":
					for child in self.root.findall("layouts"):
						self.__replaceNode(child, node, _tag, _name, _id)
					continue

				found = self.__replaceNode(self.root, node, _tag, _name, _id)

				if not found and _tag == "screen":
					#print("MVC: style: Skin: applyNode: add tag: %s, name: %s, id: %s" % (_tag, _name, _id))
					self.root.append(node)
					found = True
				if not found:
					#print("MVC: style: Skin: applyNode: not found tag: %s, name: %s, id: %s" % (_tag, _name, _id))
					pass

	def applyAttributes(self, nodes):
		if nodes:
			to_replace = []
			for node in nodes:
				name = node.attrib.get("name", "")
				value = node.attrib.get("value", "")
				expect = node.attrib.get("expect", None)
				to_replace.append((name, value, expect, node.tag))
			#print("MVC: style: Skin: replace: %s" % str(to_replace))
			self.__replaceAttributes(self.root, to_replace)

	def __replaceAttributes(self, node, replace):
		for key in node.attrib.iterkeys():
			for name, value, expect, node_tag in replace:
				if expect is not None and expect != node.attrib[key]:
					continue
				if node_tag == "set" and key == name:
					node.attrib[key] = value
					continue
				if node.attrib[key].startswith(name):
					node.attrib[key] = node.attrib[key].replace(name, value)
					continue

		for x in node:
			self.__replaceAttributes(x, replace)

	def getConfig(self):
		d = dict()
		d["preset"] = dict()
		d["style"] = dict()
		if self.style_node is not None:
			for node in self.style_node:
				name = node.attrib.get("name", "")
				value = node.attrib.get("value", "")
				if name and value:
					d[node.tag][name] = value
		return d


class Style(TreeBase, object):
	def __init__(self, filename=None):
		TreeBase.__init__(self, filename)

	def checkDependency(self, _depend):
		return

	def hasStyle(self):
		#print("MVC: style: Style: hasStyle: %s" % str(self.root is not None))
		return self.root is not None

	def printInfo(self):
		groups = self.getGroup()
		for key1 in sorted(groups):
			#print("MVC: style: Style: printInfo: key1: %s" % key1)
			for key2 in sorted(groups[key1]):
				#print("MVC: style: Style: printInfo: key2:   %s" % key2)
				for _key3 in sorted(groups[key1][key2]):
					#print("MVC: style: Style: printInfo:    %s" % _key3)
					pass

	def getStyleNodes(self):
		l = []
		for node in self.root:
			if node.tag in ("presets", "sorted", "depends"):
				continue
			for style in node.findall("style"):
				item = StyleItem(style, node)
				#print("MVC: style: Style: getStyleNodes: item.getParentName: %s" % str(item.getParentName()))
				#print("MVC: style: Style: getStyleNodes: item.getName: %s" % str(item.getName()))
				#print("MVC: style: Style: getStyleNodes: item.getValue: %s" % str(item.getValue()))
				l.append(item)
		return l

	def getStyleNode(self, key, value):
		styles = self.getStyleNodes()
		for style in styles:
			n = style.getName()
			v = style.getValue()
			if n == key and v == value:
				#print("MVC: style: Style: getStyleNode: key: %s, value: %s" % (key, value))
				return style
		return None

	def getSkinNode(self, key, value):
		style = self.getStyleNode(key, value)
		if style:
			return style.getSkinNode()
		#print("MVC: style: Style: getSkinNode: not skin, key: %s, value: %s" % (key, value))
		return None

	def getGroup(self):
		d = dict()
		styles = self.getStyleNodes()
		for style in styles:
			if self.checkDependency is not None and not self.checkDependency(style.getDepend()):
				continue
			p = style.getParentName()
			n = style.getName()
			v = style.getValue()
			if p not in d:
				d[p] = dict()
			if n not in d[p]:
				d[p][n] = dict()
			d[p][n][v] = style.getSkinNode()
		return d

	def getDefault(self):
		d = dict()
		#print("MVC: style: Style: getDefault: dict(): %s" % str(d))
		for node1 in self.root.findall("presets"):
			for default in node1.findall("default"):
				for node2 in default:
					name = node2.attrib.get("name", "")
					value = node2.attrib.get("value", "")
					if name and value:
						d[name] = value
		return d

	def getPreset(self):
		d = dict()
		for node in self.root.findall("presets"):
			for styles in node.findall("style"):
				p = styles.attrib.get("name", "")
				n = styles.attrib.get("value", "")
				if p not in d:
					d[p] = dict()
				if n not in d[p]:
					d[p][n] = dict()
				for s in styles:
					v = s.attrib.get("name", "")
					value = s.attrib.get("value", "")
					d[p][n][v] = value
		return d

	def getPresetPreview(self, name, value, default=None):
		if name:
			for node in self.root.findall("presets"):
				for styles in node.findall("style"):
					for s in styles:
						n = s.attrib.get("name", "")
						v = s.attrib.get("value", "")
						if n == name and v == value:
							if "preview" in styles.attrib:
								return styles.attrib.get("preview", "")
							return default
		return default

	def getPreview(self, name, value, default=None):
		if name:
			for node in self.root:
				for styles in node.findall("style"):
					n = styles.attrib.get("name", "")
					v = styles.attrib.get("value", "")
					if n == name and v == value:
						if "preview" in styles.attrib:
							return styles.attrib.get("preview", "")
						return default
		return default

	def getDepends(self):
		d = dict()
		for node in self.root:
			for styles in node.findall("depend"):
				n = styles.attrib.get("name", "")
				v = styles.attrib.get("value", "")
				if n and v:
					d[n] = v
		return d

	def getSorted(self):
		d = dict()
		for nodes in self.root.findall("sorted"):
			for node in nodes:
				i = node.attrib.get("id", "")
				n = node.attrib.get("name", "")
				if n and i:
					d[n] = int(i)
		return d

	def sort(self, styles):
		s = self.getSorted()
		k = styles.keys()
		lx = sorted(k, key=lambda x: s.get(x, x))
		return lx

	def checkPresets(self):
		errors = []
		count = 0
		preset = self.getPreset()
		node = ElementTree.Element("presets")
		for key1 in sorted(preset):
			#print("MVC: style: Style: checkPresets: key1: %s" % key1)
			for key2 in sorted(preset[key1]):
				root = ElementTree.Element("style")
				root.attrib["name"] = key1
				root.attrib["value"] = key2
				element = None
				for key3 in sorted(preset[key1][key2]):
					#print("MVC:  " + str(key2) + " = " + preset[key1][key2][key3])
					test = self.getSkinNode(key3, preset[key1][key2][key3])
					if test is None:
						count += 1
						text = str.format('name="{0}" value="{1}"', key3, preset[key1][key2][key3])
						if text not in errors:
							errors.append(text)
						#print("MVC: style: Style: checkPresets: text: %s" % text)
						element = ElementTree.Element("style")
						element.attrib["name"] = key3
						element.attrib["value"] = preset[key1][key2][key3]
						root.append(element)
				if element is not None:
					node.append(root)

		if count > 0:
			info = ElementTree.Element("info")
			node.insert(0, info)
			info.attrib["description"] = "{0} error(s) in presets found!".format(count)
			info.attrib["time_stamp"] = str(datetime.now())
			for text in errors:
				info.append(ElementTree.Comment(text))
			#print("MVC: style: Style: checkPresets: %s errors found" % count)
			self.indent(node)
			return ElementTree.tostring(node)
		return ""

	def getSkinComponents(self, config_MVCStyles):
		defaults = self.getDefault()
		style_info = []
		nodes = []
		for key in sorted(config_MVCStyles.preset):
			value = config_MVCStyles.preset[key].getValue()
			style_info.append(("preset", key, value))
		for key in sorted(config_MVCStyles.style):
			value = config_MVCStyles.style[key].getValue()
			node = self.getSkinNode(key, value)
			if node is None and key in defaults:
				#print("MVC: style: Style: getSkinComponents: no style key: %s, value: %s" % (key, value))
				value = defaults[key]
				node = self.getSkinNode(key, value)
				if node is None:
					#print("MVC: style: Style: getSkinComponents: not found key: %s, value: %s" % (key, value))
					continue
				#print("MVC: style: Style: getSkinComponents: use default key: %s, value: %s" % (key, value))
			nodes.append(node)
			style_info.append(("style", key, value))
		return (nodes, style_info)


class StyleItem(object):
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


# class StyleUser(object):
# 	def __init__(self):
# 		self.user_root = None
#
# 	def read(self, filename):
# 		#print("MVC: style: StyleUser: read: filename: %s" % filename)
# 		if filename and not os.path.exists(filename):
# 			#print("MVC: style: StyleUser: read: file does not exist: %s" % filename)
# 			return False
# 		tree = ElementTree.parse(filename)
# 		self.user_root = tree.getroot()
# 		return True
#
# 	def loadToStyle(self, style, skin_name):
# 		if style.root is None:
# 			style.root = ElementTree.fromstring("<styles></styles>")
# 		unused = self.__getUnusable(skin_name)
# 		for node in self.user_root:
# 			n = node.get("name")
# 			if node.tag == "usable" or n in unused:
# 				#print("MVC: style: StyleUser: loadToStyle: cancel: node.tag: %s, n: %s" % (str(node.tag), str(n)))
# 				continue
# 			#print("MVC: style: loadToStyle: StyleUser: add: %s" % str(node.tag))
# 			self.__addNode(style, node)
#
# 	def __addNode(self, style, node):
# 		for elem in style.root:
# 			if elem.tag == node.tag:
# 				for item in node:
# 					elem.append(item)
# 				return
# 		style.root.append(node)
#
# 	def __getUnusable(self, skin_name):
# 		l1 = []
# 		l2 = []
# 		for nodes in self.user_root.findall("usable"):
# 			for node in nodes:
# 				n = node.get("name")
# 				if n:
# 					v = node.get("value")
# 					if v in skin_name:
# 						l1.append(n)
# 					else:
# 						l2.append(n)
# 		s1 = set(l1)
# 		s2 = set(l2)
# 		return s2 - s1
#
# 	def isUsable4Skin(self, skin_name):
# 		#print("MVC: style: StyleUser: isUsable4Skin: check usability: %s" % skin_name)
# 		if self.user_root is None:
# 			return False
# 		for nodes in self.user_root.findall("usable"):
# 			for node in nodes:
# 				n = node.get("name")
# 				v = node.get("value")
# 				if not n and v in skin_name:
# 					return True
# 		return False
