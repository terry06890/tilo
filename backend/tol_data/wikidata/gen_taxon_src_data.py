#!/usr/bin/python3

"""
Reads a wikidata JSON dump, looking for enwiki taxon items, and associated
IDs from sources like GBIF/etc, and IUCN conservation status. Writes results
into a database.

The JSON dump contains an array of objects, each of which describes a
Wikidata item item1, and takes up it's own line.
- Getting item1's Wikidata ID: item1['id'] (eg: "Q144")
- Checking if item1 is a taxon: item1['claims']['P31'][idx1]['mainsnak']['datavalue']['value']['id'] == id1
	'idx1' indexes an array of statements
	'id1' is a Wikidata ID denoting a taxon item type (eg: Q310890 means 'monotypic taxon')
- Checking if item1 is a taxon-alt: item1['claims']['P31'][idx1]['mainsnak']['datavalue']['value']['id'] == id1
	'id1' denotes a common-name-alternative item type (eg: Q55983715 means 'organisms known by a particular common name')
	Getting the ID of the item that item1 is an alternative for:
		item1['claims']['P31'][idx1]['qualifiers']['P642'][idx2]['datavalue']['value']['numeric-id']
- Checking for an EOL/NCBI/etc ID: item['claims'][prop1][idx1]['mainsnak']['datavalue']['value'] (eg: "328672")
	'prop1' denotes a 'has ID from source *' property (eg: 'P830' means 'has EOL ID')
- Checking for an IUCN status: item['claims']['P141'][idx1]['mainsnak']['datavalue']['value']['id'] (eg: "Q219127")

Based on code from https://github.com/OneZoom/OZtree, located in
OZprivate/ServerScripts/TaxonMappingAndPopularity/ (22 Aug 2022).
"""

# On Linux, running on the full dataset caused the processes to hang after processing. This was resolved by:
# - Storing subprocess results in temp files. Apparently passing large objects through pipes can cause deadlock.
# - Using set_start_method('spawn'). Apparently 'fork' can cause unexpected copying of lock/semaphore/etc state.
#   Related: https://bugs.python.org/issue6721
# - Using pool.map() instead of pool.imap_unordered(), which seems to hang in some cases (was using python 3.8).
#   Possibly related: https://github.com/python/cpython/issues/72882

import sys, os, re, math, io
from collections import defaultdict
import bz2, json, sqlite3
import multiprocessing, indexed_bzip2, pickle, tempfile

WIKIDATA_FILE = 'latest-all.json.bz2'
OFFSETS_FILE = 'offsets.dat'
DB_FILE = 'taxon_srcs.db'
N_PROCS = 6 # Took about 3 hours with N_PROCS=6

# Wikidata entity IDs
TAXON_IDS = ['Q16521', 'Q310890', 'Q23038290', 'Q713623'] # 'taxon', 'monotypic taxon', 'fossil taxon', 'clade'
TAXON_ALT_IDS = ['Q55983715', 'Q502895'] # 'organisms known by a particular common name', 'common name'
SRC_PROP_IDS = {'P830': 'eol', 'P685': 'ncbi', 'P1391': 'if', 'P850': 'worms', 'P5055': 'irmng', 'P846': 'gbif'}
IUCN_STATUS_IDS = {
	'Q211005': 'least concern', 'Q719675': 'near threatened', 'Q278113': 'vulnerable',
	'Q11394': 'endangered', 'Q219127': 'critically endangered', 'Q239509': 'extinct in the wild',
	'Q237350': 'extinct species', 'Q3245245': 'data deficient'
}
# For filtering lines before parsing JSON
LINE_REGEX = re.compile(('"id":(?:"' + '"|"'.join([s for s in TAXON_IDS + TAXON_ALT_IDS]) + '")\D').encode())

