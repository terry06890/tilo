#!/usr/bin/python3

import sys, os, re
import csv
import sqlite3

usageInfo = f"""
Usage: {sys.argv[0]}

Generates a sqlite db from a directory of CSV files holding EOL image data
"""
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

imagesListDir = "imagesList/"
dbFile = "imagesList.db"

print("Creating database")
dbCon = sqlite3.connect(dbFile)
dbCur = dbCon.cursor()
dbCur.execute("CREATE TABLE images" \
	" (content_id INT PRIMARY KEY, page_id INT, source_url TEXT, copy_url TEXT, license TEXT, copyright_owner TEXT)")
print("Reading CSV files")
csvFilenames = os.listdir(imagesListDir)
for filename in csvFilenames:
	print(f"Processing {imagesListDir}{filename}")
	with open(imagesListDir + filename, newline="") as file:
		for (contentId, pageId, sourceUrl, copyUrl, license, owner) in csv.reader(file):
			if re.match(r"^[a-zA-Z]", contentId): # Skip header line
				continue
			dbCur.execute("INSERT INTO images VALUES (?, ?, ?, ?, ?, ?)",
				(int(contentId), int(pageId), sourceUrl, copyUrl, license, owner))
print("Closing database")
dbCon.commit()
dbCon.close()
