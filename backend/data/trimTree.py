#!/usr/bin/python3

import sys
import sqlite3

usageInfo = f"""
Usage: {sys.argv[0]}

Tries to remove 'low significance' nodes from the database. Currently
removes nodes that don't have an image or description, or a presence in
the reduced tree. Also, for nodes with 'many' children, trims some more,
ignoring the presence of node descriptions.
"""
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

dbFile = "data.db"
softChildLimit = 500 # Used to determine when a node has 'many' children

print("Opening database")
dbCon = sqlite3.connect(dbFile)
dbCur = dbCon.cursor()

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
		row = dbCur.execute("SELECT parent FROM edges WHERE child = ?", (name,)).fetchone()
		if row != None:
			parent = row[0]
			if parent not in nodesToKeep and parent not in ancestors:
				ancestors.add(parent)
				if name not in nodesToStronglyKeep:
					nodesToStronglyKeep.add(parent)
				name = parent
				continue
		break
nodesToKeep.update(ancestors)
print(f"Result: {len(nodesToKeep)} nodes to keep")

# Find root node
query = "SELECT name FROM nodes LEFT JOIN edges ON nodes.name = edges.child WHERE edges.parent IS NULL LIMIT 1"
(rootName,) = dbCur.execute(query).fetchone()
print(f"Found root node \"{rootName}\"")

print("Looking for trimmable nodes")
nodeToTipsChg = {} # Used to update 'tips' values after trimming
nodesToDelete = set()
iterNum = 0
def findTrimmables(nodeName):
	global iterNum
	iterNum += 1
	if iterNum % 1e4 == 0:
		print(f"At iteration {iterNum}")
	#
	childNames = [row[0] for row in dbCur.execute("SELECT child FROM edges WHERE parent = ?", (nodeName,))]
	childrenToKeep, otherChildren = set(), set()
	for n in childNames:
		if n in nodesToKeep:
			childrenToKeep.add(n)
		else:
			otherChildren.add(n)
	tipsRemoved = 0
	# Check soft limit
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
	# Mark nodes for deletion
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
	childNames = [row[0] for row in dbCur.execute("SELECT child FROM edges WHERE parent = ?", (nodeName,))]
	if len(childNames) == 0:
		return 1
	else:
		tipsRemoved = 0
		for n in childNames:
			tipsRemoved += markForDeletion(n)
		return tipsRemoved
findTrimmables(rootName)

print(f"Deleting {len(nodesToDelete)} nodes")
iterNum = 0
for nodeName in nodesToDelete:
	iterNum += 1
	if iterNum % 1e4 == 0:
		print(f"At iteration {iterNum}")
	#
	dbCur.execute("DELETE FROM nodes WHERE name = ?", (nodeName,))
	dbCur.execute("DELETE FROM edges WHERE parent = ?", (nodeName,))
	dbCur.execute("DELETE FROM edges WHERE child = ?", (nodeName,))
	dbCur.execute("DELETE FROM names WHERE name = ?", (nodeName,))
	# Could also delete from 'eol_ids', 'wiki_ids', and 'descs', but this
		# makes it much harder to restore the original data if needed, and
		# the memory savings didn't seem significant.

print(f"Updating num-tips for {len(nodeToTipsChg)} nodes")
iterNum = 0
for (nodeName, tipsChg) in nodeToTipsChg.items():
	iterNum += 1
	if iterNum % 1e5 == 0:
		print(f"At iteration {iterNum}")
	#
	dbCur.execute("UPDATE nodes SET tips = tips - ? WHERE name = ?", (tipsChg, nodeName))

print("Closing database")
dbCon.commit()
dbCon.close()
