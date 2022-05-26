#!/usr/bin/python3

import sys, re
import sqlite3

usageInfo =  f"usage: {sys.argv[0]}\n"
usageInfo += "Reads Wikimedia enwiki redirect data from enwiki/, and node and wiki-id\n"
usageInfo += "data from a sqlite database, and adds supplmenentary alt-name data.\n"
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

enwikiDb = "enwiki/enwikiData.db"
dbFile = "data.db"
altNameRegex = re.compile(r"[a-zA-Z]+")
	# Avoids names like 'Evolution of Elephants', 'Banana fiber', 'Fish (zoology)',

# Open dbs
enwikiCon = sqlite3.connect(enwikiDb)
enwikiCur = enwikiCon.cursor()
dbCon = sqlite3.connect(dbFile)
dbCur = dbCon.cursor()
# Get nodes with wiki-ids
print("Getting nodes with wiki IDs")
nodeToWikiId = {}
for row in dbCur.execute("SELECT name, wiki_id from descs"):
	nodeToWikiId[row[0]] = row[1]
print("Found {} nodes".format(len(nodeToWikiId)))
# Find wiki-ids that redirect to each node
print("Finding redirecter names")
nodeToAltNames = {}
numAltNames = 0
iterNum = 0
for (nodeName, wikiId) in nodeToWikiId.items():
	iterNum += 1
	if iterNum % 1e4 == 0:
		print("At iteration {}".format(iterNum))
	#
	nodeToAltNames[nodeName] = set()
	query = "SELECT p1.title FROM pages p1" \
		" INNER JOIN redirects r1 ON p1.id = r1.id" \
		" INNER JOIN pages p2 ON r1.target = p2.title WHERE p2.id = ?"
	for (name,) in enwikiCur.execute(query, (wikiId,)):
		if altNameRegex.fullmatch(name) != None:
			nodeToAltNames[nodeName].add(name.lower())
			numAltNames += 1
print("Found {} alt-names".format(numAltNames))
# Remove existing alt-names
print("Removing existing alt-names")
query = "SELECT alt_name FROM names WHERE alt_name IN ({})"
iterNum = 0
for (nodeName, altNames) in nodeToAltNames.items():
	iterNum += 1
	if iterNum % 1e4 == 0:
		print("At iteration {}".format(iterNum))
	#
	existingNames = set()
	for (name,) in dbCur.execute(query.format(",".join(["?"] * len(altNames))), list(altNames)):
		existingNames.add(name)
	numAltNames -= len(existingNames)
	altNames.difference_update(existingNames)
print("Left with {} alt-names".format(numAltNames))
# Add alt-names
print("Adding alt-names")
for (nodeName, altNames) in nodeToAltNames.items():
	for altName in altNames:
		dbCur.execute("INSERT INTO names VALUES (?, ?, ?)", (nodeName, altName, 0))
# Close dbs
dbCon.commit()
dbCon.close()
enwikiCon.close()
