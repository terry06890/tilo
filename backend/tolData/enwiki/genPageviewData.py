#!/usr/bin/python3

import sys, os, glob, math, re
from collections import defaultdict
import bz2, sqlite3

import argparse
parser = argparse.ArgumentParser(description="""
Reads through wikimedia files containing pageview counts,
computes average counts, and adds them to a database
""", formatter_class=argparse.RawDescriptionHelpFormatter)
args = parser.parse_args()

pageviewFiles = glob.glob('./pageviews/pageviews-*-user.bz2')
dbFile = 'pageviewData.db'
dumpIndexDb = 'dumpIndex.db'

# Took about 15min per file (each about 180e6 lines)

if os.path.exists(dbFile):
	print('ERROR: Database already exists')
	sys.exit(1)

# Each pageview file has lines that seem to hold these space-separated fields:
	# wiki code (eg: en.wikipedia), article title, page ID (may be: null),
	# platform (eg: mobile-web), monthly view count,
	# hourly count string (eg: A1B2 means 1 view on day 1 and 2 views on day 2)
namespaceRegex = re.compile(r'[a-zA-Z]+:')
titleToViews: dict[str, int] = defaultdict(int)
linePrefix = b'en.wikipedia '
for filename in pageviewFiles:
	print(f'Reading from {filename}')
	with bz2.open(filename, 'rb') as file:
		for lineNum, line in enumerate(file, 1):
			if lineNum % 1e6 == 0:
				print(f'At line {lineNum}')
			if not line.startswith(linePrefix):
				continue
			# Get second and second-last fields
			line = line[len(linePrefix):line.rfind(b' ')] # Remove first and last fields
			title = line[:line.find(b' ')].decode('utf-8')
			viewCount = int(line[line.rfind(b' ')+1:])
			if namespaceRegex.match(title) is not None:
				continue
			# Update map
			titleToViews[title] += viewCount
print(f'Found {len(titleToViews)} titles')

print('Writing to db')
dbCon = sqlite3.connect(dbFile)
dbCur = dbCon.cursor()
idbCon = sqlite3.connect(dumpIndexDb)
idbCur = idbCon.cursor()
dbCur.execute('CREATE TABLE views (title TEXT PRIMARY KEY, id INT, views INT)')
for title, views in titleToViews.items():
	row = idbCur.execute('SELECT id FROM offsets WHERE title = ?', (title,)).fetchone()
	if row is not None:
		wikiId = int(row[0])
		dbCur.execute('INSERT INTO views VALUES (?, ?, ?)', (title, wikiId, math.floor(views / len(pageviewFiles))))
dbCon.commit()
dbCon.close()
idbCon.close()
