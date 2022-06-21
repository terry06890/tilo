#!/usr/bin/python3

import sys, re
import bz2, html, urllib.parse
import sqlite3

usageInfo =  f"usage: {sys.argv[0]}\n"
usageInfo += "For a set of page-ids, looks up their content in an enwiki dump,\n"
usageInfo += "trying to get infobox image filenames, adding info to an sqlite db.\n"
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

def getInputPageIds():
	pageIds = set()
	dbCon = sqlite3.connect("../data.db")
	dbCur = dbCon.cursor()
	for (pageId,) in dbCur.execute("SELECT id from wiki_ids"):
		pageIds.add(pageId)
	dbCon.close()
	return pageIds
dumpFile = "enwiki-20220501-pages-articles-multistream.xml.bz2"
indexDb = "dumpIndex.db"
imgDb = "imgData.db" # Output db
idLineRegex = re.compile(r"<id>(.*)</id>")
imageLineRegex = re.compile(r".*\| *image *= *([^|]*)")
bracketImageRegex = re.compile(r"\[\[(File:[^|]*).*]]")
imageNameRegex = re.compile(r".*\.(jpg|jpeg|png|gif|tiff|tif)", flags=re.IGNORECASE)
cssImgCropRegex = re.compile(r"{{css image crop\|image *= *(.*)", flags=re.IGNORECASE)

# Open dbs
indexDbCon = sqlite3.connect(indexDb)
indexDbCur = indexDbCon.cursor()
imgDbCon = sqlite3.connect(imgDb)
imgDbCur = imgDbCon.cursor()
# Create image-db table
pidsDone = set()
if imgDbCur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='page_imgs'").fetchone() == None:
	imgDbCur.execute("CREATE TABLE page_imgs (page_id INT PRIMARY KEY, img_name TEXT)") # img_name may be NULL
	imgDbCur.execute("CREATE INDEX page_imgs_idx ON page_imgs(img_name)")
else:
	for (pid,) in imgDbCur.execute("SELECT page_id FROM page_imgs"):
		pidsDone.add(pid)
	print(f"Will skip {len(pidsDone)} already-processed page-ids")
# Get input pageIds
print("Getting input page-ids", file=sys.stderr)
pageIds = getInputPageIds()
for pid in pidsDone:
	pageIds.remove(pid)
print(f"Found {len(pageIds)} page-ids to process")
# Get page-id dump-file offsets
print("Getting dump-file offsets", file=sys.stderr)
offsetToPageids = {}
offsetToEnd = {}
iterNum = 0
for pageId in pageIds:
	iterNum += 1
	if iterNum % 1e4 == 0:
		print(f"At iteration {iterNum}", file=sys.stderr)
	#
	query = "SELECT offset, next_offset FROM offsets WHERE id = ?"
	row = indexDbCur.execute(query, (pageId,)).fetchone()
	if row == None:
		print(f"WARNING: Page id {pageId} not found", file=sys.stderr)
		continue
	(chunkOffset, endOffset) = row
	offsetToEnd[chunkOffset] = endOffset
	if chunkOffset not in offsetToPageids:
		offsetToPageids[chunkOffset] = []
	offsetToPageids[chunkOffset].append(pageId)
print(f"Found {len(offsetToEnd)} chunks to check", file=sys.stderr)
# Look through dump file, jumping to chunks containing relevant pages
print("Reading through dump file", file=sys.stderr)
def getImageName(content):
	""" Given an array of text-content lines, returns an image-filename, or None """
	for line in content:
		match = imageLineRegex.match(line)
		if match != None:
			imageName = match.group(1).strip()
			if imageName == "":
				return None
			imageName = html.unescape(imageName)
			# Account for {{...
			if imageName.startswith("{"):
				match = cssImgCropRegex.match(imageName)
				if match == None:
					return None
				imageName = match.group(1)
			# Account for [[File:...|...]]
			if imageName.startswith("["):
				match = bracketImageRegex.match(imageName)
				if match == None:
					return None
				imageName = match.group(1)
			# Account for <!--
			if imageName.find("<!--") != -1:
				return None
			# Remove an initial 'File:'
			if imageName.startswith("File:"):
				imageName = imageName[5:]
			# Remove an initial 'Image:'
			if imageName.startswith("Image:"):
				imageName = imageName[6:]
			# Check for extension
			match = imageNameRegex.match(imageName)
			if match != None:
				imageName = match.group(0)
				imageName = urllib.parse.unquote(imageName)
				imageName = html.unescape(imageName) # Intentionally unescaping again (handles some odd cases)
				imageName = imageName.replace("_", " ")
				return imageName
			# Skip lines like: | image = &lt;imagemap&gt;
			return None
	# Doesn't try and find images in outside-infobox [[File:...]] and <imagemap> sections
	return None
with open(dumpFile, mode='rb') as file:
	iterNum = 0
	for (pageOffset, endOffset) in offsetToEnd.items():
		iterNum += 1
		if iterNum % 100 == 0:
			print(f"At iteration {iterNum}", file=sys.stderr)
		#
		pageIds = offsetToPageids[pageOffset]
		# Jump to chunk
		file.seek(pageOffset)
		compressedData = file.read(None if endOffset == -1 else endOffset - pageOffset)
		data = bz2.BZ2Decompressor().decompress(compressedData).decode()
		# Look in chunk for pages
		lines = data.splitlines()
		lineIdx = 0
		while lineIdx < len(lines):
			# Look for <page>
			if lines[lineIdx].lstrip() != "<page>":
				lineIdx += 1
				continue
			# Check page id
			lineIdx += 3
			idLine = lines[lineIdx].lstrip()
			match = idLineRegex.fullmatch(idLine)
			if match == None or int(match.group(1)) not in pageIds:
				lineIdx += 1
				continue
			pageId = int(match.group(1))
			lineIdx += 1
			# Look for <text> in <page>
			foundText = False
			while lineIdx < len(lines):
				if not lines[lineIdx].lstrip().startswith("<text "):
					lineIdx += 1
					continue
				foundText = True
				# Get text content
				content = []
				line = lines[lineIdx]
				content.append(line[line.find(">") + 1:])
				lineIdx += 1
				foundTextEnd = False
				while lineIdx < len(lines):
					line = lines[lineIdx]
					if not line.endswith("</text>"):
						content.append(line)
						lineIdx += 1
						continue
					foundTextEnd = True
					content.append(line[:line.rfind("</text>")])
					# Look for image-filename
					imageName = getImageName(content)
					imgDbCur.execute("INSERT into page_imgs VALUES (?, ?)", (pageId, imageName))
					break
				if not foundTextEnd:
					print(f"Did not find </text> for page id {pageId}", file=sys.stderr)
				break
			if not foundText:
				print(f"Did not find <text> for page id {pageId}", file=sys.stderr)
# Close dbs
indexDbCon.close()
imgDbCon.commit()
imgDbCon.close()
