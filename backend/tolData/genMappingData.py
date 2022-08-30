#!/usr/bin/python3

import sys, re, os
from collections import defaultdict
import gzip, bz2, csv, sqlite3

import argparse
parser = argparse.ArgumentParser(description='''
Maps otol IDs to EOL and enwiki titles, using IDs from various
other sources (like NCBI).

Reads otol taxonomy data to get source IDs for otol IDs,
then looks up those IDs in an EOL provider_ids file,
and in a wikidata dump, and stores results in the database.

Based on code from https://github.com/OneZoom/OZtree, located in
OZprivate/ServerScripts/TaxonMappingAndPopularity/ (22 Aug 2022).
''', formatter_class=argparse.RawDescriptionHelpFormatter)
args = parser.parse_args()

taxonomyFile = 'otol/taxonomy.tsv'
eolIdsFile = 'eol/provider_ids.csv.gz'
wikidataDb = 'wikidata/taxonSrcs.db'
enwikiDumpIndexDb = 'enwiki/dumpIndex.db'
pickedMappings = {
	'eol': ['pickedEolIds.txt'],
	'enwiki': ['pickedWikiIds.txt', 'pickedWikiIdsRough.txt']
}
dbFile = 'data.db'

print('Reading taxonomy file')
# The file has a header line, then lines that hold these fields (each is followed by a tab-pipe-tab sequence):
	# uid (otol-id, eg: 93302), parent_uid, name, rank, 
	# sourceinfo (comma-separated source specifiers, eg: ncbi:2952,gbif:3207147), uniqueName, flags
OTOL_SRCS = ['ncbi', 'if', 'worms', 'irmng', 'gbif'] # Earlier sources will get higher priority
nodeToSrcIds = defaultdict(dict) # Maps otol ID to {src1: id1, src2: id2, ...}
usedSrcIds = set() # {(src1, id1), ...} (used to avoid storing IDs that won't be used)
with open(taxonomyFile) as file: # Had about 4.5e6 lines
	lineNum = 0
	for line in file:
		lineNum += 1
		if lineNum % 1e5 == 0:
			print(f'At line {lineNum}')
		# Skip header line
		if lineNum == 1:
			continue
		# Parse line
		fields = line.split('\t|\t')
		try:
			otolId = int(fields[0])
		except ValueError:
			print(f'Skipping non-integral ID {fields[0]} on line {lineNum}')
			continue
		srcInfo = fields[4]
		# Add source IDs
		for srcPair in srcInfo.split(','):
			src, srcId = srcPair.split(':', 1)
			if srcId.isdecimal() and src in OTOL_SRCS and src not in nodeToSrcIds[otolId]:
				srcId = int(srcId)
				nodeToSrcIds[otolId][src] = srcId
				usedSrcIds.add((src, srcId))
print(f'- Result has {sum([len(v) for v in nodeToSrcIds.values()]):,} entries') # Was about 6.7e6

print('Reading EOL provider_ids file')
# The CSV file has a header line, then lines that hold these fields:
	# node_id, resource_pk (ID from external source), resource_id (int denoting external-source),
	# page_id (eol ID), preferred_canonical_for_page
EOL_SRCS = {676: 'ncbi', 459: 'worms', 767: 'gbif'} # Maps ints to external-source names
srcToEolId = {src: {} for src in EOL_SRCS.values()} # Maps src1 to {id1: eolId1, ...}
with gzip.open(eolIdsFile, mode='rt') as file: # Had about 13e6 lines
	for lineNum, row in enumerate(csv.reader(file), 1):
		if lineNum % 1e6 == 0:
			print(f'At line {lineNum}')
		# Skip header line
		if lineNum == 1:
			continue
		# Parse line
		eolId = int(row[3])
		srcVal = int(row[2])
		srcId = row[1]
		if srcId.isdecimal() and srcVal in EOL_SRCS:
			srcId = int(srcId)
			src = EOL_SRCS[srcVal]
			if (src, srcId) not in usedSrcIds:
				continue
			if srcId in srcToEolId[src]:
				print(f'Found {src} ID {srcId} with multiple EOL IDs {srcToEolId[src][srcId]} and {eolId}')
				continue
			srcToEolId[src][srcId] = eolId
print(f'- Result has {sum([len(v) for v in srcToEolId.values()]):,} entries')
	# Was about 3.5e6 (4.2e6 without usedSrcIds)

print('Resolving candidate EOL IDs')
# For each otol ID, find eol IDs with matching sources, and choose the 'best' one
nodeToEolId = {} # Maps otol ID to eol ID
for otolId, srcInfo in nodeToSrcIds.items():
	eolIdToCount = defaultdict(int)
	for src, srcId in srcInfo.items():
		if src in srcToEolId and srcId in srcToEolId[src]:
			eolId = srcToEolId[src][srcId]
			eolIdToCount[eolId] += 1
	if len(eolIdToCount) == 1:
		nodeToEolId[otolId] = list(eolIdToCount)[0]
	elif len(eolIdToCount) > 1:
		# For multiple candidates, prefer those with most sources, and break ties by picking the lowest
		maxCount = max(eolIdToCount.values())
		eolIds = [eolId for eolId, count in eolIdToCount.items() if count == maxCount]
		nodeToEolId[otolId] = min(eolIds)
print(f'- Result has {len(nodeToEolId):,} entries') # Was about 2.7e6

print('Reading from Wikidata db')
srcToWikiTitle = defaultdict(dict) # Maps 'eol'/etc to {srcId1: title1, ...}
wikiTitles = set()
titleToIucnStatus = {}
dbCon = sqlite3.connect(wikidataDb)
dbCur = dbCon.cursor()
for src, srcId, title in dbCur.execute('SELECT src, id, title from src_id_to_title'):
	if (src, srcId) not in usedSrcIds and src != 'eol': # Keep EOL IDs for later use 
		continue
	srcToWikiTitle[src][srcId] = title
	wikiTitles.add(title)
