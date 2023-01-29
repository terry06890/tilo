#!/usr/bin/python3

"""
Generates a sqlite db from a directory of CSV files holding EOL image data
"""

import argparse
import os
import glob
import csv
import re
import sqlite3

IMAGE_LISTS_GLOB = os.path.join('imagesList', '*.csv')
DB_FILE = 'images_list.db'

def genData(imageListsGlob: str, dbFile: str) -> None:
	print('Creating database')
	dbCon = sqlite3.connect(dbFile)
	dbCur = dbCon.cursor()
	dbCur.execute('CREATE TABLE images' \
		' (content_id INT PRIMARY KEY, page_id INT, source_url TEXT,' \
			' copy_url TEXT, license TEXT, copyright_owner TEXT)')
	dbCur.execute('CREATE INDEX images_pid_idx ON images(page_id)')

	print('Reading CSV files')
	for filename in glob.glob(imageListsGlob):
		print(f'Processing {filename}')
		with open(filename, newline='') as file:
			for contentId, pageId, sourceUrl, copyUrl, license, owner in csv.reader(file):
				if re.match(r'^[a-zA-Z]', contentId): # Skip header line (not in all files)
					continue
				dbCur.execute('INSERT INTO images VALUES (?, ?, ?, ?, ?, ?)',
					(int(contentId), int(pageId), sourceUrl, copyUrl, license, owner))

	print('Closing database')
	dbCon.commit()
	dbCon.close()

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.parse_args()

	genData(IMAGE_LISTS_GLOB, DB_FILE)
