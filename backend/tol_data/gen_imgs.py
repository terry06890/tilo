#!/usr/bin/python3

"""
Reads node IDs and image paths from a file, and possibly from a directory,
and generates cropped/resized versions of those images into a directory,
with names of the form 'nodeId1.jpg'. Also adds image metadata to the
database.

SIGINT can be used to stop, and the program can be re-run to continue
processing. It uses already-existing database entries to decide what
to skip.
"""

import os, subprocess
import sqlite3, urllib.parse
import signal

IMG_LIST_FILE = 'img_list.txt'
EOL_IMG_DIR = os.path.join('eol', 'imgs') # Used to decide which IMG_LIST_FILE lines denote chosen EOL images
OUT_DIR = 'img'
EOL_IMG_DB = os.path.join('eol', 'images_list.db')
ENWIKI_IMG_DB = os.path.join('enwiki', 'img_data.db')
PICKED_IMGS_DIR = 'picked_imgs'
PICKED_IMGS_FILE = 'img_data.txt'
DB_FILE = 'data.db'
#
IMG_OUT_SZ = 200

ImgId = tuple[int, str] # Holds an int ID and a source string (eg: 'eol')
class PickedImg:
	""" Represents a picked-image from pickedImgsDir """
	def __init__(self, nodeName: str, id: int, filename: str, url: str, license: str, artist: str, credit: str):
		self.nodeName = nodeName
		self.id = id
		self.filename = filename
		self.url = url
		self.license = license
		self.artist = artist
		self.credit = credit

def genImgs(
		imgListFile: str, eolImgDir: str, outDir: str, eolImgDb: str, enwikiImgDb: str,
		pickedImgsDir: str, pickedImgsFile: str, dbFile):
	""" Reads the image-list file, generates images, and updates db """
	if not os.path.exists(outDir):
		os.mkdir(outDir)
	#
	dbCon = sqlite3.connect(dbFile)
	dbCur = dbCon.cursor()
	print('Checking for image tables')
	nodesDone: set[str] = set()
	imgsDone: set[ImgId] = set()
	if dbCur.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="node_imgs"').fetchone() is None:
		# Add image tables if not present
		dbCur.execute('CREATE TABLE node_imgs (name TEXT PRIMARY KEY, img_id INT, src TEXT)')
		dbCur.execute('CREATE TABLE images (' \
			'id INT, src TEXT, url TEXT, license TEXT, artist TEXT, credit TEXT, PRIMARY KEY (id, src))')
	else:
		# Get existing image-associated nodes
		for (otolId,) in dbCur.execute('SELECT nodes.id FROM node_imgs INNER JOIN nodes ON node_imgs.name = nodes.name'):
			nodesDone.add(otolId)
		# Get existing node-associated images
		for imgId, imgSrc in dbCur.execute('SELECT id, src from images'):
			imgsDone.add((imgId, imgSrc))
		print(f'Found {len(nodesDone)} nodes and {len(imgsDone)} images to skip')
	#
	print('Processing picked-images')
	success = processPickedImgs(pickedImgsDir, pickedImgsFile, nodesDone, imgsDone, outDir, dbCur)
	if success:
		print('Processing images from eol and enwiki')
		processImgs(imgListFile, eolImgDir, eolImgDb, enwikiImgDb, nodesDone, imgsDone, outDir, dbCur)
	# Close db
	dbCon.commit()
	dbCon.close()
def processPickedImgs(
		pickedImgsDir: str, pickedImgsFile: str, nodesDone: set[str], imgsDone: set[ImgId],
		outDir: str, dbCur: sqlite3.Cursor) -> bool:
	""" Converts picked-images and updates db, returning False upon interruption or failure """
	# Read picked-image data
	nodeToPickedImg: dict[str, PickedImg] = {}
	if os.path.exists(os.path.join(pickedImgsDir, pickedImgsFile)):
		with open(os.path.join(pickedImgsDir, pickedImgsFile)) as file:
			for lineNum, line in enumerate(file, 1):
				filename, url, license, artist, credit = line.rstrip().split('|')
				nodeName = os.path.splitext(filename)[0] # Remove extension
				(otolId,) = dbCur.execute('SELECT id FROM nodes WHERE name = ?', (nodeName,)).fetchone()
				nodeToPickedImg[otolId] = PickedImg(nodeName, lineNum, filename, url, license, artist, credit)
	# Set SIGINT handler
	interrupted = False
	def onSigint(sig, frame):
		nonlocal interrupted
		interrupted = True
	signal.signal(signal.SIGINT, onSigint)
	# Convert images
	for otolId, imgData in nodeToPickedImg.items():
		# Check for SIGINT event
		if interrupted:
			print('Exiting')
			return False
		# Skip if already processed
		if otolId in nodesDone:
			continue
		# Convert image
		success = convertImage(os.path.join(pickedImgsDir, imgData.filename), os.path.join(outDir, otolId + '.jpg'))
		if not success:
			return False
		# Add entry to db
		if (imgData.id, 'picked') not in imgsDone:
			dbCur.execute('INSERT INTO images VALUES (?, ?, ?, ?, ?, ?)',
				(imgData.id, 'picked', imgData.url, imgData.license, imgData.artist, imgData.credit))
			imgsDone.add((imgData.id, 'picked'))
		dbCur.execute('INSERT INTO node_imgs VALUES (?, ?, ?)', (imgData.nodeName, imgData.id, 'picked'))
		nodesDone.add(otolId)
	return True
