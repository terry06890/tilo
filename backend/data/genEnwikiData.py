#!/usr/bin/python3

import sys, re
import sqlite3

usageInfo =  f"usage: {sys.argv[0]}\n"
usageInfo += "Reads Wikimedia enwiki data from enwiki/, a list of node names,"
usageInfo += "and node and name data from a sqlite database, and adds\n"
usageInfo += "description data for names that don't have them\n"
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

enwikiDb = "enwiki/enwikiData.db"
namesFile = "reducedTol/names.txt"
dbFile = "data.db"

# Open dbs
enwikiCon = sqlite3.connect(enwikiDb)
enwikiCur = enwikiCon.cursor()
dbCon = sqlite3.connect(dbFile)
dbCur = dbCon.cursor()
# Read in names to check
print("Getting names to check")
nodeNames = set()
with open(namesFile) as file:
	for line in file:
		nodeNames.add(line.rstrip())
print("Found {} names".format(len(nodeNames)))
# Remove names that have descriptions
print("Checking for existing name descriptions")
namesWithDescs = set()
for name in nodeNames:
	row = dbCur.execute("SELECT name FROM descs where name = ?", (name,)).fetchone()
	if row != None:
		namesWithDescs.add(name)
nodeNames.difference_update(namesWithDescs)
print("Remaining nodes: {}".format(len(nodeNames)))
# Find page id for each node name
nodeToPageId = {}
print("Getting node page-ids")
for name in nodeNames:
	row = enwikiCur.execute("SELECT id FROM pages where pages.title = ? COLLATE nocase", (name,)).fetchone()
	if row != None:
		nodeToPageId[name] = row[0]
# Resolve redirects
print("Resolving redirects")
redirectingNames = set()
for (name, pageId) in nodeToPageId.items():
	row = enwikiCur.execute("SELECT target_id FROM redirects where redirects.id = ?", (pageId,)).fetchone()
	if row != None:
		nodeToPageId[name] = row[0]
		redirectingNames.add(name)
# Add descriptions for each node
print("Adding description data")
for (name, pageId) in nodeToPageId.items():
	row = enwikiCur.execute("SELECT desc FROM descs where descs.id = ?", (pageId,)).fetchone()
	if row != None:
		dbCur.execute("INSERT INTO descs VALUES (?, ?, ?)", (name, row[0], 1 if name in redirectingNames else 0))
# Close dbs
dbCon.commit()
dbCon.close()
enwikiCon.commit()
enwikiCon.close()
