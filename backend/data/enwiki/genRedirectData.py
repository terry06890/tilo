#!/usr/bin/python3

import sys, os.path
from mwsql import Dump
import sqlite3

usageInfo =  f"usage: {sys.argv[0]}\n"
usageInfo += "Reads a gzipped Wikimedia enwiki 'redirect' table MySql dump,\n"
usageInfo += "obtaining a page-id to redirect-page-id mapping, and adds it to\n"
usageInfo += "a sqlite db.\n"
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

redirectDumpFile = "enwiki-20220420-redirect.sql.gz"
enwikiDb = "enwikiData.db"

# Open db
dbCon = sqlite3.connect(enwikiDb)
dbCur = dbCon.cursor()
dbCur.execute("CREATE TABLE redirects (id INT PRIMARY KEY, target_id INT)")
dbCur2 = dbCon.cursor()
# Parse redirect data
dump = Dump.from_file(redirectDumpFile)
iterationNum = 0
for row in dump.rows(convert_dtypes=True):
	iterationNum += 1
	if iterationNum % 1e6 == 0:
		print("At iteration {}".format(iterationNum))
	# Add to map
	[pageId, namespace, title] = row[:3]
	if namespace == 0: # If page is in the article namespace
		row = dbCur2.execute("SELECT id from pages where pages.title = ?", (title.replace("_", " "),)).fetchone()
		if row != None:
			targetId = row[0]
			dbCur.execute("INSERT INTO redirects VALUES (?, ?)", (pageId, targetId))
# Close db
dbCon.commit()
dbCon.close()
