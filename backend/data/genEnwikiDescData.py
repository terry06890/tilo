#!/usr/bin/python3

import sys, re
import sqlite3

usageInfo =  f"usage: {sys.argv[0]}\n"
usageInfo += "Reads Wikimedia enwiki data from enwiki/, and node and name data"
usageInfo += "from a sqlite database, and adds description data for names that\n"
usageInfo += "don't have them.\n"
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

enwikiDb = "enwiki/enwikiData.db"
dbFile = "data.db"
namesToSkipFile = "genEnwikiDescNamesToSkip.txt"
titlesToUseFile = "genEnwikiDescTitlesToUse.txt"
titleToUseRegex = re.compile(r"(.*) \(.*\)")

# Open dbs
enwikiCon = sqlite3.connect(enwikiDb)
enwikiCur = enwikiCon.cursor()
dbCon = sqlite3.connect(dbFile)
dbCur = dbCon.cursor()
# Read name/title files
namesToSkip = set()
nameToPickedTitle = {} # Maps names to titles to be used for them
if os.path.exists(namesToSkipFile):
	with open(namesToSkipFile) as file:
		for line in file:
			namesToSkip.add(line.rstrip())
	print("Read in {len(namesToSkip)} names to skip")
if os.path.exists(titlesToUseFile):
	with open(titlesToUseFile) as file:
		for line in file:
			title = line.rstrip()
			name = titleToUseRegex.sub(r"\1", title) # Remove parens
			nameToPickedTitle[name.lower()] = title
print("Read in {len(titlesToUse)} titles to use for certain names")
# Get node names without descriptions
print("Getting node names")
nodeNames = set()
query = "SELECT nodes.name FROM nodes LEFT JOIN descs ON nodes.name = descs.name WHERE desc IS NULL"
for row in dbCur.execute(query):
	nodeNames.add(row[0])
print(f"Found {len(nodeNames)} names")
nodeNames.difference_update(namesToSkip)
# Find page id for each node name
print("Getting node page-ids")
nodeToPageId = {}
iterNum = 0
for name in nodeNames:
	iterNum += 1
	if iterNum % 1e4 == 0:
		print(f"At iteration {iterNum}")
	#
	if name not in nameToPickedTitle:
		row = enwikiCur.execute("SELECT id FROM pages WHERE pages.title = ? COLLATE NOCASE", (name,)).fetchone()
		if row != None:
			nodeToPageId[name] = row[0]
	else:
		title = nameToPickedTitle[name]
		row = enwikiCur.execute("SELECT id FROM pages WHERE pages.title = ?", (title,)).fetchone()
		if row != None:
			nodeToPageId[name] = row[0]
		else:
			print("WARNING: Picked title {title} not found", file=sys.stderr)
# Resolve redirects
print("Resolving redirects")
redirectingNames = set()
iterNum = 0
for (name, pageId) in nodeToPageId.items():
	iterNum += 1
	if iterNum % 1000 == 0:
		print(f"At iteration {iterNum}")
	#
	row = enwikiCur.execute(
		"SELECT pages.id FROM redirects INNER JOIN pages ON redirects.target = pages.title WHERE redirects.id = ?",
		(pageId,)).fetchone()
	if row != None:
		nodeToPageId[name] = row[0]
		redirectingNames.add(name)
# Add descriptions for each node
print("Adding description data")
iterNum = 0
for (name, pageId) in nodeToPageId.items():
	iterNum += 1
	if iterNum % 1000 == 0:
		print(f"At iteration {iterNum}")
	#
	row = enwikiCur.execute("SELECT desc FROM descs where descs.id = ?", (pageId,)).fetchone()
	if row != None:
		dbCur.execute("INSERT INTO descs VALUES (?, ?, ?, ?, ?)",
			(name, row[0], 1 if name in redirectingNames else 0, pageId, 0))
# Close dbs
dbCon.commit()
dbCon.close()
enwikiCon.close()
