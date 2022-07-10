#!/usr/bin/python3

import sys, re
import sqlite3

usageInfo = f"""
Usage: {sys.argv[0]}

Reads from a database containing data from Wikipdia, along with
node and wiki-id information from the database, and use wikipedia
page-redirect information to add additional alt-name data.
"""
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

enwikiDb = "enwiki/descData.db"
dbFile = "data.db"
altNameRegex = re.compile(r"[a-zA-Z]+")
	# Avoids names like 'Evolution of Elephants', 'Banana fiber', 'Fish (zoology)',

print("Opening databases")
enwikiCon = sqlite3.connect(enwikiDb)
enwikiCur = enwikiCon.cursor()
dbCon = sqlite3.connect(dbFile)
dbCur = dbCon.cursor()

print("Getting nodes with wiki IDs")
nodeToWikiId = {}
for (nodeName, wikiId) in dbCur.execute("SELECT name, id from wiki_ids"):
	nodeToWikiId[nodeName] = wikiId
print(f"Found {len(nodeToWikiId)}")

print("Iterating through nodes, finding names that redirect to them")
nodeToAltNames = {}
numAltNames = 0
iterNum = 0
for (nodeName, wikiId) in nodeToWikiId.items():
	iterNum += 1
	if iterNum % 1e4 == 0:
		print(f"At iteration {iterNum}")
	#
	nodeToAltNames[nodeName] = set()
	query = "SELECT p1.title FROM pages p1" \
		" INNER JOIN redirects r1 ON p1.id = r1.id" \
		" INNER JOIN pages p2 ON r1.target = p2.title WHERE p2.id = ?"
	for (name,) in enwikiCur.execute(query, (wikiId,)):
		if altNameRegex.fullmatch(name) != None and name.lower() != nodeName:
			nodeToAltNames[nodeName].add(name.lower())
			numAltNames += 1
print(f"Found {numAltNames} alt-names")

print("Excluding existing alt-names from the set")
query = "SELECT alt_name FROM names WHERE alt_name IN ({})"
iterNum = 0
for (nodeName, altNames) in nodeToAltNames.items():
	iterNum += 1
	if iterNum % 1e4 == 0:
		print(f"At iteration {iterNum}")
	#
	existingNames = set()
	for (name,) in dbCur.execute(query.format(",".join(["?"] * len(altNames))), list(altNames)):
		existingNames.add(name)
	numAltNames -= len(existingNames)
	altNames.difference_update(existingNames)
print(f"Left with {numAltNames} alt-names")

print("Adding alt-names to database")
for (nodeName, altNames) in nodeToAltNames.items():
	for altName in altNames:
		dbCur.execute("INSERT INTO names VALUES (?, ?, ?, 'enwiki')", (nodeName, altName, 0))

print("Closing databases")
dbCon.commit()
dbCon.close()
enwikiCon.close()
