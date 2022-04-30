#!/usr/bin/python3

import sys, os, subprocess
import sqlite3
import signal

usageInfo =  f"usage: {sys.argv[0]}\n"
usageInfo += "Creates web-usable copies of reviewed images.\n"
usageInfo += "Looks in a reviewed-images directory for images named 'eolId1 contentId1.ext1', \n"
usageInfo += "and places copied/resized versions in another directory, with name 'eolId1.jpg'.\n"
usageInfo += "Also adds image metadata to a database, making use of an images-list database.\n"
usageInfo += "\n"
usageInfo += "SIGINT can be used to stop conversion, and the program can be re-run to\n"
usageInfo += "continue processing. It uses existing output files to decide where from.\n"
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

imgDir = "imgsReviewed/"
outDir = "img/"
imagesListDb = "eol/imagesList.db"
dbFile = "data.db"
IMG_OUT_SZ = 200

# Create output directory if not present
if not os.path.exists(outDir):
	os.mkdir(outDir)
# Open images-list db
imagesListDbCon = sqlite3.connect(imagesListDb)
imagesListCur = imagesListDbCon.cursor()
# Create/open data db
dbCon = sqlite3.connect(dbFile)
dbCur = dbCon.cursor()
if dbCur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='images'").fetchone() == None:
	dbCur.execute("CREATE TABLE images (eol_id INT PRIMARY KEY, source_url TEXT, license TEXT, copyright_owner TEXT)")
def closeDb():
	dbCon.commit()
	dbCon.close()
# Get list of input images
print("Reading input image list")
inputImgList = os.listdir(imgDir)
inputImgList.sort(key=lambda s: int(s.split(" ")[0]))
if len(inputImgList) == 0:
	print("No input images found")
	closeDb()
	sys.exit(0)
# Get next image to convert
inputImgIdx = 0
print("Checking for existing output files")
outputImgList = os.listdir(outDir)
if len(outputImgList) > 0:
	latestOutputId = 0
	for filename in outputImgList:
		latestOutputId = max(latestOutputId, int(filename.split(".")[0]))
	while int(inputImgList[inputImgIdx].split(" ")[0]) <= latestOutputId:
		inputImgIdx += 1
		if inputImgIdx == len(inputImgList):
			print("No unprocessed input images found")
			closeDb()
			sys.exit(0)
# Detect SIGINT signals
interrupted = False
def onSigint(sig, frame):
	global interrupted
	interrupted = True
signal.signal(signal.SIGINT, onSigint)
# Convert input images
	# There are two interrupt checks because the subprocess exits on a SIGINT (not prevented by the handler above).
	# The second check prevents adding a db entry for a non-created file.
	# The first check prevents starting a new subprocess after a sigint occurs while adding to db
print("Converting images")
for i in range(inputImgIdx, len(inputImgList)):
	if interrupted:
		print("Exiting")
		break
	imgName = inputImgList[i]
	[eolIdStr, otherStr] = imgName.split(" ")
	contentId = int(otherStr.split(".")[0])
	print("Converting {}".format(imgName))
	subprocess.run(
		['npx', 'smartcrop-cli', 
			'--width', str(IMG_OUT_SZ),
			'--height', str(IMG_OUT_SZ),
			imgDir + imgName,
			outDir + eolIdStr + ".jpg"],
		stdout=subprocess.DEVNULL)
	if interrupted:
		print("Exiting")
		break
	# Add entry to db
	imagesListQuery = "SELECT content_id, source_url, license, copyright_owner FROM images WHERE content_id = ?"
	row = imagesListCur.execute(imagesListQuery, (contentId,)).fetchone()
	dbCur.execute("INSERT INTO images VALUES (?, ?, ?, ?)", (int(eolIdStr), row[1], row[2], row[3]))
closeDb()
