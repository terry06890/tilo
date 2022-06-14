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
imgsDone = set()
if dbCur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='node_imgs'").fetchone() == None:
	dbCur.execute("CREATE TABLE node_imgs (id TEXT PRIMARY KEY, img_id INT, src TEXT)")
	dbCur.execute("CREATE TABLE images" \
		" (id INT, src TEXT, url TEXT, license TEXT, artist TEXT, credit TEXT, PRIMARY KEY (id, src))")
else:
	# Get existing node-associations
	for (otolId,) in dbCur.execute("SELECT id from node_imgs"):
		nodesDone.add(otolId)
	# And images
	for (imgId, imgSrc) in dbCur.execute("SELECT id, src from images"):
		imgsDone.add((imgId, imgSrc))
	print(f"Found {len(nodesDone)} nodes and {len(imgsDone)} images pre-existing")
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
		# Convert image
		print(f"{otolId}: converting {imgPath}")
		if os.path.exists(outPath):
			print(f"ERROR: Output image already exists")
			break
		try:
			completedProcess = subprocess.run(
				['npx', 'smartcrop-cli', '--width', str(IMG_OUT_SZ), '--height', str(IMG_OUT_SZ), imgPath, outPath],
				stdout=subprocess.DEVNULL)
		except Exception as e:
			print(f"ERROR: Exception while attempting to run smartcrop: {e}")
			break
		if completedProcess.returncode != 0:
			print(f"ERROR: smartcrop had exit status {completedProcess.returncode}")
			break
		# Add entry to db
		fromEol = imgPath.startswith("eol/")
		imgName = os.path.basename(os.path.normpath(imgPath)) # Get last path component
		imgName = os.path.splitext(imgName)[0] # Remove extension
		if fromEol:
			(eolId, _, contentId) = imgName.partition(" ")
			(eolId, contentId) = (int(eolId), int(contentId))
			if (eolId, "eol") not in imgsDone:
				query = "SELECT source_url, license, copyright_owner FROM images WHERE content_id = ?"
				row = eolCur.execute(query, (contentId,)).fetchone()
				if row == None:
					print("ERROR: No image record for EOL ID {eolId}, content ID {contentId}", file=sys.stderr)
					break
				(url, license, owner) = row
				dbCur.execute("INSERT INTO images VALUES (?, ?, ?, ?, ?, ?)",
					(eolId, "eol", url, license, owner, ""))
				imgsDone.add((eolId, "eol"))
			dbCur.execute("INSERT INTO node_imgs VALUES (?, ?, ?)", (otolId, eolId, "eol"))
		else:
			enwikiId = int(imgName)
			if (enwikiId, "enwiki") not in imgsDone:
				query = "SELECT name, license, artist, credit FROM" \
					" page_imgs INNER JOIN imgs ON page_imgs.img_name = imgs.name" \
					" WHERE page_imgs.page_id = ?"
				row = enwikiCur.execute(query, (enwikiId,)).fetchone()
				if row == None:
					print("ERROR: No image record for enwiki ID {enwikiId}", file=sys.stderr)
					break
				(name, license, artist, credit) = row
				url = "https://en.wikipedia.org/wiki/File:" + urllib.parse.quote(name)
				dbCur.execute("INSERT INTO images VALUES (?, ?, ?, ?, ?, ?)",
					(enwikiId, "enwiki", url, license, artist, credit))
				imgsDone.add((enwikiId, "enwiki"))
			dbCur.execute("INSERT INTO node_imgs VALUES (?, ?, ?)", (otolId, enwikiId, "enwiki"))
# Close dbs
dbCon.commit()
dbCon.close()
eolCon.close()
enwikiCon.close()
