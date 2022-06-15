#!/usr/bin/python3

import sys
import sqlite3

usageInfo =  f"usage: {sys.argv[0]}\n"
usageInfo += "Removes certain children from a tol-tree in an sqlite db.\n"
usageInfo += "Looks for nodes with an amount of children above a threshold,\n"
usageInfo += "and removes the excess, excluding those with 'significant'\n"
usageInfo += "associations, like those with descriptions and images.\n"
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

dbFile = "data.db"
softChildLimit = 100

dbCon = sqlite3.connect(dbFile)
dbCur = dbCon.cursor()
# Get nodes that shouldn't be deleted, along with their ancestors
print("Finding nodes to keep")
nodesToKeep = set()
print("\tFinding nodes with descs")
for (name,) in dbCur.execute("SELECT name FROM descs"):
	nodesToKeep.add(name)
print("\tFinding nodes with images")
for (name,) in dbCur.execute("SELECT name FROM nodes INNER JOIN node_imgs ON nodes.id = node_imgs.id"):
	nodesToKeep.add(name)
print("\tFinding nodes in reduced-tree")
for (name,) in dbCur.execute("SELECT name from r_nodes"):
	nodesToKeep.add(name)
print("\tFinding ancestors")
ancestors = set()
iterNum = 0
for name in nodesToKeep:
	iterNum += 1
	if iterNum % 1e4 == 0:
		print(f"\tAt iteration {iterNum}")
	#
	while True:
		row = dbCur.execute("SELECT node FROM edges WHERE child = ?", (name,)).fetchone()
		if row != None:
			parent = row[0]
			if parent not in nodesToKeep and parent not in ancestors:
				ancestors.add(parent)
				continue
		break
nodesToKeep.update(ancestors)
print(f"Total of {len(nodesToKeep)} nodes to keep")
# Find root node
query = "SELECT name FROM nodes LEFT JOIN edges ON nodes.name = edges.child WHERE edges.node IS NULL LIMIT 1"
(rootName,) = dbCur.execute(query).fetchone()
print(f"Found root node {rootName}")
# Traverse tree, looking for trimmable nodes
print("Looking for trimmable nodes")
nodeToTipsChg = {}
nodesToDelete = set()
iterNum = 0
def findTrimmables(nodeName):
	global iterNum
	iterNum += 1
	if iterNum % 1e4 == 0:
		print(f"At iteration {iterNum}")
	#
	childNames = [row[0] for row in dbCur.execute("SELECT child FROM edges WHERE node = ?", (nodeName,))]
	tipsRemoved = 0
	if len(childNames) > softChildLimit:
		# Look for children to delete, excluding 'kept nodes'
		childrenToKeep, otherChildren = [], []
		for n in childNames:
			if n in nodesToKeep:
				childrenToKeep.append(n)
			else:
				otherChildren.append(n)
		# Only trim beyond threshold
		if len(childrenToKeep) < softChildLimit:
			numMoreToKeep = softChildLimit - len(childrenToKeep)
			# Prefer keeping nodes with more tips
			childToTips = {}
			query = "SELECT name, tips FROM nodes WHERE name IN ({})".format(",".join(["?"] * len(otherChildren)))
			for (n, tips) in dbCur.execute(query, otherChildren):
				childToTips[n] = tips
			otherChildren.sort(key=lambda n: childToTips[n], reverse=True)
			childrenToKeep.extend(otherChildren[:numMoreToKeep])
			otherChildren = otherChildren[numMoreToKeep:]
		# 'Simulate' deletions
		childNames = childrenToKeep
		for n in otherChildren:
			tipsRemoved += markForDeletion(n)
	# Recurse on children
	for n in childNames:
		tipsRemoved += findTrimmables(n)
	# Store info for updating num-tips later
	nodeToTipsChg[nodeName] = tipsRemoved
	return tipsRemoved
def markForDeletion(nodeName):
	nodesToDelete.add(nodeName)
	childNames = [row[0] for row in dbCur.execute("SELECT child FROM edges WHERE node = ?", (nodeName,))]
	if len(childNames) == 0:
		return 1
	else:
		tipsRemoved = 0
		for n in childNames:
			tipsRemoved += markForDeletion(n)
		return tipsRemoved
findTrimmables(rootName)
# Delete trimmable nodes
print(f"Deleting {len(nodesToDelete)} nodes")
iterNum = 0
for nodeName in nodesToDelete:
	iterNum += 1
	if iterNum % 1e4 == 0:
		print(f"At iteration {iterNum}")
	#
	dbCur.execute("DELETE FROM nodes WHERE name = ?", (nodeName,))
	dbCur.execute("DELETE FROM edges WHERE node = ?", (nodeName,))
	dbCur.execute("DELETE FROM edges WHERE child = ?", (nodeName,))
	dbCur.execute("DELETE FROM names WHERE name = ?", (nodeName,))
	dbCur.execute("DELETE FROM eol_ids WHERE name = ?", (nodeName,))
print(f"Updating num-tips for {len(nodeToTipsChg)} nodes")
iterNum = 0
for (nodeName, tipsChg) in nodeToTipsChg.items():
	iterNum += 1
	if iterNum % 1e5 == 0:
		print(f"At iteration {iterNum}")
	#
	dbCur.execute("UPDATE nodes SET tips = tips - ? WHERE name = ?", (tipsChg, nodeName))
# Close db
dbCon.commit()
dbCon.close()
