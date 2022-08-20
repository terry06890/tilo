#!/usr/bin/python3

import sys, os, subprocess
import sqlite3, urllib.parse
import signal

import argparse
parser = argparse.ArgumentParser(description="""
Reads node IDs and image paths from a file, and possibly from a directory,
and generates cropped/resized versions of those images into a directory,
with names of the form 'nodeId1.jpg'. Also adds image metadata to the
database.

SIGINT can be used to stop, and the program can be re-run to continue
processing. It uses already-existing database entries to decide what
to skip.
""", formatter_class=argparse.RawDescriptionHelpFormatter)
parser.parse_args()

imgListFile = "imgList.txt"
outDir = "img/"
eolImgDb = "eol/imagesList.db"
enwikiImgDb = "enwiki/imgData.db"
pickedImgsDir = "pickedImgs/"
pickedImgsFilename = "imgData.txt"
dbFile = "data.db"
IMG_OUT_SZ = 200
genImgFiles = True # Usable for debugging

if not os.path.exists(outDir):
	os.mkdir(outDir)

print("Opening databases")
dbCon = sqlite3.connect(dbFile)
dbCur = dbCon.cursor()
eolCon = sqlite3.connect(eolImgDb)
eolCur = eolCon.cursor()
enwikiCon = sqlite3.connect(enwikiImgDb)
enwikiCur = enwikiCon.cursor()
print("Checking for picked-images")
nodeToPickedImg = {}
if os.path.exists(pickedImgsDir + pickedImgsFilename):
	lineNum = 0
	with open(pickedImgsDir + pickedImgsFilename) as file:
		for line in file:
			lineNum += 1
			(filename, url, license, artist, credit) = line.rstrip().split("|")
			nodeName = os.path.splitext(filename)[0] # Remove extension
			(otolId,) = dbCur.execute("SELECT id FROM nodes WHERE name = ?", (nodeName,)).fetchone()
			nodeToPickedImg[otolId] = {
				"nodeName": nodeName, "id": lineNum,
				"filename": filename, "url": url, "license": license, "artist": artist, "credit": credit,
			}

print("Checking for image tables")
nodesDone = set()
imgsDone = set()
if dbCur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='node_imgs'").fetchone() == None:
	# Add image tables if not present
	dbCur.execute("CREATE TABLE node_imgs (name TEXT PRIMARY KEY, img_id INT, src TEXT)")
	dbCur.execute("CREATE TABLE images" \
		" (id INT, src TEXT, url TEXT, license TEXT, artist TEXT, credit TEXT, PRIMARY KEY (id, src))")
else:
	# Get existing image-associated nodes
	for (otolId,) in dbCur.execute("SELECT nodes.id FROM node_imgs INNER JOIN nodes ON node_imgs.name = nodes.name"):
		nodesDone.add(otolId)
	# Get existing node-associated images
	for (imgId, imgSrc) in dbCur.execute("SELECT id, src from images"):
		imgsDone.add((imgId, imgSrc))
	print(f"Found {len(nodesDone)} nodes and {len(imgsDone)} images to skip")

# Set SIGINT handler
interrupted = False
def onSigint(sig, frame):
	global interrupted
	interrupted = True
signal.signal(signal.SIGINT, onSigint)

print("Iterating through input images")
def quit():
	print("Closing databases")
	dbCon.commit()
	dbCon.close()
	eolCon.close()
	enwikiCon.close()
	sys.exit(0)
def convertImage(imgPath, outPath):
	print(f"Converting {imgPath} to {outPath}")
	if os.path.exists(outPath):
		print(f"ERROR: Output image already exists")
		return False
	try:
		completedProcess = subprocess.run(
			['npx', 'smartcrop-cli', '--width', str(IMG_OUT_SZ), '--height', str(IMG_OUT_SZ), imgPath, outPath],
			stdout=subprocess.DEVNULL
		)
	except Exception as e:
		print(f"ERROR: Exception while attempting to run smartcrop: {e}")
		return False
	if completedProcess.returncode != 0:
		print(f"ERROR: smartcrop had exit status {completedProcess.returncode}")
		return False
	return True
print("Processing picked-images")
for (otolId, imgData) in nodeToPickedImg.items():
	# Check for SIGINT event
	if interrupted:
		print("Exiting")
		quit()
	# Skip if already processed
	if otolId in nodesDone:
		continue
	# Convert image
	if genImgFiles:
		success = convertImage(pickedImgsDir + imgData["filename"], outDir + otolId + ".jpg")
		if not success:
			quit()
	else:
		print(f"Processing {imgData['nodeName']}: {otolId}.jpg")
	# Add entry to db
	if (imgData["id"], "picked") not in imgsDone:
		dbCur.execute("INSERT INTO images VALUES (?, ?, ?, ?, ?, ?)",
			(imgData["id"], "picked", imgData["url"], imgData["license"], imgData["artist"], imgData["credit"]))
		imgsDone.add((imgData["id"], "picked"))
	dbCur.execute("INSERT INTO node_imgs VALUES (?, ?, ?)", (imgData["nodeName"], imgData["id"], "picked"))
	nodesDone.add(otolId)
print("Processing images from eol and enwiki")
iterNum = 0
with open(imgListFile) as file:
	for line in file:
		iterNum += 1
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
		# Convert image
		if genImgFiles:
			success = convertImage(imgPath, outDir + otolId + ".jpg")
			if not success:
				break
		else:
			if iterNum % 1e4 == 0:
				print(f"At iteration {iterNum}")
		# Add entry to db
		(nodeName,) = dbCur.execute("SELECT name FROM nodes WHERE id = ?", (otolId,)).fetchone()
		fromEol = imgPath.startswith("eol/")
		imgName = os.path.basename(os.path.normpath(imgPath)) # Get last path component
		imgName = os.path.splitext(imgName)[0] # Remove extension
		if fromEol:
			eolId, _, contentId = imgName.partition(" ")
			eolId, contentId = (int(eolId), int(contentId))
			if (eolId, "eol") not in imgsDone:
				query = "SELECT source_url, license, copyright_owner FROM images WHERE content_id = ?"
				row = eolCur.execute(query, (contentId,)).fetchone()
				if row == None:
					print(f"ERROR: No image record for EOL ID {eolId}, content ID {contentId}")
					break
				(url, license, owner) = row
				dbCur.execute("INSERT INTO images VALUES (?, ?, ?, ?, ?, ?)",
					(eolId, "eol", url, license, owner, ""))
				imgsDone.add((eolId, "eol"))
			dbCur.execute("INSERT INTO node_imgs VALUES (?, ?, ?)", (nodeName, eolId, "eol"))
		else:
			enwikiId = int(imgName)
			if (enwikiId, "enwiki") not in imgsDone:
				query = "SELECT name, license, artist, credit FROM" \
					" page_imgs INNER JOIN imgs ON page_imgs.img_name = imgs.name" \
					" WHERE page_imgs.page_id = ?"
				row = enwikiCur.execute(query, (enwikiId,)).fetchone()
				if row == None:
					print(f"ERROR: No image record for enwiki ID {enwikiId}")
					break
				(name, license, artist, credit) = row
				url = "https://en.wikipedia.org/wiki/File:" + urllib.parse.quote(name)
				dbCur.execute("INSERT INTO images VALUES (?, ?, ?, ?, ?, ?)",
					(enwikiId, "enwiki", url, license, artist, credit))
				imgsDone.add((enwikiId, "enwiki"))
			dbCur.execute("INSERT INTO node_imgs VALUES (?, ?, ?)", (nodeName, enwikiId, "enwiki"))
# Close dbs
quit()