def processImgs(
		imgListFile: str, eolImgDir: str, eolImgDb: str, enwikiImgDb: str,
		nodesDone: set[str], imgsDone: set[ImgId], outDir: str, dbCur: sqlite3.Cursor) -> bool:
	""" Converts EOL and enwiki images, and updates db, returning False upon interrupted or failure """
	eolCon = sqlite3.connect(eolImgDb)
	eolCur = eolCon.cursor()
	enwikiCon = sqlite3.connect(enwikiImgDb)
	enwikiCur = enwikiCon.cursor()
	# Set SIGINT handler
	interrupted = False
	def onSigint(sig, frame):
		nonlocal interrupted
		interrupted = True
	signal.signal(signal.SIGINT, onSigint)
	# Convert images
	flag = False # Set to True upon interruption or failure
	with open(imgListFile) as file:
		for line in file:
			# Check for SIGINT event
			if interrupted:
				print('Exiting')
				flag = True
				break
			# Skip lines without an image path
			if line.find(' ') == -1:
				continue
			# Get filenames
			otolId, _, imgPath = line.rstrip().partition(' ')
			# Skip if already processed
			if otolId in nodesDone:
				continue
			# Convert image
			success = convertImage(imgPath, os.path.join(outDir, otolId + '.jpg'))
			if not success:
				flag = True
				break
			# Add entry to db
			(nodeName,) = dbCur.execute('SELECT name FROM nodes WHERE id = ?', (otolId,)).fetchone()
			fromEol = imgPath.startswith(eolImgDir)
			imgName = os.path.basename(os.path.normpath(imgPath)) # Get last path component
			imgName = os.path.splitext(imgName)[0] # Remove extension
			if fromEol:
				eolIdStr, _, contentIdStr = imgName.partition(' ')
				eolId, contentId = int(eolIdStr), int(contentIdStr)
				if (eolId, 'eol') not in imgsDone:
					query = 'SELECT source_url, license, copyright_owner FROM images WHERE content_id = ?'
					row = eolCur.execute(query, (contentId,)).fetchone()
					if row is None:
						print(f'ERROR: No image record for EOL ID {eolId}, content ID {contentId}')
						flag = True
						break
					url, license, owner = row
					dbCur.execute('INSERT INTO images VALUES (?, ?, ?, ?, ?, ?)',
						(eolId, 'eol', url, license, owner, ''))
					imgsDone.add((eolId, 'eol'))
				dbCur.execute('INSERT INTO node_imgs VALUES (?, ?, ?)', (nodeName, eolId, 'eol'))
			else:
				enwikiId = int(imgName)
				if (enwikiId, 'enwiki') not in imgsDone:
					query = 'SELECT name, license, artist, credit FROM' \
						' page_imgs INNER JOIN imgs ON page_imgs.img_name = imgs.name' \
						' WHERE page_imgs.page_id = ?'
					row = enwikiCur.execute(query, (enwikiId,)).fetchone()
					if row is None:
						print(f'ERROR: No image record for enwiki ID {enwikiId}')
						flag = True
						break
					name, license, artist, credit = row
					url = 'https://en.wikipedia.org/wiki/File:' + urllib.parse.quote(name)
					dbCur.execute('INSERT INTO images VALUES (?, ?, ?, ?, ?, ?)',
						(enwikiId, 'enwiki', url, license, artist, credit))
					imgsDone.add((enwikiId, 'enwiki'))
				dbCur.execute('INSERT INTO node_imgs VALUES (?, ?, ?)', (nodeName, enwikiId, 'enwiki'))
	eolCon.close()
	enwikiCon.close()
	return not flag
def convertImage(imgPath: str, outPath: str):
	print(f'Converting {imgPath} to {outPath}')
	if os.path.exists(outPath):
		print('ERROR: Output image already exists')
		return False
	try:
		completedProcess = subprocess.run(
			['npx', 'smartcrop-cli', '--width', str(IMG_OUT_SZ), '--height', str(IMG_OUT_SZ), imgPath, outPath],
			stdout=subprocess.DEVNULL
		)
	except Exception as e:
		print(f'ERROR: Exception while attempting to run smartcrop: {e}')
		return False
	if completedProcess.returncode != 0:
		print(f'ERROR: smartcrop had exit status {completedProcess.returncode}')
		return False
	return True

if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.parse_args()
	#
	genImgs(IMG_LIST_FILE, EOL_IMG_DIR, OUT_DIR, EOL_IMG_DB, ENWIKI_IMG_DB, PICKED_IMGS_DIR, PICKED_IMGS_FILE, DB_FILE)
