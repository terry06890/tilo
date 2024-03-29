#!/usr/bin/python3

"""
Maps otol IDs to EOL and enwiki titles, using IDs from various
other sources (like NCBI).

Reads otol taxonomy data to get source IDs for otol IDs,
then looks up those IDs in an EOL provider_ids file,
and in a wikidata dump, and stores results in the database.

Based on code from https://github.com/OneZoom/OZtree, located in
OZprivate/ServerScripts/TaxonMappingAndPopularity/ (22 Aug 2022).
"""

import argparse
import os
from collections import defaultdict
import gzip
import csv
import sqlite3

TAXONOMY_FILE = os.path.join('otol', 'taxonomy.tsv')
EOL_IDS_FILE = os.path.join('eol', 'provider_ids.csv.gz')
WIKIDATA_DB = os.path.join('wikidata', 'taxon_srcs.db')
ENWIKI_DUMP_INDEX_DB = os.path.join('enwiki', 'dump_index.db')
PICKED_MAPPINGS = {
	'eol': ['picked_eol_ids.txt'],
	'enwiki': ['picked_wiki_ids.txt', 'picked_wiki_ids_rough.txt']
}
DB_FILE = 'data.db'

OTOL_SRCS = ['ncbi', 'if', 'worms', 'irmng', 'gbif'] # Earlier sources will get higher priority
EOL_SRCS = {676: 'ncbi', 459: 'worms', 767: 'gbif'} # Maps external-source int-identifiers to names

def genData(
		taxonomyFile: str,
		eolIdsFile: str,
		wikidataDb: str,
		pickedMappings: dict[str, list[str]],
		enwikiDumpIndexDb: str,
		dbFile: str) -> None:
	""" Reads the files and enwiki db and creates the db """
	nodeToSrcIds: dict[int, dict[str, int]] = {} # Maps otol ID to {src1: id1, src2: id2, ...}
	usedSrcIds: set[tuple[str, int]] = set() # {(src1, id1), ...} (used to avoid storing IDs that won't be used)
	nodeToEolId: dict[int, int] = {} # Maps otol ID to eol ID
	nodeToWikiTitle: dict[int, str] = {} # Maps otol ID to wikipedia title
	titleToIucnStatus: dict[str, str] = {} # Maps wikipedia title to IUCN string
	titleToPageId: dict[str, int] = {} # Maps wikipedia title to page ID

	# Get mappings from data input
	readTaxonomyFile(taxonomyFile, nodeToSrcIds, usedSrcIds)
	readEolIdsFile(eolIdsFile, nodeToSrcIds, usedSrcIds, nodeToEolId)
	readWikidataDb(wikidataDb, nodeToSrcIds, usedSrcIds, nodeToWikiTitle, titleToIucnStatus, nodeToEolId)
	readPickedMappings(pickedMappings, nodeToEolId, nodeToWikiTitle)
	getEnwikiPageIds(enwikiDumpIndexDb, nodeToWikiTitle, titleToPageId)

	print('Writing to db')
	dbCon = sqlite3.connect(dbFile)
	dbCur = dbCon.cursor()

	# Get otol id-to-name map
	otolIdToName: dict[int, str] = {}
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

def readTaxonomyFile(
		taxonomyFile: str,
		nodeToSrcIds: dict[int, dict[str, int]],
		usedSrcIds: set[tuple[str, int]]) -> None:
	""" Reads taxonomy file, and maps OTOL node IDs to external-source IDs """
	# The file has a header line, then lines that hold these fields (each is followed by a tab-pipe-tab sequence):
		# uid (otol-id, eg: 93302), parent_uid, name, rank, 
		# sourceinfo (comma-separated source specifiers, eg: ncbi:2952,gbif:3207147), uniqueName, flags
	print('Reading taxonomy file')
	with open(taxonomyFile) as file: # Had about 4.5e6 lines
		for lineNum, line in enumerate(file, 1):
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
			srcsField = fields[4]

			# Add source IDs
			for srcPair in srcsField.split(','):
				src, srcIdStr = srcPair.split(':', 1)
				if srcIdStr.isdecimal() and src in OTOL_SRCS:
					if otolId not in nodeToSrcIds:
						nodeToSrcIds[otolId] = {}
					elif src in nodeToSrcIds[otolId]:
						continue
					srcId = int(srcIdStr)
					nodeToSrcIds[otolId][src] = srcId
					usedSrcIds.add((src, srcId))
	print(f'- Result has {sum([len(v) for v in nodeToSrcIds.values()]):,} entries') # Was about 6.7e6

