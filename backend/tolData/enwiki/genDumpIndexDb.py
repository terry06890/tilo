#!/usr/bin/python3

import sys, os, re
import bz2
import sqlite3

import argparse
parser = argparse.ArgumentParser(description="""
Adds data from the wiki dump index-file into a database
""", formatter_class=argparse.RawDescriptionHelpFormatter)
parser.parse_args()

indexFile = "enwiki-20220501-pages-articles-multistream-index.txt.bz2" # Had about 22e6 lines
indexDb = "dumpIndex.db"

if os.path.exists(indexDb):
	raise Exception(f"ERROR: Existing {indexDb}")
print("Creating database")
dbCon = sqlite3.connect(indexDb)
dbCur = dbCon.cursor()
dbCur.execute("CREATE TABLE offsets (title TEXT PRIMARY KEY, id INT UNIQUE, offset INT, next_offset INT)")

print("Iterating through index file")
lineRegex = re.compile(r"([^:]+):([^:]+):(.*)")
lastOffset = 0
lineNum = 0
entriesToAdd = []
with bz2.open(indexFile, mode='rt') as file:
	for line in file:
		lineNum += 1
		if lineNum % 1e5 == 0:
			print(f"At line {lineNum}")
		#
		match = lineRegex.fullmatch(line.rstrip())
		(offset, pageId, title) = match.group(1,2,3)
		offset = int(offset)
		if offset > lastOffset:
			for (t, p) in entriesToAdd:
				try:
					dbCur.execute("INSERT INTO offsets VALUES (?, ?, ?, ?)", (t, p, lastOffset, offset))
				except sqlite3.IntegrityError as e:
					# Accounts for certain entries in the file that have the same title
					print(f"Failed on title \"{t}\": {e}", file=sys.stderr)
			entriesToAdd = []
			lastOffset = offset
		entriesToAdd.append([title, pageId])
for (title, pageId) in entriesToAdd:
	try:
		dbCur.execute("INSERT INTO offsets VALUES (?, ?, ?, ?)", (title, pageId, lastOffset, -1))
	except sqlite3.IntegrityError as e:
		print(f"Failed on title \"{t}\": {e}", file=sys.stderr)

print("Closing database")
dbCon.commit()
dbCon.close()