def genData(wikidataFile: str, offsetsFile: str, dbFile: str, nProcs: int) -> None:
	""" Reads the dump and writes source/iucn info to db """
	# Maps to populate
	srcIdToId: dict[str, dict[int, int]] = defaultdict(dict) # Maps 'eol'/etc to {srcId1: wikidataId1, ...}
	idToTitle: dict[int, str] = {} # Maps wikidata ID to enwiki title
	idToAltId: dict[int, int] = {} # Maps taxon-item wikidata ID to taxon-alt ID (eg: 'canis lupus familiaris' -> 'dog')
	idToIucnStatus: dict[int, str] = {} # Maps wikidata ID to iucn-status string ('least concern', etc)
	# Check db
	if os.path.exists(dbFile):
		print('ERROR: Database already exists')
		sys.exit(1)
	# Read dump
	if nProcs == 1:
		with bz2.open(wikidataFile, mode='rb') as file:
			for lineNum, line in enumerate(file, 1):
				if lineNum % 1e4 == 0:
					print(f'At line {lineNum}')
				readDumpLine(line, srcIdToId, idToTitle, idToAltId, idToIucnStatus)
	else:
		if not os.path.exists(offsetsFile):
			print('Creating offsets file') # For indexed access for multiprocessing (creation took about 6.7 hours)
			with indexed_bzip2.open(wikidataFile) as file:
				with open(offsetsFile, 'wb') as file2:
					pickle.dump(file.block_offsets(), file2)
		print('Allocating file into chunks')
		fileSz: int # About 1.4 TB
		with indexed_bzip2.open(wikidataFile) as file:
			with open(offsetsFile, 'rb') as file2:
				file.set_block_offsets(pickle.load(file2))
				fileSz = file.seek(0, io.SEEK_END)
		chunkSz = math.floor(fileSz / nProcs)
		chunkIdxs = [-1] + [chunkSz * i for i in range(1, nProcs)] + [fileSz-1]
			# Each adjacent pair specifies a start+end byte index for readDumpChunk()
		print(f'- Chunk size: {chunkSz:,}')
		print('Starting processes to read dump')
		with tempfile.TemporaryDirectory() as tempDirName:
			# Using maxtasksperchild=1 to free resources on task completion
			with multiprocessing.Pool(processes=nProcs, maxtasksperchild=1) as pool:
				for outFilename in pool.map(
						readDumpChunkOneParam,
						((i, wikidataFile, offsetsFile, chunkIdxs[i], chunkIdxs[i+1],
							os.path.join(tempDirName, f'{i}.pickle')) for i in range(nProcs))):
					# Get map data from subprocess output file
					with open(outFilename, 'rb') as file:
						maps = pickle.load(file)
					# Add to maps
					for src, idMap in maps[0].items():
						srcIdToId[src].update(idMap)
					idToTitle.update(maps[1])
					idToAltId.update(maps[2])
					idToIucnStatus.update(maps[3])
	#
	print('Writing to db')
	dbCon = sqlite3.connect(dbFile)
	dbCur = dbCon.cursor()
	dbCur.execute('CREATE TABLE src_id_to_title (src TEXT, id INT, title TEXT, PRIMARY KEY(src, id))')
	for src, submap in srcIdToId.items():
		for srcId, wId in submap.items():
			if wId not in idToTitle: # Check for a title, possibly via an alt-taxon
				if wId in idToAltId:
					wId = idToAltId[wId]
				else:
					continue
			dbCur.execute('INSERT INTO src_id_to_title VALUES (?, ?, ?)', (src, srcId, idToTitle[wId]))
	dbCur.execute('CREATE TABLE title_iucn (title TEXT PRIMARY KEY, status TEXT)')
	for wId, status in idToIucnStatus.items():
		if wId not in idToTitle: # Check for a title, possibly via an alt-taxon
			if wId in idToAltId and idToAltId[wId] not in idToIucnStatus:
				wId = idToAltId[wId]
			else:
				continue
		dbCur.execute('INSERT OR IGNORE INTO title_iucn VALUES (?, ?)', (idToTitle[wId], status))
			# The 'OR IGNORE' allows for multiple taxons using the same alt
	dbCon.commit()
	dbCon.close()
