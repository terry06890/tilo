#!/usr/bin/python3

import sys, re, os
import sqlite3

usageInfo = f"""
Usage: {sys.argv[0]}

Reads a database containing data from Wikipedia, and tries to associate
wiki pages with nodes in the tree-of-life database, and add descriptions for
nodes that don't have them.
"""
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

enwikiDb = "enwiki/descData.db"
dbFile = "data.db"
namesToSkipFile = "pickedEnwikiNamesToSkip.txt"
pickedLabelsFile = "pickedEnwikiLabels.txt"
# Got about 25k descriptions when testing

print("Opening databases")
enwikiCon = sqlite3.connect(enwikiDb)
enwikiCur = enwikiCon.cursor()
dbCon = sqlite3.connect(dbFile)
dbCur = dbCon.cursor()

print("Checking for names to skip")
namesToSkip = set()
if os.path.exists(namesToSkipFile):
	with open(namesToSkipFile) as file:
		for line in file:
			namesToSkip.add(line.rstrip())
	print(f"Found {len(namesToSkip)}")
print("Checking for picked-titles")
nameToPickedTitle = {}
if os.path.exists(pickedLabelsFile):
	with open(pickedLabelsFile) as file:
		for line in file:
			(name, _, title) = line.rstrip().partition("|")
			nameToPickedTitle[name.lower()] = title
print(f"Found {len(nameToPickedTitle)}")

print("Getting names of nodes without descriptions")
nodeNames = set()
query = "SELECT nodes.name FROM nodes LEFT JOIN wiki_ids ON nodes.name = wiki_ids.name WHERE wiki_ids.id IS NULL"
for (name,) in dbCur.execute(query):
	nodeNames.add(name)
print(f"Found {len(nodeNames)}")
nodeNames.difference_update(namesToSkip)

print("Associating nodes with page IDs")
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

print("Resolving redirects")
redirectingNames = set()
iterNum = 0
for (name, pageId) in nodeToPageId.items():
	iterNum += 1
	if iterNum % 1e3 == 0:
		print(f"At iteration {iterNum}")
	#
	query = "SELECT pages.id FROM redirects INNER JOIN pages ON redirects.target = pages.title WHERE redirects.id = ?"
	row = enwikiCur.execute(query, (pageId,)).fetchone()
	if row != None:
		nodeToPageId[name] = row[0]
		redirectingNames.add(name)

print("Adding description data")
iterNum = 0
for (name, pageId) in nodeToPageId.items():
	iterNum += 1
	if iterNum % 1e3 == 0:
		print(f"At iteration {iterNum}")
	#
	row = enwikiCur.execute("SELECT desc FROM descs where descs.id = ?", (pageId,)).fetchone()
	if row != None:
		dbCur.execute("INSERT INTO wiki_ids VALUES (?, ?, ?)", (name, pageId, 1 if name in redirectingNames else 0))
		dbCur.execute("INSERT OR IGNORE INTO descs VALUES (?, ?, ?)", (pageId, row[0], 0))

print("Closing databases")
dbCon.commit()
dbCon.close()
enwikiCon.close()