for title, status in dbCur.execute('SELECT title, status from title_iucn'):
	if title in wikiTitles:
		titleToIucnStatus[title] = status
print(f'- Source-to-title map has {sum([len(v) for v in srcToWikiTitle.values()]):,} entries')
	# Was about 1.1e6 (1.2e6 without usedSrcIds)
print(f'- IUCN map has {len(titleToIucnStatus):,} entries') # Was about 7e4 (7.2e4 without usedSrcIds)
dbCon.close()

print('Resolving candidate Wikidata items')
# For each otol ID, find wikidata titles with matching sources, and choose the 'best' one
nodeToWikiTitle = {}
for otolId, srcInfo in nodeToSrcIds.items():
	titleToSrcs = defaultdict(list) # Maps candidate titles to {src1: srcId1, ...}
	for src, srcId in srcInfo.items():
		if src in srcToWikiTitle and srcId in srcToWikiTitle[src]:
			title = srcToWikiTitle[src][srcId]
			titleToSrcs[title].append(src)
	# Choose title to use
	if len(titleToSrcs) == 1:
		nodeToWikiTitle[otolId] = list(titleToSrcs)[0]
	elif len(titleToSrcs) > 1: # Test example: otol ID 621052
		# Get titles with most sources
		maxSrcCnt = max([len(srcs) for srcs in titleToSrcs.values()])
		titleToSrcs = {t: s for t, s in titleToSrcs.items() if len(s) == maxSrcCnt}
		if len(titleToSrcs) == 1:
			nodeToWikiTitle[otolId] = list(titleToSrcs)[0]
		else: # Test example: otol ID 4235272
			# Get a title with a source with highest priority
			srcToTitle = {s: t for t in titleToSrcs for s in titleToSrcs[t]}
			for src in OTOL_SRCS:
				if src in srcToTitle:
					nodeToWikiTitle[otolId] = srcToTitle[src]
					break
print(f'- Result has {len(nodeToWikiTitle):,} entries') # Was about 4e5

print('Adding extra EOL mappings from Wikidata')
eolIdToNode = {eolId: node for node, eolId in nodeToEolId.items()}
wikiTitleToNode = {title: node for node, title in nodeToWikiTitle.items()}
addedEntries = {}
for eolId, title in srcToWikiTitle['eol'].items():
	if title in wikiTitleToNode:
		otolId = wikiTitleToNode[title]
		if otolId not in nodeToEolId: # Only add if the otol ID has no EOL ID
			nodeToEolId[otolId] = eolId
			addedEntries[otolId] = eolId
print(f'- Added {len(addedEntries):,} entries') # Was about 3e3

print('Reading picked mappings')
for src in pickedMappings:
	for filename in pickedMappings[src]:
		if not os.path.exists(filename):
			continue
		with open(filename) as file:
			for line in file:
				otolId, mappedVal = line.rstrip().split('|')
				otolId = int(otolId)
				if src == 'eol':
					if mappedVal:
						nodeToEolId[otolId] = int(mappedVal)
					else:
						if otolId in nodeToEolId:
							del nodeToEolId[otolId]
				else: # src == 'enwiki'
					if mappedVal:
						nodeToWikiTitle[otolId] = mappedVal
					else:
						if otolId in nodeToWikiTitle:
							del nodeToWikiTitle[otolId]

print(f'Getting enwiki page IDs')
titleToPageId = {}
numNotFound = 0
dbCon = sqlite3.connect(enwikiDumpIndexDb)
dbCur = dbCon.cursor()
for title in nodeToWikiTitle.values():
	row = dbCur.execute('SELECT id FROM offsets WHERE title = ?', (title,)).fetchone()
	if row != None:
		titleToPageId[title] = row[0]
	else:
		numNotFound += 1
dbCon.close()
print(f'Unable to find IDs for {numNotFound} titles') # Was 2913

print('Writing to db')
dbCon = sqlite3.connect(dbFile)
dbCur = dbCon.cursor()
# Get otol id-to-name map
otolIdToName = {}
for nodeName, nodeId in dbCur.execute('SELECT name, id from nodes'):
	if nodeId.startswith('ott'):
		otolIdToName[int(nodeId[3:])] = nodeName
# Add eol mappings
dbCur.execute('CREATE TABLE eol_ids (name TEXT PRIMARY KEY, id INT)')
dbCur.execute('CREATE INDEX eol_id_idx ON eol_ids(id)')
for otolId, eolId in nodeToEolId.items():
	if otolId in otolIdToName:
		dbCur.execute('INSERT INTO eol_ids VALUES (?, ?)', (otolIdToName[otolId], eolId))
# Add enwiki mappings
dbCur.execute('CREATE TABLE wiki_ids (name TEXT PRIMARY KEY, id INT)')
dbCur.execute('CREATE INDEX wiki_id_idx ON wiki_ids(id)')
dbCur.execute('CREATE TABLE node_iucn (name TEXT PRIMARY KEY, iucn TEXT)')
for otolId, title in nodeToWikiTitle.items():
	if otolId in otolIdToName and title in titleToPageId:
		dbCur.execute('INSERT INTO wiki_ids VALUES (?, ?)', (otolIdToName[otolId], titleToPageId[title]))
		if title in titleToIucnStatus:
			dbCur.execute('INSERT INTO node_iucn VALUES (?, ?)', (otolIdToName[otolId], titleToIucnStatus[title]))
dbCon.commit()
dbCon.close()
