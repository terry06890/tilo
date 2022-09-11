#!/usr/bin/python3

"""
For some set of EOL IDs, downloads associated images from URLs in
an image-list database. Uses multiple downloading threads.

May obtain multiple images per ID. The images will get names
with the form 'eolId1 contentId1.ext1'.

SIGINT causes the program to finish ongoing downloads and exit.
The program can be re-run to continue downloading. It looks for
already-downloaded files, and continues after the one with
highest EOL ID.
"""

import sys, re, os, random
import sqlite3
import urllib.parse, requests
import time
from threading import Thread
import signal

IMAGES_LIST_DB = 'images_list.db'
OUT_DIR = 'imgs_for_review'
DB_FILE = os.path.join('..', 'data.db')
#
MAX_IMGS_PER_ID = 3
MAX_THREADS = 5
POST_DL_DELAY_MIN = 2 # Minimum delay in seconds to pause after download before starting another (for each thread)
POST_DL_DELAY_MAX = 3
LICENSE_REGEX = r'cc-by((-nc)?(-sa)?(-[234]\.[05])?)|cc-publicdomain|cc-0-1\.0|public domain'

def downloadImgs(eolIds, imagesListDb, outDir):
	print('Getting EOL IDs to download for')
	# Get IDs from images-list db
	imgDbCon = sqlite3.connect(imagesListDb)
	imgCur = imgDbCon.cursor()
	imgListIds: set[int] = set()
	for (pageId,) in imgCur.execute('SELECT DISTINCT page_id FROM images'):
		imgListIds.add(pageId)
	# Get set intersection, and sort into list
	eolIds = eolIds.intersection(imgListIds)
	eolIdList = sorted(eolIds)
	nextIdx = 0
	print(f'Result: {len(eolIdList)} EOL IDs')
	#
	print('Checking output directory')
	if not os.path.exists(outDir):
		os.mkdir(outDir)
	else:
		print('Finding next ID to download for')
		fileList = os.listdir(outDir)
		ids = [int(filename.split(' ')[0]) for filename in fileList]
		if ids:
			ids.sort()
			nextIdx = eolIdList.index(ids[-1]) + 1
	if nextIdx == len(eolIdList):
		print('No IDs left. Exiting...')
		return
	#
	print('Starting download threads')
	numThreads = 0
	threadException: Exception | None = None # Used for ending main thread after a non-main thread exception
	# Handle SIGINT signals
	interrupted = False
	oldHandler = None
	def onSigint(sig, frame):
		nonlocal interrupted
		interrupted = True
		signal.signal(signal.SIGINT, oldHandler)
	oldHandler = signal.signal(signal.SIGINT, onSigint)
	# Function for threads to execute
	def downloadImg(url, outFile):
		nonlocal numThreads, threadException
		try:
			data = requests.get(url)
			with open(outFile, 'wb') as file:
				file.write(data.content)
			time.sleep(random.random() * (POST_DL_DELAY_MAX - POST_DL_DELAY_MIN) + POST_DL_DELAY_MIN)
		except Exception as e:
			print(f'Error while downloading to {outFile}: {str(e)}', file=sys.stderr)
			threadException = e
		numThreads -= 1
	# Manage downloading
	for idx in range(nextIdx, len(eolIdList)):
		eolId = eolIdList[idx]
		# Get image urls
		ownerSet: set[str] = set() # Used to get images from different owners, for variety
		exitLoop = False
		query = 'SELECT content_id, copy_url, license, copyright_owner FROM images WHERE page_id = ?'
		for contentId, url, license, copyrightOwner in imgCur.execute(query, (eolId,)):
			if url.startswith('data/'):
				url = 'https://content.eol.org/' + url
			urlParts = urllib.parse.urlparse(url)
			extension = os.path.splitext(urlParts.path)[1]
			if len(extension) <= 1:
				print(f'WARNING: No filename extension found in URL {url}', file=sys.stderr)
				continue
			# Check image-quantity limit
			if len(ownerSet) == MAX_IMGS_PER_ID:
				break
			# Check for skip conditions
			if re.fullmatch(LICENSE_REGEX, license) is None:
				continue
			if len(copyrightOwner) > 100: # Avoid certain copyrightOwner fields that seem long and problematic
				continue
			if copyrightOwner in ownerSet:
				continue
			ownerSet.add(copyrightOwner)
			# Determine output filename
			outPath = os.path.join(outDir, f'{eolId} {contentId}{extension}')
			if os.path.exists(outPath):
				print(f'WARNING: {outPath} already exists. Skipping download.')
				continue
			# Check thread limit
			while numThreads == MAX_THREADS:
				time.sleep(1)
			# Wait for threads after an interrupt or thread-exception
			if interrupted or threadException is not None:
				print('Waiting for existing threads to end')
				while numThreads > 0:
					time.sleep(1)
				exitLoop = True
				break
			# Perform download
			print(f'Downloading image to {outPath}')
			numThreads += 1
			thread = Thread(target=downloadImg, args=(url, outPath), daemon=True)
			thread.start()
		if exitLoop:
			break
	# Close images-list db
	while numThreads > 0:
		time.sleep(1)
	print('Finished downloading')
	imgDbCon.close()

def getEolIdsFromDb(dbFile) -> set[int]:
	eolIds: set[int] = set()
	dbCon = sqlite3.connect(dbFile)
	dbCur = dbCon.cursor()
	for (id,) in dbCur.execute('SELECT id FROM eol_ids'):
		eolIds.add(id)
	dbCon.close()
	return eolIds
if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.parse_args()
	#
	eolIds = getEolIdsFromDb(DB_FILE)
	downloadImgs(eolIds, IMAGES_LIST_DB, OUT_DIR)
