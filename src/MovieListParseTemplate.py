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


from Version import ID
try:
	from Debug import logger
except ImportError:
	class Logger():
		def __init__(self):
			return

		def debug(self, msg, *args):
			print(ID + ": " + msg % args)

		def info(self, msg, *args):
			print(ID + ": " + msg % args)

		def warning(self, msg, *args):
			print(ID + ": " + msg % args)
	logger = Logger()
try:
	from FileUtils import readFile
except ImportError:
	def readFile(path):
		f = open(path, "r")
		data = f.read()
		f.close()
		return data
try:
	from __init__ import _  # pylint: disable=W0611
except ImportError:
	def _(txt):
		return "_(\"" + txt + "\")"
try:
	import pprint
	pp = pprint.PrettyPrinter(indent=4, width=120)
except ImportError:
	pp = None
try:
	from SkinUtils import getSkinPath
	template_path = getSkinPath("MovieListTemplate.py")
except ImportError:
	template_path = "skin/MovieListTemplate.py"


def MultiContentEntryProgressPixmap(pos, size, png, foreColor, percent, borderWidth):
	return "MultiContentEntryProgressPixmap(" + "pos=" + str(pos) + ", size=" + str(size) + ", percent=" + str(percent) + ", png=" + str(png)\
		+ ", foreColor=" + ("0x%x" % foreColor) + ", borderWidth=" + str(borderWidth) + ")"


def MultiContentEntryText(pos, size, font, flags, text, color, color_sel):
	return "MultiContentEntryText(" + "pos=" + str(pos) + ", size=" + str(size) + ", font=" + str(font) + ", flags=" + str(flags)\
		+ ", text=" + str(text) + ", color=" + ("0x%x" % color) + ", color_sel=" + ("0x%x" % color_sel) + ")"


def MultiContentEntryPixmapAlphaBlend(pos, size, png):
	return "MultiContentEntryPixmapAlphaBlend(" + "pos=" + str(pos) + ", size=" + str(size) + ", png=" + str(png) + ")"


def gFont(_font_name, font_size):
	return font_size


def parseTemplate(template_string):

	def parseFonts(fonts):
		fonts_data = eval(str(fonts).replace("'", ""))
		fonts = []
		for font in fonts_data:
			fonts.append(font)

		return fonts

	def parseListStyles(list_styles):
		row_height = [0, 0, 0, 0, 0]
		lines_per_row = [0, 0, 0, 0, 0]
		for index, list_style in list_styles.iteritems():
			row_height[index] = list_style[2]
			lines_per_row[index] = list_style[3]
		return row_height, lines_per_row

	# just for parsing, no real values, used by eval
	font_height = [0, 0, 0]
	RT_HALIGN_LEFT = ""		# noqa: F841 pylint: disable=W0612
	RT_HALIGN_RIGHT = ""		# noqa: F841 pylint: disable=W0612
	RT_HALIGN_CENTER = ""		# noqa: F841 pylint: disable=W0612
	yoffs = 0			# noqa: F841 pylint: disable=W0612
	start = 0			# noqa: F841 pylint: disable=W0612
	spacer = 0			# noqa: F841 pylint: disable=W0612
	date_width = 0			# noqa: F841 pylint: disable=W0612
	length_width = 0		# noqa: F841 pylint: disable=W0612
	progress_width = 0		# noqa: F841 pylint: disable=W0612
	width = 0			# noqa: F841 pylint: disable=W0612
	bar_size = (0, 0)		# noqa: F841 pylint: disable=W0612
	icon_size = (0, 0)		# noqa: F841 pylint: disable=W0612
	picon_size = (0, 0)		# noqa: F841 pylint: disable=W0612
	row_height = [0, 0, 0, 0, 0]
	line_height = row_height

	template = eval(template_string)

	fonts = parseFonts(template["fonts"])
	font_height = [fonts[0] + 3, fonts[1] + 3, fonts[2] + 3]
	list_styles = template["list_styles"]
	row_height, lines_per_row = parseListStyles(list_styles)
	for i, height in enumerate(row_height):
		line_height[i] = height / lines_per_row[i]
	template_attributes = template["template_attributes"]
	template_attributes["row_height"] = row_height		# row height
	template_attributes["lines_per_row"] = lines_per_row	# lines per row
	template_attributes["line_height"] = line_height	# line height
	template_attributes["font_height"] = font_height	# adjusted font height
	logger.info("list_styles: %s", str(list_styles))
	logger.info("template_attributes: %s", str(template_attributes))
	return list_styles, template_attributes


def main():
	logger.debug("Checking movie list template...")
	data_string = readFile(template_path)
	if data_string:
		_list_styles, template_attributes = parseTemplate(data_string)

		RT_HALIGN_LEFT = "RT_HALIGN_LEFT"			# noqa: F841 pylint: disable=W0612
		RT_HALIGN_RIGHT = "RT_HALIGN_RIGHT"			# noqa: F841 pylint: disable=W0612
		RT_HALIGN_CENTER = "RT_HALIGN_CENTER"			# noqa: F841 pylint: disable=W0612
		width = 1200 - 15					# noqa: F841 pylint: disable=W0612
		start = template_attributes["start"]			# noqa: F841 pylint: disable=W0612
		spacer = template_attributes["spacer"]			# noqa: F841 pylint: disable=W0612
		bar_size = template_attributes["bar_size"]		# noqa: F841 pylint: disable=W0612
		icon_size = template_attributes["icon_size"]		# noqa: F841 pylint: disable=W0612
		picon_size = template_attributes["picon_size"]		# noqa: F841 pylint: disable=W0612
		date_width = template_attributes["date_width"]		# noqa: F841 pylint: disable=W0612
		length_width = template_attributes["length_width"]	# noqa: F841 pylint: disable=W0612
		progress_width = template_attributes["progress_width"]	# noqa: F841 pylint: disable=W0612
		yoffs = template_attributes["yoffs"]			# noqa: F841 pylint: disable=W0612
		font_height = template_attributes["font_height"]	# noqa: F841 pylint: disable=W0612
		row_height = template_attributes["row_height"]		# noqa: F841 pylint: disable=W0612
		lines_per_row = template_attributes["lines_per_row"]	# noqa: F841 pylint: disable=W0612
		line_height = template_attributes["line_height"]	# noqa: F841 pylint: disable=W0612

		if pp:
			pp.pprint(eval(data_string))
		else:
			logger.debug(eval(data_string))
	logger.debug("Done.")


if __name__ == "__main__":
	main()
