#!/usr/bin/python3

import re
import sys, os.path, glob
import mwxml, mwparserfromhell
import sqlite3

usageInfo =  f"usage: {sys.argv[0]}\n"
usageInfo += "Reads Wikimedia enwiki pages-articles XML dumps, obtaining\n"
usageInfo += "descriptions for page-ids, and adds them to a sqlite db.\n"
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

wikiDumpFiles = glob.glob("enwiki_content/enwiki-*-pages-articles-multistream*.xml")
wikiDumpFiles.sort(key = lambda x: int(re.search(r"multistream(\d+)", x).group(1)))
enwikiDb = "enwikiData.db"

# Some regexps and functions for parsing wikitext
descLineRegex = "^ *[A-Z'\"]"
embeddedHtmlRegex = r"<[^<]+/>|<!--[^<]+-->|<[^</]+>([^<]*|[^<]*<[^<]+>[^<]*)</[^<]+>|<[^<]+$"
	# Recognises a self-closing HTML tag, a tag 0 children, tag with 1 child with 0 children, or unclosed tag
convertTemplateRegex = r"{{convert\|(\d[^|]*)\|(?:(to|-)\|(\d[^|]*)\|)?([a-z][^|}]*)[^}]*}}"
def convertTemplateReplace(match):
	if match.group(2) == None:
		return "{} {}".format(match.group(1), match.group(4))
	else:
		return "{} {} {} {}".format(match.group(1), match.group(2), match.group(3), match.group(4))
parenGrpRegex = r" \([^()]*\)"
def parseDesc(text):
	prevLine = None
	for line in text.splitlines():
		if prevLine != None:
			if line.strip() == "" or re.match(descLineRegex, line) != None:
				return prevLine
			else:
				prevLine = None
		if re.match(descLineRegex, line) != None:
			line = re.sub(embeddedHtmlRegex, "", line)
			line = re.sub(convertTemplateRegex, convertTemplateReplace, line)
			line = mwparserfromhell.parse(line).strip_code() # Remove wikitext markup
			prevLine = re.sub(parenGrpRegex, "", line)
	if prevLine != None:
		return prevLine
	return None

# Open db
dbCon = sqlite3.connect(enwikiDb)
dbCur = dbCon.cursor()
dbCur.execute("CREATE TABLE descs (id INT PRIMARY KEY, desc TEXT)")
# Parse data
iterationNum = 0
for fileName in wikiDumpFiles:
	print("Processing file {}".format(fileName))
	dump = mwxml.Dump.from_file(open(fileName))
	for page in dump:
		iterationNum += 1
		if iterationNum % 10000 == 0:
			print("At iteration {}".format(iterationNum))
		# Parse page
		if page.namespace == 0 and page.redirect == None:
			revision = next(page)
			desc = parseDesc(revision.text)
			if desc != None:
				dbCur.execute("INSERT INTO descs VALUES (?, ?)", (page.id, desc))
# Close db
dbCon.commit()
dbCon.close()
