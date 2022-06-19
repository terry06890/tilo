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
softChildLimit = 500

dbCon = sqlite3.connect(dbFile)
dbCur = dbCon.cursor()
# Get nodes that shouldn't be deleted, along with their ancestors
print("Finding nodes to keep")
nodesToKeep = set()
nodesToStronglyKeep = set()
print("\tFinding nodes with descs")
for (name,) in dbCur.execute("SELECT name FROM wiki_ids"): # Can assume the wiki_id has a desc
	nodesToKeep.add(name)
print("\tFinding nodes with images")
for (name,) in dbCur.execute("SELECT name FROM node_imgs"):
	nodesToKeep.add(name)
	nodesToStronglyKeep.add(name)
print("\tFinding nodes in reduced-tree")
for (name,) in dbCur.execute("SELECT name from r_nodes"):
	nodesToKeep.add(name)
	nodesToStronglyKeep.add(name)
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
				if name in nodesToStronglyKeep:
					nodesToStronglyKeep.add(parent)
				name = parent
				continue
		break
nodesToKeep.update(ancestors)
print(f"Total of {len(nodesToKeep)} nodes to keep")
# Find root node
query = "SELECT name FROM nodes LEFT JOIN edges ON nodes.name = edges.child WHERE edges.node IS NULL LIMIT 1"
(rootName,) = dbCur.execute(query).fetchone()
print(f"Found root node '{rootName}'")
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
	childrenToKeep, otherChildren = set(), set()
	for n in childNames:
		if n in nodesToKeep:
			childrenToKeep.add(n)
		else:
			otherChildren.add(n)
	# Check soft limit
	tipsRemoved = 0
	if len(childrenToKeep) > softChildLimit:
		numToTrim = len(childrenToKeep) - softChildLimit
		# Try removing weakly-kept nodes, preferring those with less tips
		candidatesToTrim = [n for n in childrenToKeep if n not in nodesToStronglyKeep]
		childToTips = {}
		query = "SELECT name, tips FROM nodes WHERE name IN ({})".format(",".join(["?"] * len(candidatesToTrim)))
		for (n, tips) in dbCur.execute(query, candidatesToTrim):
			childToTips[n] = tips
		candidatesToTrim.sort(key=lambda n: childToTips[n], reverse=True)
		otherChildren.update(candidatesToTrim[-numToTrim:])
		childrenToKeep.difference_update(candidatesToTrim[-numToTrim:])
	# 'Simulate' deletions
	for n in otherChildren:
		tipsRemoved += markForDeletion(n)
	# Recurse on children
	for n in childrenToKeep:
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
