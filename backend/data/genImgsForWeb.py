#!/usr/bin/python3

import sys, os, subprocess
import sqlite3, urllib.parse
import signal

usageInfo =  f"usage: {sys.argv[0]}\n"
usageInfo += "Reads a list of eol/enwiki images from a file, and generates web-usable versions.\n"
usageInfo += "Uses smartcrop, and places resulting images in a directory, with name 'otolId1.jpg'.\n"
usageInfo += "Also adds image metadata to an sqlite database.\n"
usageInfo += "\n"
usageInfo += "SIGINT can be used to stop conversion, and the program can be re-run to\n"
usageInfo += "continue processing. It uses existing output files to decide where to continue from.\n"
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

imgListFile = "mergedImgList.txt"
outDir = "img/"
eolImgDb = "eol/imagesList.db"
enwikiImgDb = "enwiki/enwikiImgs.db"
dbFile = "data.db"
IMG_OUT_SZ = 200

# Create output directory if not present
if not os.path.exists(outDir):
	os.mkdir(outDir)
# Open dbs
dbCon = sqlite3.connect(dbFile)
dbCur = dbCon.cursor()
eolCon = sqlite3.connect(eolImgDb)
eolCur = eolCon.cursor()
enwikiCon = sqlite3.connect(enwikiImgDb)
enwikiCur = enwikiCon.cursor()
# Create image tables if not present
nodesDone = set()
if dbCur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='images'").fetchone() == None:
	dbCur.execute("CREATE TABLE images" \
		" (id INT, src TEXT, url TEXT, license TEXT, artist TEXT, credit TEXT, PRIMARY KEY (id, src))")
	dbCur.execute("CREATE TABLE node_imgs (id TEXT PRIMARY KEY, img_id INT, src TEXT)")
else:
	# Get existing node-associations
	for (otolId,) in dbCur.execute("SELECT DISTINCT id from node_imgs"):
		nodesDone.add(otolId)
	print(f"Found {len(nodesDone)} nodes already processed")
# Detect SIGINT signals
interrupted = False
def onSigint(sig, frame):
	global interrupted
	interrupted = True
signal.signal(signal.SIGINT, onSigint)
# Iterate though images to process
with open(imgListFile) as file:
	for line in file:
		# Check for SIGINT event
		if interrupted:
			print("Exiting")
			break
		# Skip lines without an image path
		if line.find(" ") == -1:
			continue
		# Get filenames
		(otolId, _, imgPath) = line.rstrip().partition(" ")
		# Skip if already processed
		if otolId in nodesDone:
			continue
		outPath = outDir + otolId + ".jpg"
		# Convert image if needed
		convertedImage = False
		if not os.path.exists(outPath):
			print(f"{otolId}: converting {imgPath}")
			completedProcess = subprocess.run(
				['npx', 'smartcrop-cli', '--width', str(IMG_OUT_SZ), '--height', str(IMG_OUT_SZ), imgPath, outPath],
				stdout=subprocess.DEVNULL
			)
			# Prevent adding a db entry after an interrupted conversion
				# Needed because the subprocess above exits on a SIGINT (not prevented by onSigint() above)
			if completedProcess.returncode < 0:
				print("Exiting due to interrupted subprocess")
				break
			convertedImage = True
		# Add entry to db
		fromEol = imgPath.startswith("eol/")
		imgName = os.path.basename(os.path.normpath(imgPath)) # Get last path component
		imgName = os.path.splitext(imgName)[0] # Remove extension
		if fromEol:
			(eolId, _, contentId) = imgName.partition(" ")
			(eolId, contentId) = (int(eolId), int(contentId))
			if convertedImage:
				query = "SELECT source_url, license, copyright_owner FROM images WHERE content_id = ?"
				(url, license, owner) = eolCur.execute(query, (contentId,)).fetchone()
				dbCur.execute("INSERT INTO images VALUES (?, ?, ?, ?, ?, ?)",
					(eolId, "eol", url, license, owner, ""))
			dbCur.execute("INSERT INTO node_imgs VALUES (?, ?, ?)", (otolId, eolId, "eol"))
		else:
			enwikiId = int(imgName)
			if convertedImage:
				query = "SELECT name, license, artist, credit FROM" \
					" page_imgs INNER JOIN imgs ON page_imgs.img_name = imgs.name" \
					" WHERE page_imgs.page_id = ?"
				(name, license, artist, credit) = enwikiCur.execute(query, (enwikiId,)).fetchone()
				url = "https://en.wikipedia.org/wiki/File:" + urllib.parse.quote(name)
				dbCur.execute("INSERT INTO images VALUES (?, ?, ?, ?, ?, ?)",
					(enwikiId, "enwiki", url, license, artist, credit))
			dbCur.execute("INSERT INTO node_imgs VALUES (?, ?, ?)", (otolId, enwikiId, "enwiki"))
# Close dbs
dbCon.commit()
dbCon.close()
eolCon.close()
enwikiCon.close()
