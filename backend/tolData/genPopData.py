#!/usr/bin/python3

import sqlite3

import argparse
parser = argparse.ArgumentParser(description="""
Reads enwiki page view info from a database, and stores it
as node popularity values in the database.
""", formatter_class=argparse.RawDescriptionHelpFormatter)
args = parser.parse_args()

pageviewsDb = 'enwiki/pageviewData.db'
dbFile = 'data.db'

dbCon = sqlite3.connect(dbFile)
dbCur = dbCon.cursor()

print('Getting view counts')
pdbCon = sqlite3.connect(pageviewsDb)
pdbCur = pdbCon.cursor()
nodeToViews: dict[str, int] = {} # Maps node names to counts
iterNum = 0
for wikiId, views in pdbCur.execute('SELECT id, views from views'):
	iterNum += 1
	if iterNum % 1e4 == 0:
		print(f'At iteration {iterNum}') # Reached 1.6e6
	#
	row = dbCur.execute('SELECT name FROM wiki_ids WHERE id = ?', (wikiId,)).fetchone()
	if row is not None:
		nodeToViews[row[0]] = views
pdbCon.close()

print(f'Writing {len(nodeToViews)} entries to db')
dbCur.execute('CREATE TABLE node_pop (name TEXT PRIMARY KEY, pop INT)')
for nodeName, views in nodeToViews.items():
	dbCur.execute('INSERT INTO node_pop VALUES (?, ?)', (nodeName, views))

dbCon.commit()
dbCon.close()
