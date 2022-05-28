#!/usr/bin/python3

import sys, re, os, random
import sqlite3
import urllib.parse, requests
import time
from threading import Thread
import signal

usageInfo =  f"usage: {sys.argv[0]}\n"
usageInfo += "Downloads images from URLs specified in an image-list database, using\n"
usageInfo += "EOL IDs obtained from another database. Downloaded images get names of\n"
usageInfo += "the form 'eolId1 contentId1.ext1'\n"
usageInfo += "\n"
usageInfo += "SIGINT causes the program to finish ongoing downloads and exit.\n"
usageInfo += "The program can be re-run to continue downloading, and uses\n"
usageInfo += "existing downloaded files to decide where to continue from.\n"
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

imagesListDb = "eol/imagesList.db"
dbFile = "data.db"
outDir = "imgsForReview/"
LICENSE_REGEX = r"cc-by((-nc)?(-sa)?(-[234]\.[05])?)|cc-publicdomain|cc-0-1\.0|public domain"
POST_DL_DELAY_MIN = 2 # Minimum delay in seconds to pause after download before starting another (for each thread)
POST_DL_DELAY_MAX = 3

# Get eol-ids from data db
eolIds = set()
print("Reading in EOL IDs")
dbCon = sqlite3.connect(dbFile)
dbCur = dbCon.cursor()
for row in dbCur.execute("SELECT id FROM eol_ids"):
	eolIds.add(row[0])
dbCon.close()
# Get eol-ids from images db
imgDbCon = sqlite3.connect(imagesListDb)
imgCur = imgDbCon.cursor()
imgListIds = set()
for row in imgCur.execute("SELECT DISTINCT page_id FROM images"):
	imgListIds.add(row[0])
# Get eol-id intersection, and sort into list
eolIds = eolIds.intersection(imgListIds)
eolIds = sorted(eolIds)

MAX_IMGS_PER_ID = 3
MAX_THREADS = 5
numThreads = 0
threadException = None # Used for ending main thread after a non-main thread exception
def downloadImg(url, outFile):
	global numThreads, threadException
	try:
		data = requests.get(url)
		with open(outFile, 'wb') as file:
			file.write(data.content)
		time.sleep(random.random() * (POST_DL_DELAY_MAX - POST_DL_DELAY_MIN) + POST_DL_DELAY_MIN)
	except Exception as e:
		print(f"Error while downloading to {outFile}: {str(e)}", file=sys.stderr)
		threadException = e
	numThreads -= 1
# Create output directory if not present
if not os.path.exists(outDir):
	os.mkdir(outDir)
# Find next eol ID to download for
print("Finding next ID to download for")
nextIdx = 0
fileList = os.listdir(outDir)
ids = [int(filename.split(" ")[0]) for filename in fileList]
if len(ids) > 0:
	ids.sort()
	nextIdx = eolIds.index(ids[-1]) + 1
if nextIdx == len(eolIds):
	print("No IDs left. Exiting...")
	sys.exit(0)
# Detect SIGINT signals
interrupted = False
oldHandler = None
def onSigint(sig, frame):
	global interrupted
	interrupted = True
	signal.signal(signal.SIGINT, oldHandler)
oldHandler = signal.signal(signal.SIGINT, onSigint)
# Manage downloading
for idx in range(nextIdx, len(eolIds)):
	eolId = eolIds[idx]
	# Get image urls
	imgDataList = []
	ownerSet = set() # Used to get images from different owners, for variety
	for row in imgCur.execute(
		"SELECT content_id, page_id, copy_url, license, copyright_owner FROM images WHERE page_id = ?", (eolId,)):
		license = row[3]
		copyrightOwner = row[4]
		if re.fullmatch(LICENSE_REGEX, license) == None:
			continue
		if len(copyrightOwner) > 100: # Ignore certain copyrightOwner fields that seem long and problematic
			continue
		if copyrightOwner not in ownerSet:
			ownerSet.add(copyrightOwner)
			imgDataList.append(row)
			if len(ownerSet) == MAX_IMGS_PER_ID:
				break
	if len(imgDataList) == 0:
		continue
	# Determine output filenames
	outFiles = []
	urls = []
	for row in imgDataList:
		contentId = row[0]
		url = row[2]
		if url.startswith("data/"):
			url = "https://content.eol.org/" + url
		urlParts = urllib.parse.urlparse(url)
		extension = os.path.splitext(urlParts.path)[1]
		if len(extension) <= 1:
			print(f"WARNING: No filename extension found in URL {url}", file=sys.stderr)
			continue
		outFiles.append(str(eolId) + " " + str(contentId) + extension)
		urls.append(url)
	# Start downloads
	exitLoop = False
	for i in range(len(outFiles)):
		outPath = outDir + outFiles[i]
		if not os.path.exists(outPath):
			# Enforce thread limit
			while numThreads == MAX_THREADS:
				time.sleep(1)
			# Wait for threads after an interrupt or thread-exception
			if interrupted or threadException != None:
				print("Waiting for existing threads to end")
				while numThreads > 0:
					time.sleep(1)
				exitLoop = True
				break
			print("Downloading image to {outPath}")
			# Perform download
			numThreads += 1
			thread = Thread(target=downloadImg, args=(urls[i], outPath), daemon=True)
			thread.start()
	if exitLoop:
		break
# Close images-list db
print("Finished downloading")
imgDbCon.close()
