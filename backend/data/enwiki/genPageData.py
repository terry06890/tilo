#!/usr/bin/python3

import sys, os.path
from mwsql import Dump
import sqlite3

usageInfo =  f"usage: {sys.argv[0]}\n"
usageInfo += "Reads a gzipped Wikimedia enwiki 'page' table MySql dump,\n"
usageInfo += "obtaining a page-id to page-title mapping, and adds it to\n"
usageInfo += "a sqlite db.\n"
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

pageDumpFile = "enwiki-20220420-page.sql.gz"
enwikiDb = "enwikiData.db"

# Check for existing db
if os.path.exists(enwikiDb):
	print("ERROR: Existing {}".format(enwikiDb), file=sys.stderr)
	sys.exit(1)
# Create db
dbCon = sqlite3.connect(enwikiDb)
dbCur = dbCon.cursor()
dbCur.execute("CREATE TABLE pages (id INT PRIMARY KEY, title TEXT UNIQUE)")
dbCur.execute("CREATE INDEX pages_title_idx ON pages(title COLLATE NOCASE)")
# Parse page data
dump = Dump.from_file(pageDumpFile)
iterationNum = 0
for row in dump.rows(convert_dtypes=True):
	iterationNum += 1
	if iterationNum % 1e6 == 0:
		print("At iteration {}".format(iterationNum))
	# Add to map
	if row[1] == 0: # If page in article namespace
		dbCur.execute("INSERT INTO pages VALUES (?, ?)", (row[0], row[2].replace("_", " ")))
# Close db
dbCon.commit()
dbCon.close()
