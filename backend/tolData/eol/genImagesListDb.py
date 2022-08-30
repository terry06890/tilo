#!/usr/bin/python3

import sys, os, re
import csv
import sqlite3

import argparse
parser = argparse.ArgumentParser(description="""
Generates a sqlite db from a directory of CSV files holding EOL image data
""", formatter_class=argparse.RawDescriptionHelpFormatter)
parser.parse_args()

imagesListDir = "imagesList/"
dbFile = "imagesList.db"

print("Creating database")
dbCon = sqlite3.connect(dbFile)
dbCur = dbCon.cursor()
dbCur.execute("CREATE TABLE images" \
	" (content_id INT PRIMARY KEY, page_id INT, source_url TEXT, copy_url TEXT, license TEXT, copyright_owner TEXT)")
dbCur.execute("CREATE INDEX images_pid_idx ON images(page_id)")
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
