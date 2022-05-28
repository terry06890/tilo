#!/usr/bin/python3

import sys, os, re
import bz2
import sqlite3

usageInfo =  f"usage: {sys.argv[0]}\n"
usageInfo += "Reads a Wikimedia enwiki dump index file,\n"
usageInfo += "and stores it's offset and title data to an sqlite db.\n"
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

indexFile = "enwiki-20220501-pages-articles-multistream-index.txt.bz2" # 22,034,540 lines
indexDb = "dumpIndex.db"

# Check for existing db
if os.path.exists(indexDb):
	print(f"ERROR: Existing {indexDb}", file=sys.stderr)
	sys.exit(1)
# Create db
dbCon = sqlite3.connect(indexDb)
dbCur = dbCon.cursor()
dbCur.execute("CREATE TABLE offsets (title TEXT PRIMARY KEY, offset INT, next_offset INT)")
# Reading index file
lineRegex = re.compile(r"([^:]+):([^:]+):(.*)")
lastOffset = 0
lineNum = 0
titlesToAdd = []
with bz2.open(indexFile, mode='rt') as file:
	for line in file:
		lineNum += 1
		if lineNum % 1e5 == 0:
			print(f"At line {lineNum}")
		#
		match = lineRegex.fullmatch(line.rstrip())
		(offset, _, title) = match.group(1,2,3)
		offset = int(offset)
		if offset > lastOffset:
			for t in titlesToAdd:
				try:
					dbCur.execute("INSERT INTO offsets VALUES (?, ?, ?)", (t, lastOffset, offset))
				except sqlite3.IntegrityError as e:
					# Accounts for certain entries in the file that have the same title
					print(f"Failed on title \"{t}\": {e}")
			titlesToAdd = []
			lastOffset = offset
		titlesToAdd.append(title)
for title in titlesToAdd:
	try:
		dbCur.execute("INSERT INTO offsets VALUES (?, ?, ?)", (title, lastOffset, -1))
	except sqlite3.IntegrityError as e:
		print(f"Failed on title \"{t}\": {e}")
# Close db
dbCon.commit()
dbCon.close()
