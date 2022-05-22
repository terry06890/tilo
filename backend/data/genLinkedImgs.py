#!/usr/bin/python3

import sys
import sqlite3

usageInfo =  f"usage: {sys.argv[0]}\n"
usageInfo += "Adds a table to data.db, associating nodes without images to\n"
usageInfo += "usable child images.\n"
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

dbFile = "data.db"

# Open db
dbCon = sqlite3.connect(dbFile)
dbCur = dbCon.cursor()
dbCur.execute("CREATE TABLE linked_imgs (name TEXT PRIMARY KEY, eol_id INT)")
# Get nodes with images
print("Getting nodes with images")
resolvedNodes = {} # Will map node names to eol IDs with a usable image
query = "SELECT nodes.name, eol_ids.id FROM" \
	" nodes INNER JOIN eol_ids ON nodes.name = eol_ids.name" \
		" INNER JOIN images ON eol_ids.id = images.eol_id"
for (name, eolId) in dbCur.execute(query):
	resolvedNodes[name] = eolId
print("Got {} nodes".format(len(resolvedNodes)))
# Iterate through resolved nodes, resolving ancestors where able
print("Resolving ancestor nodes")
nodesToResolve = {}
processedNodes = set()
iterNum = 0
while len(resolvedNodes) > 0:
	iterNum += 1
	if iterNum % 1e3 == 0:
		print("At iteration {}".format(iterNum))
	# Get next node
	(nodeName, eolId) = resolvedNodes.popitem()
	processedNodes.add(nodeName)
	# Traverse upwards, resolving ancestors if able
	while True:
		# Get parent
		row = dbCur.execute("SELECT node FROM edges WHERE child = ?", (nodeName,)).fetchone()
		if row == None or row[0] in processedNodes or row[0] in resolvedNodes:
			break
		parent = row[0]
		# Get parent data
		if parent not in nodesToResolve:
			childNames = [row[0] for row in dbCur.execute("SELECT child FROM edges WHERE node = ?", (parent,))]
			query = "SELECT name, tips FROM nodes WHERE name IN ({})".format(",".join(["?"] * len(childNames)))
			childObjs = [{"name": row[0], "tips": row[1], "eolId": None} for row in dbCur.execute(query, childNames)]
			childObjs.sort(key=lambda x: x["tips"], reverse=True)
			nodesToResolve[parent] = childObjs
		else:
			childObjs = nodesToResolve[parent]
		# Check if highest-tips child
		if (childObjs[0]["name"] == nodeName):
			# Resolve parent, and continue from it
			dbCur.execute("INSERT INTO linked_imgs VALUES (?, ?)", (parent, eolId))
			del nodesToResolve[parent]
			processedNodes.add(parent)
			nodeName = parent
			continue
		else:
			# Add potential EOL ID to parent
			childObj = next(c for c in childObjs if c["name"] == nodeName)
			childObj["eolId"] = eolId
			break
	# When out of resolved nodes, resolve any nodesToResolve nodes
	if len(resolvedNodes) == 0:
		for (name, childObjs) in nodesToResolve.items():
			childObj = next(c for c in childObjs if c["eolId"] != None)
			resolvedNodes[name] = childObj["eolId"]
			dbCur.execute("INSERT INTO linked_imgs VALUES (?, ?)", (name, childObj["eolId"]))
		nodesToResolve.clear()
# Close db
dbCon.commit()
dbCon.close()