#!/usr/bin/python3

"""
Adds DBpedia labels/types/abstracts/etc data into a database
"""

# In testing, this script took a few hours to run, and generated about 10GB

import argparse
import re
import bz2
import sqlite3

LABELS_FILE = 'labels_lang=en.ttl.bz2' # Had about 16e6 entries
IDS_FILE = 'page_lang=en_ids.ttl.bz2'
REDIRECTS_FILE = 'redirects_lang=en_transitive.ttl.bz2'
DISAMBIG_FILE = 'disambiguations_lang=en.ttl.bz2'
TYPES_FILE = 'instance-types_lang=en_specific.ttl.bz2'
ABSTRACTS_FILE = 'short-abstracts_lang=en.ttl.bz2'
DB_FILE = 'desc_data.db'

def genData(
		labelsFile: str, idsFile: str, redirectsFile: str, disambigFile: str,
		typesFile: str, abstractsFile: str, dbFile: str) -> None:
	""" Reads the files and writes to db """
	print('Creating database')
	dbCon = sqlite3.connect(dbFile)
	dbCur = dbCon.cursor()

	print('Reading/storing label data')
	dbCur.execute('CREATE TABLE labels (iri TEXT PRIMARY KEY, label TEXT)')
	dbCur.execute('CREATE INDEX labels_idx ON labels(label)')
	dbCur.execute('CREATE INDEX labels_idx_nc ON labels(label COLLATE NOCASE)')
	labelLineRegex = re.compile(r'<([^>]+)> <[^>]+> "((?:[^"]|\\")+)"@en \.\n')
	with bz2.open(labelsFile, mode='rt') as file:
		for lineNum, line in enumerate(file, 1):
			if lineNum % 1e5 == 0:
				print(f'At line {lineNum}')
			match = labelLineRegex.fullmatch(line)
			if match is None:
				raise Exception(f'ERROR: Line {lineNum} has unexpected format')
			dbCur.execute('INSERT INTO labels VALUES (?, ?)', (match.group(1), match.group(2)))

	print('Reading/storing wiki page ids')
	dbCur.execute('CREATE TABLE ids (iri TEXT PRIMARY KEY, id INT)')
	dbCur.execute('CREATE INDEX ids_idx ON ids(id)')
	idLineRegex = re.compile(r'<([^>]+)> <[^>]+> "(\d+)".*\n')
	with bz2.open(idsFile, mode='rt') as file:
		for lineNum, line in enumerate(file, 1):
			if lineNum % 1e5 == 0:
				print(f'At line {lineNum}')
			match = idLineRegex.fullmatch(line)
			if match is None:
				raise Exception(f'ERROR: Line {lineNum} has unexpected format')
			try:
				dbCur.execute('INSERT INTO ids VALUES (?, ?)', (match.group(1), int(match.group(2))))
			except sqlite3.IntegrityError as e:
				# Accounts for certain lines that have the same IRI
				print(f'WARNING: Failed to add entry with IRI "{match.group(1)}": {e}')

	print('Reading/storing redirection data')
	dbCur.execute('CREATE TABLE redirects (iri TEXT PRIMARY KEY, target TEXT)')
	redirLineRegex = re.compile(r'<([^>]+)> <[^>]+> <([^>]+)> \.\n')
	with bz2.open(redirectsFile, mode='rt') as file:
		for lineNum, line in enumerate(file, 1):
			if lineNum % 1e5 == 0:
				print(f'At line {lineNum}')
			match = redirLineRegex.fullmatch(line)
			if match is None:
				raise Exception(f'ERROR: Line {lineNum} has unexpected format')
			dbCur.execute('INSERT INTO redirects VALUES (?, ?)', (match.group(1), match.group(2)))

	print('Reading/storing diambiguation-page data')
	dbCur.execute('CREATE TABLE disambiguations (iri TEXT PRIMARY KEY)')
	disambigLineRegex = redirLineRegex
	with bz2.open(disambigFile, mode='rt') as file:
		for lineNum, line in enumerate(file, 1):
			if lineNum % 1e5 == 0:
				print(f'At line {lineNum}')
			match = disambigLineRegex.fullmatch(line)
			if match is None:
				raise Exception(f'ERROR: Line {lineNum} has unexpected format')
			dbCur.execute('INSERT OR IGNORE INTO disambiguations VALUES (?)', (match.group(1),))

	print('Reading/storing instance-type data')
	dbCur.execute('CREATE TABLE types (iri TEXT, type TEXT)')
	dbCur.execute('CREATE INDEX types_iri_idx ON types(iri)')
	typeLineRegex = redirLineRegex
	with bz2.open(typesFile, mode='rt') as file:
		for lineNum, line in enumerate(file, 1):
			if lineNum % 1e5 == 0:
				print(f'At line {lineNum}')
			match = typeLineRegex.fullmatch(line)
			if match is None:
				raise Exception(f'ERROR: Line {lineNum} has unexpected format')
			dbCur.execute('INSERT INTO types VALUES (?, ?)', (match.group(1), match.group(2)))

	print('Reading/storing abstracts')
	dbCur.execute('CREATE TABLE abstracts (iri TEXT PRIMARY KEY, abstract TEXT)')
	descLineRegex = labelLineRegex
	with bz2.open(abstractsFile, mode='rt') as file:
		for lineNum, line in enumerate(file):
			if lineNum % 1e5 == 0:
				print(f'At line {lineNum}')
			if line[0] == '#':
				continue
			match = descLineRegex.fullmatch(line)
			if match is None:
				raise Exception(f'ERROR: Line {lineNum} has unexpected format')
			dbCur.execute('INSERT INTO abstracts VALUES (?, ?)',
				(match.group(1), match.group(2).replace(r'\"', '"')))

	print('Closing database')
	dbCon.commit()
	dbCon.close()

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.parse_args()

	genData(LABELS_FILE, IDS_FILE, REDIRECTS_FILE, DISAMBIG_FILE, TYPES_FILE, ABSTRACTS_FILE, DB_FILE)
