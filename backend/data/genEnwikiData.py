#!/usr/bin/python3

import sys, re
import sqlite3

usageInfo =  f"usage: {sys.argv[0]}\n"
usageInfo += "Reads Wikimedia enwiki data from enwiki/, along with node and name data\n"
usageInfo += "from a sqlite database, associates nodes with enwiki pages, and adds\n"
usageInfo += "alt-name and description information for those nodes.\n"
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

enwikiDb = "enwiki/enwikiData.db"
dbFile = "data.db"

# Open dbs
enwikiCon = sqlite3.connect(enwikiDb)
enwikiCur = enwikiCon.cursor()
dbCon = sqlite3.connect(dbFile)
dbCur = dbCon.cursor()
# Find page id for each node name
nodeToPageId = {}
print("Getting node page-ids")
iterationNum = 0
for row in dbCur.execute("SELECT name from nodes"):
	iterationNum += 1
	if iterationNum % 1e4 == 0:
		print("At iteration {}".format(iterationNum))
	#
	name = row[0]
	row = enwikiCur.execute("SELECT id FROM pages where pages.title = ? COLLATE nocase", (name,)).fetchone()
	if row != None:
		nodeToPageId[name] = row[0]
# Resolve redirects
print("Resolving redirects")
redirectingNames = set()
iterationNum = 0
for (name, pageId) in nodeToPageId.items():
	iterationNum += 1
	if iterationNum % 1e4 == 0:
		print("At iteration {}".format(iterationNum))
	#
	row = enwikiCur.execute("SELECT target_id FROM redirects where redirects.id = ?", (pageId,)).fetchone()
	if row != None:
		nodeToPageId[name] = row[0]
		redirectingNames.add(name)
# Add descriptions for each node
print("Adding node description data")
dbCur.execute("CREATE TABLE descs (name TEXT PRIMARY KEY, desc TEXT, redirected INT)")
iterationNum = 0
for (name, pageId) in nodeToPageId.items():
	iterationNum += 1
	if iterationNum % 1e4 == 0:
		print("At iteration {}".format(iterationNum))
	#
	row = enwikiCur.execute("SELECT desc FROM descs where descs.id = ?", (pageId,)).fetchone()
	if row != None:
		dbCur.execute("INSERT INTO descs VALUES (?, ?, ?)", (name, row[0], 1 if name in redirectingNames else 0))
# Close dbs
dbCon.commit()
dbCon.close()
enwikiCon.commit()
enwikiCon.close()
