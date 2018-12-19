#!/usr/bin/python
import sys
import os
import string
from xml.sax import make_parser
from xml.sax.handler import ContentHandler, property_lexical_handler
try:
	from _xmlplus.sax.saxlib import LexicalHandler
	no_comments = False
except ImportError:
	class LexicalHandler(object):
		pass
	no_comments = True

class parseXML(ContentHandler, LexicalHandler, object):
	def __init__(self, attrlist):
		self.isPointsElement, self.isReboundsElement = 0, 0
		self.attrlist = attrlist
		self.last_comment = None

	def comment(self, comment):
		if comment.find("TRANSLATORS:") != -1:
			self.last_comment = comment

	def startElement(self, _name, attrs):
		for x in ["text", "title", "value", "caption"]:
			try:
				attrlist.add((attrs[x], self.last_comment))
				self.last_comment = None
			except KeyError:
				pass

parser = make_parser()

attrlist = set()

contentHandler = parseXML(attrlist)
parser.setContentHandler(contentHandler)
if not no_comments:
	parser.setProperty(property_lexical_handler, contentHandler)

for arg in sys.argv[1:]:
	if os.path.isdir(arg):
		for afile in os.listdir(arg):
			if (afile.endswith(".xml")):
				parser.parse(os.path.join(arg, afile))
	else:
		parser.parse(arg)

	attrlist = list(attrlist)
	attrlist.sort(key=lambda a: a[0])

	for (k, c) in attrlist:
		print("")
		print('#: ' + arg)
		string.replace(k, "\\n", "\"\n\"")
		if c:
			for l in c.split('\n'):
				print("#. " + l)
		if str(k).strip() != "":
			print('msgid "' + str(k) + '"')
			print('msgstr ""')

	attrlist = set()
