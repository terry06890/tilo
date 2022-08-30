#!/usr/bin/python3

import sys, os, re
import sqlite3

import argparse
parser = argparse.ArgumentParser(description='''
Maps nodes to short descriptions, using data from DBpedia and
Wikipedia, and stores results in the database.
''', formatter_class=argparse.RawDescriptionHelpFormatter)
args = parser.parse_args()

dbpediaDb = 'dbpedia/descData.db'
enwikiDb = 'enwiki/descData.db'
dbFile = 'data.db'

print('Creating table')
dbCon = sqlite3.connect(dbFile)
dbCur = dbCon.cursor()
dbCur.execute('CREATE TABLE descs (wiki_id INT PRIMARY KEY, desc TEXT, from_dbp INT)')

print('Getting node mappings')
nodeToWikiId = {}
for name, wikiId in dbCur.execute('SELECT name, id from wiki_ids'):
	nodeToWikiId[name] = wikiId

print('Reading data from DBpedia')
dbpCon = sqlite3.connect(dbpediaDb)
dbpCur = dbpCon.cursor()
print('Getting node IRIs')
nodeToIri = {}
iterNum = 0
for name, wikiId in nodeToWikiId.items():
	iterNum += 1
	if iterNum % 1e5 == 0:
		print(f'At iteration {iterNum}')
	#
	row = dbpCur.execute('SELECT iri FROM ids where id = ?', (wikiId,)).fetchone()
	if row != None:
		nodeToIri[name] = row[0]
print('Resolving redirects')
iterNum = 0
for name, iri in nodeToIri.items():
	iterNum += 1
	if iterNum % 1e5 == 0:
		print(f'At iteration {iterNum}')
	#
	row = dbpCur.execute('SELECT target FROM redirects where iri = ?', (iri,)).fetchone()
	if row != None:
		nodeToIri[name] = row[0]
print('Adding descriptions')
iterNum = 0
for name, iri in nodeToIri.items():
	iterNum += 1
	if iterNum % 1e4 == 0:
		print(f'At iteration {iterNum}')
	#
	row = dbpCur.execute('SELECT abstract FROM abstracts WHERE iri = ?', (iri,)).fetchone()
	if row != None:
		dbCur.execute('INSERT OR IGNORE INTO descs VALUES (?, ?, ?)', (nodeToWikiId[name], row[0], 1))
		del nodeToWikiId[name]
dbpCon.close()

print('Reading data from Wikipedia')
enwikiCon = sqlite3.connect(enwikiDb)
enwikiCur = enwikiCon.cursor()
print('Resolving redirects')
iterNum = 0
for name, wikiId in nodeToWikiId.items():
	iterNum += 1
	if iterNum % 1e4 == 0:
		print(f'At iteration {iterNum}')
	#
	query = 'SELECT pages.id FROM redirects INNER JOIN pages ON redirects.target = pages.title WHERE redirects.id = ?'
	row = enwikiCur.execute(query, (wikiId,)).fetchone()
	if row != None:
		nodeToWikiId[name] = row[0]
print('Adding descriptions')
iterNum = 0
for name, wikiId in nodeToWikiId.items():
	iterNum += 1
	if iterNum % 1e3 == 0:
		print(f'At iteration {iterNum}')
	#
	row = enwikiCur.execute('SELECT desc FROM descs where id = ?', (wikiId,)).fetchone()
	if row != None:
		dbCur.execute('INSERT OR IGNORE INTO descs VALUES (?, ?, ?)', (wikiId, row[0], 0))

print('Closing databases')
dbCon.commit()
dbCon.close()