def readEolIdsFile(
		eolIdsFile: str,
		nodeToSrcIds: dict[int, dict[str, int]],
		usedSrcIds: set[tuple[str, int]],
		nodeToEolId: dict[int, int]) -> None:
	""" Reads EOL provider IDs file, and maps EOL IDs to external-source IDs """
	# The file is a CSV with a header line, then lines that hold these fields:
		# node_id, resource_pk (ID from external source), resource_id (int denoting external-source),
		# page_id (eol ID), preferred_canonical_for_page
	print('Reading EOL provider IDs file')
	srcToEolId: dict[str, dict[int, int]] = {src: {} for src in EOL_SRCS.values()} # Maps src1 to {id1: eolId1, ...}
	with gzip.open(eolIdsFile, mode='rt') as file: # Had about 13e6 lines
		for lineNum, row in enumerate(csv.reader(file), 1):
			if lineNum % 1e6 == 0:
				print(f'At line {lineNum}')

			# Skip header line
			if lineNum == 1:
				continue

			# Parse line
			eolId = int(row[3])
			srcInt = int(row[2])
			srcIdStr = row[1]
			if srcIdStr.isdecimal() and srcInt in EOL_SRCS:
				srcId = int(srcIdStr)
				src = EOL_SRCS[srcInt]
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
	for otolId, srcInfo in nodeToSrcIds.items():
		eolIdToCount: dict[int, int] = defaultdict(int)
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

def readWikidataDb(
		wikidataDb: str,
		nodeToSrcIds: dict[int, dict[str, int]],
		usedSrcIds: set[tuple[str, int]],
		nodeToWikiTitle: dict[int, str],
		titleToIucnStatus: dict[str, str],
		nodeToEolId: dict[int, int]) -> None:
	""" Reads db holding ID and IUCN mappings from wikidata, and maps otol IDs to Wikipedia titles and EOL IDs """
	print('Reading from Wikidata db')
	srcToWikiTitle: dict[str, dict[int, str]] = defaultdict(dict) # Maps 'eol'/etc to {srcId1: title1, ...}
	wikiTitles = set()
	dbCon = sqlite3.connect(wikidataDb)
	dbCur = dbCon.cursor()
	for src, srcId, title in dbCur.execute('SELECT src, id, title from src_id_to_title'):
		if (src, srcId) in usedSrcIds or src == 'eol': # Keep EOL IDs for later use 
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
	for otolId, srcInfo in nodeToSrcIds.items():
		titleToSrcs: dict[str, list[str]] = defaultdict(list) # Maps candidate titles to list of sources
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
			else:
				# Get a title with a source with highest priority
				srcToTitle = {s: t for t in titleToSrcs for s in titleToSrcs[t]}
				for src in OTOL_SRCS:
					if src in srcToTitle:
						nodeToWikiTitle[otolId] = srcToTitle[src]
						break
	print(f'- Result has {len(nodeToWikiTitle):,} entries') # Was about 4e5

	print('Adding extra EOL mappings from Wikidata')
	wikiTitleToNode = {title: node for node, title in nodeToWikiTitle.items()}
	addedEntries: dict[int, int] = {}
	for eolId, title in srcToWikiTitle['eol'].items():
		if title in wikiTitleToNode:
			otolId = wikiTitleToNode[title]
			if otolId not in nodeToEolId: # Only add if the otol ID has no EOL ID
				nodeToEolId[otolId] = eolId
				addedEntries[otolId] = eolId
	print(f'- Added {len(addedEntries):,} entries') # Was about 3e3

def readPickedMappings(
		pickedMappings: dict[str, list[str]],
		nodeToEolId: dict[int, int],
		nodeToWikiTitle: dict[int, str]) -> None:
	""" Read mappings from OTOL IDs to EOL IDs and Wikipedia titles """
	print('Reading picked mappings')
	for src in pickedMappings:
		for filename in pickedMappings[src]:
			if not os.path.exists(filename):
				continue
			with open(filename) as file:
				for line in file:
					otolIdStr, mappedVal = line.rstrip().split('|')
					otolId = int(otolIdStr)
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

def getEnwikiPageIds(enwikiDumpIndexDb: str, nodeToWikiTitle: dict[int, str], titleToPageId: dict[str, int]) -> None:
	""" Read a db for mappings from enwiki titles to page IDs """
	print('Getting enwiki page IDs')
	numNotFound = 0
	dbCon = sqlite3.connect(enwikiDumpIndexDb)
	dbCur = dbCon.cursor()
	for title in nodeToWikiTitle.values():
		record = dbCur.execute('SELECT id FROM offsets WHERE title = ?', (title,)).fetchone()
		if record != None:
			titleToPageId[title] = record[0]
		else:
			numNotFound += 1
	dbCon.close()
	print(f'Unable to find IDs for {numNotFound} titles') # Was 2913

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
	args = parser.parse_args()

	genData(TAXONOMY_FILE, EOL_IDS_FILE, WIKIDATA_DB, PICKED_MAPPINGS, ENWIKI_DUMP_INDEX_DB, DB_FILE)
