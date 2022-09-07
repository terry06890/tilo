#!/usr/bin/python3

import re, os
import html, csv, sqlite3

import argparse
parser = argparse.ArgumentParser(description="""
Maps nodes to vernacular names, using data from EOL, enwiki, and a
picked-names file, and stores results in the database.
""", formatter_class=argparse.RawDescriptionHelpFormatter)
args = parser.parse_args()

eolNamesFile = 'eol/vernacularNames.csv'
enwikiDb = 'enwiki/descData.db'
pickedNamesFile = 'pickedNames.txt'
dbFile = 'data.db'

dbCon = sqlite3.connect(dbFile)
dbCur = dbCon.cursor()

print('Getting node mappings')
nodeToTips: dict[str, int] = {}
eolIdToNode: dict[int, str] = {} # Maps eol ID to node name (if there are multiple, choose one with most tips)
wikiIdToNode: dict[int, str] = {}
for name, tips in dbCur.execute('SELECT name, tips from nodes'):
	nodeToTips[name] = tips
for name, eolId in dbCur.execute('SELECT name, id from eol_ids'):
	if eolId not in eolIdToNode or nodeToTips[eolIdToNode[eolId]] < nodeToTips[name]:
		eolIdToNode[eolId] = name
for name, wikiId in dbCur.execute('SELECT name, id from wiki_ids'):
	if wikiId not in wikiIdToNode or nodeToTips[wikiIdToNode[wikiId]] < nodeToTips[name]:
		wikiIdToNode[wikiId] = name

print('Creating table')
dbCur.execute('CREATE TABLE names(name TEXT, alt_name TEXT, pref_alt INT, src TEXT, PRIMARY KEY(name, alt_name))')
dbCur.execute('CREATE INDEX names_idx ON names(name)')
dbCur.execute('CREATE INDEX names_alt_idx ON names(alt_name)')
dbCur.execute('CREATE INDEX names_alt_idx_nc ON names(alt_name COLLATE NOCASE)')

print('Getting names from EOL')
# The CSV file has a header line, then lines with these fields:
	# page_id, canonical_form (canonical name, not always unique to page ID),
	# vernacular_string (vernacular name), language_code,
	# resource_name, is_preferred_by_resource, is_preferred_by_eol
namesToSkip = {'unknown', 'unknown species', 'unidentified species'}
with open(eolNamesFile, newline='') as file:
	for lineNum, fields in enumerate(csv.reader(file), 1):
		if lineNum % 1e5 == 0:
			print(f'At line {lineNum}') # Reached about 2.8e6
		# Skip header line
		if lineNum == 1:
			continue
		# Parse line
		eolId = int(fields[0])
		name = html.unescape(fields[2]).lower()
		lang = fields[3]
		isPreferred = 1 if fields[6] == 'preferred' else 0
		# Add to db
		if eolId in eolIdToNode and name not in namesToSkip and name not in nodeToTips \
			and lang == 'eng' and len(name.split(' ')) <= 3: # Ignore names with >3 words
			cmd = 'INSERT OR IGNORE INTO names VALUES (?, ?, ?, \'eol\')'
				# The 'OR IGNORE' accounts for duplicate lines
			dbCur.execute(cmd, (eolIdToNode[eolId], name, isPreferred))

print('Getting names from Wikipedia')
altNameRegex = re.compile(r'[a-z]+') # Avoids names like 'evolution of elephants', 'banana fiber', 'fish (zoology)',
enwikiCon = sqlite3.connect(enwikiDb)
enwikiCur = enwikiCon.cursor()
iterNum = 0
for wikiId, nodeName in wikiIdToNode.items():
	iterNum += 1
	if iterNum % 1e4 == 0:
		print(f'At iteration {iterNum}') # Reached about 3.6e5
	#
	query = 'SELECT p1.title FROM pages p1' \
		' INNER JOIN redirects r1 ON p1.id = r1.id' \
		' INNER JOIN pages p2 ON r1.target = p2.title WHERE p2.id = ?'
	for (name,) in enwikiCur.execute(query, (wikiId,)):
		name = name.lower()
		if altNameRegex.fullmatch(name) is not None and name != nodeName and name not in nodeToTips:
			dbCur.execute('INSERT OR IGNORE INTO names VALUES (?, ?, ?, \'enwiki\')', (nodeName, name, 0))

print('Getting picked names')
# File format:
	# nodename1|altName1|isPreferred1 -> Add an alt-name
	# nodename1|altName1|             -> Remove an alt-name
	# nodename1|nodeName1|            -> Remove any preferred-alt status
if os.path.exists(pickedNamesFile):
	with open(pickedNamesFile) as file:
		for line in file:
			nodeName, altName, isPreferredStr = line.lower().rstrip().split('|')
			if nodeName not in nodeToTips:
				print(f'Skipping "{nodeName}", as no such node exists')
				continue
			if isPreferredStr:
				isPreferred = 1 if isPreferredStr == '1' else 0
				if isPreferred == 1:
					# Remove any existing preferred-alt status
					cmd = 'UPDATE names SET pref_alt = 0 WHERE name = ? AND alt_name = ? AND pref_alt = 1'
					dbCur.execute(cmd, (nodeName, altName))
				# Remove any existing record
				dbCur.execute('DELETE FROM names WHERE name = ? AND alt_name = ?', (nodeName, altName))
				# Add record
				dbCur.execute('INSERT INTO names VALUES (?, ?, ?, "picked")', (nodeName, altName, isPreferred))
			elif nodeName != altName: # Remove any matching record
				dbCur.execute('DELETE FROM names WHERE name = ? AND alt_name = ?', (nodeName, altName))
			else: # Remove any preferred-alt status
				cmd = 'UPDATE names SET pref_alt = 0 WHERE name = ? AND alt_name = ? AND pref_alt = 1'
				dbCur.execute(cmd, (nodeName, altName))

print('Closing database')
dbCon.commit()
dbCon.close()
