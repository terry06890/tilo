#!/usr/bin/python3

import sys, os, re
import bz2
import html, mwxml, mwparserfromhell
import sqlite3

usageInfo =  f"usage: {sys.argv[0]}\n"
usageInfo += "Reads a Wikimedia enwiki dump, and adds page, redirect,\n"
usageInfo += "and short-description info to an sqlite db.\n"
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

dumpFile = "enwiki-20220501-pages-articles-multistream.xml.bz2" # 22,034,540 pages
enwikiDb = "enwikiData.db"

# Some regexps and functions for parsing wikitext
descLineRegex = re.compile("^ *[A-Z'\"]")
embeddedHtmlRegex = re.compile(r"<[^<]+/>|<!--[^<]+-->|<[^</]+>([^<]*|[^<]*<[^<]+>[^<]*)</[^<]+>|<[^<]+$")
	# Recognises a self-closing HTML tag, a tag 0 children, tag with 1 child with 0 children, or unclosed tag
convertTemplateRegex = re.compile(r"{{convert\|(\d[^|]*)\|(?:(to|-)\|(\d[^|]*)\|)?([a-z][^|}]*)[^}]*}}")
parensGrpRegex = re.compile(r" \([^()]*\)")
leftoverBraceRegex = re.compile(r"(?:{\||{{).*")
def convertTemplateReplace(match):
	if match.group(2) == None:
		return f"{match.group(1)} {match.group(4)}"
	else:
		return f"{match.group(1)} {match.group(2)} {match.group(3)} {match.group(4)}"
def parseDesc(text):
	# Find first matching line outside a {{...}} and [[...]] block-html-comments, then accumulate lines until a blank
	# Some cases not accounted for: disambiguation pages, abstracts with sentences split-across-lines, 
		# nested embedded html, 'content significant' embedded-html, markup not removable with mwparsefromhell, 
	lines = []
	openBraceCount = 0
	openBracketCount = 0
	inComment = False
	skip = False
	for line in text.splitlines():
		line = line.strip()
		if len(lines) == 0:
			if len(line) > 0:
				if openBraceCount > 0 or line[0] == "{":
					openBraceCount += line.count("{")
					openBraceCount -= line.count("}")
					skip = True
				if openBracketCount > 0 or line[0] == "[":
					openBracketCount += line.count("[")
					openBracketCount -= line.count("]")
					skip = True
				if inComment or line.find("<!--") != -1:
					if line.find("-->") != -1:
						if inComment:
							inComment = False
							skip = True
					else:
						inComment = True
						skip = True
				if skip:
					skip = False
					continue
				if line[-1] == ":": # Seems to help avoid disambiguation pages
					return None
				if descLineRegex.match(line) != None:
					lines.append(line)
		else:
			if len(line) == 0:
				return removeMarkup(" ".join(lines))
			lines.append(line)
	if len(lines) > 0:
		return removeMarkup(" ".join(lines))
	return None
def removeMarkup(content):
	content = embeddedHtmlRegex.sub("", content)
	content = convertTemplateRegex.sub(convertTemplateReplace, content)
	content = mwparserfromhell.parse(content).strip_code() # Remove wikitext markup
	content = parensGrpRegex.sub("", content)
	content = leftoverBraceRegex.sub("", content)
	return content
# Other helper functions
def convertTitle(title):
	return html.unescape(title).replace("_", " ")

# Check for existing db
if os.path.exists(enwikiDb):
	print(f"ERROR: Existing {enwikiDb}", file=sys.stderr)
	sys.exit(1)
# Create db
dbCon = sqlite3.connect(enwikiDb)
dbCur = dbCon.cursor()
dbCur.execute("CREATE TABLE pages (id INT PRIMARY KEY, title TEXT UNIQUE)")
dbCur.execute("CREATE INDEX pages_title_idx ON pages(title COLLATE NOCASE)")
dbCur.execute("CREATE TABLE redirects (id INT PRIMARY KEY, target TEXT)")
dbCur.execute("CREATE INDEX redirects_idx ON redirects(target)")
dbCur.execute("CREATE TABLE descs (id INT PRIMARY KEY, desc TEXT)")
# Read through dump file
print("Reading dump file")
with bz2.open(dumpFile, mode='rt') as file:
	dump = mwxml.Dump.from_file(file)
	pageNum = 0
	for page in dump:
		pageNum += 1
		if pageNum % 1e4 == 0:
			print(f"At page {pageNum}")
		# Parse page
		if page.namespace == 0:
			try:
				dbCur.execute("INSERT INTO pages VALUES (?, ?)", (page.id, convertTitle(page.title)))
			except sqlite3.IntegrityError as e:
				# Accounts for certain pages that have the same title
				print(f"Failed to add page with title \"{page.title}\": {e}")
				continue
			if page.redirect != None:
				dbCur.execute("INSERT INTO redirects VALUES (?, ?)", (page.id, convertTitle(page.redirect)))
			else:
				revision = next(page)
				desc = parseDesc(revision.text)
				if desc != None:
					dbCur.execute("INSERT INTO descs VALUES (?, ?)", (page.id, desc))
# Close db
dbCon.commit()
dbCon.close()
