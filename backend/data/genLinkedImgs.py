#!/usr/bin/python3

import sys, re
import sqlite3

usageInfo =  f"usage: {sys.argv[0]}\n"
usageInfo += "Adds a table to data.db, associating nodes without images to\n"
usageInfo += "usable child images.\n"
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

dbFile = "data.db"
compoundNameRegex = re.compile(r"\[(.+) \+ (.+)]")
upPropagateCompoundImgs = False

# Open db
dbCon = sqlite3.connect(dbFile)
dbCur = dbCon.cursor()
dbCur.execute("CREATE TABLE linked_imgs (name TEXT PRIMARY KEY, otol_ids TEXT)")
	# Associates a node with one (or two) otol-ids with usable images,
	# encoded as 'otolId1' or 'otolId1,otolId2'
# Get nodes with images
print("Getting nodes with images")
resolvedNodes = {} # Will map node names to otol IDs with a usable image
query = "SELECT nodes.name, nodes.id FROM nodes INNER JOIN node_imgs ON nodes.name = node_imgs.name"
for (name, otolId) in dbCur.execute(query):
	resolvedNodes[name] = otolId
print(f"Got {len(resolvedNodes)} nodes")
# Iterate through resolved nodes, resolving ancestors where able
print("Resolving ancestor nodes")
nodesToResolve = {}
processedNodes = {}
parentToChosenTips = {}
iterNum = 0
while len(resolvedNodes) > 0:
	iterNum += 1
	if iterNum % 1e3 == 0:
		print(f"At iteration {iterNum}")
	# Get next node
	(nodeName, otolId) = resolvedNodes.popitem()
	processedNodes[nodeName] = otolId
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
			childObjs = [{"name": row[0], "tips": row[1], "otolId": None} for row in dbCur.execute(query, childNames)]
			childObjs.sort(key=lambda x: x["tips"], reverse=True)
			nodesToResolve[parent] = childObjs
		else:
			childObjs = nodesToResolve[parent]
		# Check if highest-tips child
		if (childObjs[0]["name"] == nodeName):
			# Resolve parent, and continue from it
			dbCur.execute("INSERT INTO linked_imgs VALUES (?, ?)", (parent, otolId))
			del nodesToResolve[parent]
			processedNodes[parent] = otolId
			parentToChosenTips[parent] = childObjs[0]["tips"]
			nodeName = parent
			continue
		else:
			# Add potential otol-id
			childObj = next(c for c in childObjs if c["name"] == nodeName)
			childObj["otolId"] = otolId
			break
	# When out of resolved nodes, resolve nodesToResolve nodes, possibly adding more nodes to resolve
	if len(resolvedNodes) == 0:
		for (name, childObjs) in nodesToResolve.items():
			childObj = next(c for c in childObjs if c["otolId"] != None)
			resolvedNodes[name] = childObj["otolId"]
			parentToChosenTips[name] = childObj["tips"]
			dbCur.execute("INSERT INTO linked_imgs VALUES (?, ?)", (name, childObj["otolId"]))
		nodesToResolve.clear()
# Iterate through processed nodes with compound names
print("Replacing images for compound-name nodes")
iterNum = 0
for nodeName in processedNodes.keys():
	iterNum += 1
	if iterNum % 1e4 == 0:
		print(f"At iteration {iterNum}")
	#
	match = compoundNameRegex.fullmatch(nodeName)
	if match != None:
		# Replace associated image with subname images
		(subName1, subName2) = match.group(1,2)
		otolIdPair = ["", ""]
		if subName1 in processedNodes:
			otolIdPair[0] = processedNodes[subName1]
		if subName2 in processedNodes:
			otolIdPair[1] = processedNodes[subName2]
		# Use no image if both subimages not found
		if otolIdPair[0] == "" and otolIdPair[1] == "":
			dbCur.execute("DELETE FROM linked_imgs WHERE name = ?", (nodeName,))
			continue
		# Add to db
		dbCur.execute("UPDATE linked_imgs SET otol_ids = ? WHERE name = ?",
			(otolIdPair[0] + "," + otolIdPair[1], nodeName))
		# Possibly repeat operation upon parent/ancestors
		if upPropagateCompoundImgs:
			while True:
				# Get parent
				row = dbCur.execute("SELECT node FROM edges WHERE child = ?", (nodeName,)).fetchone()
				if row != None:
					parent = row[0]
					# Check num tips
					(numTips,) = dbCur.execute("SELECT tips from nodes WHERE name = ?", (nodeName,)).fetchone()
					if parent in parentToChosenTips and parentToChosenTips[parent] <= numTips:
						# Replace associated image
						dbCur.execute("UPDATE linked_imgs SET otol_ids = ? WHERE name = ?",
							(otolIdPair[0] + "," + otolIdPair[1], parent))
						nodeName = parent
						continue
				break
# Close db
dbCon.commit()
dbCon.close()
