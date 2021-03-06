#!/usr/bin/python3

import sys, re
import sqlite3, urllib.parse, html
import requests
import time, signal

usageInfo = f"""
Usage: {sys.argv[0]}

Reads image names from a database, and uses enwiki's online API to obtain
licensing information for them, adding the info to the database.

SIGINT causes the program to finish an ongoing download and exit.
The program can be re-run to continue downloading, and looks
at already-processed names to decide what to skip.
"""
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

imgDb = "imgData.db"
apiUrl = "https://en.wikipedia.org/w/api.php"
userAgent = "terryt.dev (terry06890@gmail.com)"
batchSz = 50 # Max 50
tagRegex = re.compile(r"<[^<]+>")
whitespaceRegex = re.compile(r"\s+")

print("Opening database")
dbCon = sqlite3.connect(imgDb)
dbCur = dbCon.cursor()
dbCur2 = dbCon.cursor()
print("Checking for table")
if dbCur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='imgs'").fetchone() == None:
	dbCur.execute("CREATE TABLE imgs(" \
		"name TEXT PRIMARY KEY, license TEXT, artist TEXT, credit TEXT, restrictions TEXT, url TEXT)")

print("Reading image names")
imgNames = set()
for (imgName,) in dbCur.execute("SELECT DISTINCT img_name FROM page_imgs WHERE img_name NOT NULL"):
	imgNames.add(imgName)
print(f"Found {len(imgNames)}")

print("Checking for already-processed images")
oldSz = len(imgNames)
for (imgName,) in dbCur.execute("SELECT name FROM imgs"):
	imgNames.discard(imgName)
print(f"Found {oldSz - len(imgNames)}")

# Set SIGINT handler
interrupted = False
oldHandler = None
def onSigint(sig, frame):
	global interrupted
	interrupted = True
	signal.signal(signal.SIGINT, oldHandler)
oldHandler = signal.signal(signal.SIGINT, onSigint)

print("Iterating through image names")
imgNames = list(imgNames)
iterNum = 0
for i in range(0, len(imgNames), batchSz):
	iterNum += 1
	if iterNum % 1 == 0:
		print(f"At iteration {iterNum} (after {(iterNum - 1) * batchSz} images)")
	if interrupted:
		print(f"Exiting loop at iteration {iterNum}")
		break
	# Get batch
	imgBatch = imgNames[i:i+batchSz]
	imgBatch = ["File:" + x for x in imgBatch]
	# Make request
	headers = {
		"user-agent": userAgent,
		"accept-encoding": "gzip",
	}
	params = {
		"action": "query",
		"format": "json",
		"prop": "imageinfo",
		"iiprop": "extmetadata|url",
		"maxlag": "5",
		"titles": "|".join(imgBatch),
		"iiextmetadatafilter": "Artist|Credit|LicenseShortName|Restrictions",
	}
	responseObj = None
	try:
		response = requests.get(apiUrl, params=params, headers=headers)
		responseObj = response.json()
	except Exception as e:
		print(f"ERROR: Exception while downloading info: {e}")
		print(f"\tImage batch: " + "|".join(imgBatch))
		continue
	# Parse response-object
	if "query" not in responseObj or "pages" not in responseObj["query"]:
		print("WARNING: Response object for doesn't have page data")
		print("\tImage batch: " + "|".join(imgBatch))
		if "error" in responseObj:
			errorCode = responseObj["error"]["code"]
			print(f"\tError code: {errorCode}")
			if errorCode == "maxlag":
				time.sleep(5)
		continue
	pages = responseObj["query"]["pages"]
	normalisedToInput = {}
	if "normalized" in responseObj["query"]:
		for entry in responseObj["query"]["normalized"]:
			normalisedToInput[entry["to"]] = entry["from"]
	for (_, page) in pages.items():
		# Some fields // More info at https://www.mediawiki.org/wiki/Extension:CommonsMetadata#Returned_data
			# LicenseShortName: short human-readable license name, apparently more reliable than 'License',
			# Artist: author name (might contain complex html, multiple authors, etc)
			# Credit: 'source'
				# For image-map-like images, can be quite large/complex html, creditng each sub-image
				# May be <a href="text1">text2</a>, where the text2 might be non-indicative
			# Restrictions: specifies non-copyright legal restrictions
		title = page["title"]
		if title in normalisedToInput:
			title = normalisedToInput[title]
		title = title[5:] # Remove 'File:'
		if title not in imgNames:
			print(f"WARNING: Got title \"{title}\" not in image-name list")
			continue
		if "imageinfo" not in page:
			print(f"WARNING: No imageinfo section for page \"{title}\"")
			continue
		metadata = page["imageinfo"][0]["extmetadata"]
		url = page["imageinfo"][0]["url"]
		license = metadata['LicenseShortName']['value'] if 'LicenseShortName' in metadata else None
		artist = metadata['Artist']['value'] if 'Artist' in metadata else None
		credit = metadata['Credit']['value'] if 'Credit' in metadata else None
		restrictions = metadata['Restrictions']['value'] if 'Restrictions' in metadata else None
		# Remove markup
		if artist != None:
			artist = tagRegex.sub(" ", artist)
			artist = whitespaceRegex.sub(" ", artist)
			artist = html.unescape(artist)
			artist = urllib.parse.unquote(artist)
		if credit != None:
			credit = tagRegex.sub(" ", credit)
			credit = whitespaceRegex.sub(" ", credit)
			credit = html.unescape(credit)
			credit = urllib.parse.unquote(credit)
		# Add to db
		dbCur2.execute("INSERT INTO imgs VALUES (?, ?, ?, ?, ?, ?)",
			(title, license, artist, credit, restrictions, url))

print("Closing database")
dbCon.commit()
dbCon.close()
