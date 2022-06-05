#!/usr/bin/python3

import sys, re, os
import sqlite3
import urllib.parse, requests
import time, signal

usageInfo =  f"usage: {sys.argv[0]}\n"
usageInfo += "Downloads images from URLs specified in an sqlite db,\n"
usageInfo += "into a specified directory.'\n"
usageInfo += "\n"
usageInfo += "SIGINT causes the program to finish an ongoing download and exit.\n"
usageInfo += "The program can be re-run to continue downloading, and looks\n"
usageInfo += "in the output directory do decide what to skip.\n"
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

imgDb = "enwikiImgs.db" # About 130k image names
outDir = "imgs"
licenseRegex = re.compile(r"cc0|cc([ -]by)?([ -]sa)?([ -][1234]\.[05])?( \w\w\w?)?", flags=re.IGNORECASE)

# Create output directory if not present
if not os.path.exists(outDir):
	os.mkdir(outDir)
# Get existing image names
print("Gettings already-downloaded images")
fileList = os.listdir(outDir)
pageIdsDone = set()
for filename in fileList:
	(basename, extension) = os.path.splitext(filename)
	pageIdsDone.add(int(basename))
print(f"Found {len(pageIdsDone)} already-downloaded images")
# Set SIGINT handler
interrupted = False
oldHandler = None
def onSigint(sig, frame):
	global interrupted
	interrupted = True
	signal.signal(signal.SIGINT, oldHandler)
oldHandler = signal.signal(signal.SIGINT, onSigint)
# Open db
dbCon = sqlite3.connect(imgDb)
dbCur = dbCon.cursor()
# Start downloads
print("Starting downloads")
iterNum = 0
query = "SELECT page_id, license, artist, credit, restrictions, url FROM" \
	" imgs INNER JOIN page_imgs ON imgs.name = page_imgs.img_name"
for (pageId, license, artist, credit, restrictions, url) in dbCur.execute(query):
	if pageId in pageIdsDone:
		continue
	if interrupted:
		print(f"Exiting loop")
		break
	# Check for problematic attributes
	if license == None or licenseRegex.fullmatch(license) == None:
		continue
	if artist == None or artist == "" or len(artist) > 100 or re.match(r"(\d\. )?File:", artist) != None:
		continue
	if credit == None or len(credit) > 300 or re.match(r"File:", credit) != None:
		continue
	if restrictions != None and restrictions != "":
		continue
	# Download image
	iterNum += 1
	print(f"Iteration {iterNum}: Downloading for page-id {pageId}")
	urlParts = urllib.parse.urlparse(url)
	extension = os.path.splitext(urlParts.path)[1]
	if len(extension) <= 1:
		print(f"WARNING: No filename extension found in URL {url}", file=sys.stderr)
		sys.exit(1)
	outFile = f"{outDir}/{pageId}{extension}"
	headers = {
		"user-agent": "terryt.dev (terry06890@gmail.com)",
		"accept-encoding": "gzip",
	}
	try:
		response = requests.get(url, headers=headers)
		with open(outFile, 'wb') as file:
			file.write(response.content)
		time.sleep(1)
			# https://en.wikipedia.org/wiki/Wikipedia:Database_download says to "throttle self to 1 cache miss per sec"
			# It's unclear how to properly check for cache misses, so just do about <=1 per sec
	except Exception as e:
		print(f"Error while downloading to {outFile}: {e}", file=sys.stderr)
# Close db
dbCon.close()
