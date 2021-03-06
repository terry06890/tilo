#!/usr/bin/python3

import sys, os, re
import bz2
import html, mwxml, mwparserfromhell
import sqlite3

usageInfo = f"""
Usage: {sys.argv[0]}

Reads through the wiki dump, and attempts to
parse short-descriptions, and add them to a database.
"""
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

dumpFile = "enwiki-20220501-pages-articles-multistream.xml.bz2" # Had about 22e6 pages
enwikiDb = "descData.db"
# In testing, this script took over 10 hours to run, and generated about 5GB

descLineRegex = re.compile("^ *[A-Z'\"]")
embeddedHtmlRegex = re.compile(r"<[^<]+/>|<!--[^<]+-->|<[^</]+>([^<]*|[^<]*<[^<]+>[^<]*)</[^<]+>|<[^<]+$")
	# Recognises a self-closing HTML tag, a tag with 0 children, tag with 1 child with 0 children, or unclosed tag
convertTemplateRegex = re.compile(r"{{convert\|(\d[^|]*)\|(?:(to|-)\|(\d[^|]*)\|)?([a-z][^|}]*)[^}]*}}")
def convertTemplateReplace(match):
	if match.group(2) == None:
		return f"{match.group(1)} {match.group(4)}"
	else:
		return f"{match.group(1)} {match.group(2)} {match.group(3)} {match.group(4)}"
parensGroupRegex = re.compile(r" \([^()]*\)")
leftoverBraceRegex = re.compile(r"(?:{\||{{).*")

def parseDesc(text):
	# Find first matching line outside {{...}}, [[...]], and block-html-comment constructs,
		# and then accumulate lines until a blank one.
	# Some cases not accounted for include: disambiguation pages, abstracts with sentences split-across-lines, 
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
	content = parensGroupRegex.sub("", content)
	content = leftoverBraceRegex.sub("", content)
	return content
def convertTitle(title):
	return html.unescape(title).replace("_", " ")

print("Creating database")
if os.path.exists(enwikiDb):
	raise Exception(f"ERROR: Existing {enwikiDb}")
dbCon = sqlite3.connect(enwikiDb)
dbCur = dbCon.cursor()
dbCur.execute("CREATE TABLE pages (id INT PRIMARY KEY, title TEXT UNIQUE)")
dbCur.execute("CREATE INDEX pages_title_idx ON pages(title COLLATE NOCASE)")
dbCur.execute("CREATE TABLE redirects (id INT PRIMARY KEY, target TEXT)")
dbCur.execute("CREATE INDEX redirects_idx ON redirects(target)")
dbCur.execute("CREATE TABLE descs (id INT PRIMARY KEY, desc TEXT)")

print("Iterating through dump file")
with bz2.open(dumpFile, mode='rt') as file:
	dump = mwxml.Dump.from_file(file)
	pageNum = 0
	for page in dump:
		pageNum += 1
		if pageNum % 1e4 == 0:
			print(f"At page {pageNum}")
		if pageNum > 3e4:
			break
		# Parse page
		if page.namespace == 0:
			try:
				dbCur.execute("INSERT INTO pages VALUES (?, ?)", (page.id, convertTitle(page.title)))
			except sqlite3.IntegrityError as e:
				# Accounts for certain pages that have the same title
				print(f"Failed to add page with title \"{page.title}\": {e}", file=sys.stderr)
				continue
			if page.redirect != None:
				dbCur.execute("INSERT INTO redirects VALUES (?, ?)", (page.id, convertTitle(page.redirect)))
			else:
				revision = next(page)
				desc = parseDesc(revision.text)
				if desc != None:
					dbCur.execute("INSERT INTO descs VALUES (?, ?)", (page.id, desc))

print("Closing database")
dbCon.commit()
dbCon.close()