def readDumpLine(
		lineBytes: bytes,
		srcIdToId: dict[str, dict[int, int]],
		idToTitle: dict[int, str],
		idToAltId: dict[int, int],
		idToIucnStatus: dict[int, str]) -> None:
	# Check if taxon item
	if LINE_REGEX.search(lineBytes) is None:
		return
	try:
		line = lineBytes.decode('utf-8').rstrip().rstrip(',')
		jsonItem = json.loads(line)
	except json.JSONDecodeError:
		print(f'Unable to parse line {line} as JSON')
		return
	isTaxon = False
	altTaxa: list[int] = [] # For a taxon-alt item, holds associated taxon-item IDs
	claims = None
	try:
		claims = jsonItem['claims']
		for statement in claims['P31']: # Check for 'instance of' statements
			typeId: str = statement['mainsnak']['datavalue']['value']['id']
			if typeId in TAXON_IDS:
				isTaxon = True
				break
			elif typeId in TAXON_ALT_IDS:
				snaks = statement['qualifiers']['P642'] # Check for 'of' qualifiers
				altTaxa.extend([int(s['datavalue']['value']['numeric-id']) for s in snaks])
				break
	except (KeyError, ValueError):
		return
	if not isTaxon and not altTaxa:
		return
	# Get wikidata ID and enwiki title
	itemId: int | None = None
	itemTitle: str | None = None
	try:
		itemId = int(jsonItem['id'][1:]) # Skips initial 'Q'
		itemTitle = jsonItem['sitelinks']['enwiki']['title']
	except KeyError:
		# Allow taxon-items without titles (they might get one via a taxon-alt)
		if itemId is not None and isTaxon:
			itemTitle = None
		else:
			return
	# Update maps
	if itemTitle is not None:
		idToTitle[itemId] = itemTitle
	for altId in altTaxa:
		idToAltId[altId] = itemId
	# Check for source IDs
	for srcPropId, src in SRC_PROP_IDS.items():
		if srcPropId in claims:
			try:
				srcId = int(claims[srcPropId][0]['mainsnak']['datavalue']['value'])
				srcIdToId[src][srcId] = itemId
			except (KeyError, ValueError):
				continue
	# Check for IUCN status
	if 'P141' in claims: # Check for 'iucn conservation status' statement
		try:
			iucnStatusId: str = claims['P141'][0]['mainsnak']['datavalue']['value']['id']
			idToIucnStatus[itemId] = IUCN_STATUS_IDS[iucnStatusId]
		except KeyError:
			pass
def readDumpChunkOneParam(params: tuple[int, str, str, int, int, str]) -> str:
	""" Forwards to readDumpChunk(), for use with pool.map() """
	return readDumpChunk(*params)
def readDumpChunk(
		procId: int, wikidataFile: str, offsetsFile: str, startByte: int, endByte: int, outFilename: str) -> str:
	""" Reads lines in the dump that begin after a start-byte, and not after an end byte.
		If startByte is -1, start at the first line. """
	# Maps to populate
	maps: tuple[
		dict[str, dict[int, int]],
		dict[int, str],
		dict[int, int],
		dict[int, str]] = (defaultdict(dict), {}, {}, {})
	# Read dump
	with indexed_bzip2.open(wikidataFile) as file:
		# Load offsets file
		with open(offsetsFile, 'rb') as file2:
			offsets = pickle.load(file2)
			file.set_block_offsets(offsets)
		# Seek to chunk
		if startByte != -1:
			file.seek(startByte)
			file.readline()
		else:
			startByte = 0 # Used for progress calculation
		# Read lines
		count = 0
		while file.tell() <= endByte:
			count += 1
			if count % 1e4 == 0:
				perc = (file.tell() - startByte) / (endByte - startByte) * 100
				print(f'Thread {procId}: {perc:.2f}%')
			readDumpLine(file.readline(), *maps)
	# Output results into file
	with open(outFilename, 'wb') as file:
		pickle.dump(maps, file)
	return outFilename

if __name__ == '__main__': # Guard needed for multiprocessing
	import argparse
	parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
	args = parser.parse_args()
	#
	multiprocessing.set_start_method('spawn')
	genData(WIKIDATA_FILE, OFFSETS_FILE, DB_FILE, N_PROCS)
