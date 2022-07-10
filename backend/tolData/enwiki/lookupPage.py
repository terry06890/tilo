#!/usr/bin/python3

import sys, re
import bz2
import sqlite3

usageInfo = f"""
Usage: {sys.argv[0]} title1

Looks up a page with title title1 in the wiki dump, using
the dump-index db, and prints the corresponding <page>.
"""
if len(sys.argv) != 2:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

dumpFile = "enwiki-20220501-pages-articles-multistream.xml.bz2"
indexDb = "dumpIndex.db"
pageTitle = sys.argv[1].replace("_", " ")

print("Looking up offset in index db")
dbCon = sqlite3.connect(indexDb)
dbCur = dbCon.cursor()
query = "SELECT title, offset, next_offset FROM offsets WHERE title = ?"
row = dbCur.execute(query, (pageTitle,)).fetchone()
if row == None:
	print("Title not found")
	sys.exit(0)
_, pageOffset, endOffset = row
dbCon.close()
print(f"Found chunk at offset {pageOffset}")

print("Reading from wiki dump")
content = []
with open(dumpFile, mode='rb') as file:
	# Get uncompressed chunk
	file.seek(pageOffset)
	compressedData = file.read(None if endOffset == -1 else endOffset - pageOffset)
	data = bz2.BZ2Decompressor().decompress(compressedData).decode()
	# Look in chunk for page
	lines = data.splitlines()
	lineIdx = 0
	found = False
	pageNum = 0
	while not found:
		line = lines[lineIdx]
		if line.lstrip() == "<page>":
			pageNum += 1
			if pageNum > 100:
				print("ERROR: Did not find title after 100 pages")
				break
			lineIdx += 1
			titleLine = lines[lineIdx]
			if titleLine.lstrip() == '<title>' + pageTitle + '</title>':
				found = True
				print(f"Found title in chunk as page {pageNum}")
				content.append(line)
				content.append(titleLine)
				while True:
					lineIdx += 1
					line = lines[lineIdx]
					content.append(line)
					if line.lstrip() == "</page>":
						break
		lineIdx += 1

print("Content: ")
print("\n".join(content))
