#!/usr/bin/python3

import sys, os.path, re
import json, sqlite3

usageInfo =  f"usage: {sys.argv[0]}\n"
usageInfo += "Reads \n"
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

dbFile = "data.db"
nodeNamesFile = "reducedTol/names.txt"
minimalNames = set()
nodeMap = {} # Maps node names to node objects
PREF_NUM_CHILDREN = 3 # Attempt inclusion of children up to this limit
compNameRegex = re.compile(r"\[.+ \+ .+]")

# Connect to db
dbCon = sqlite3.connect(dbFile)
dbCur = dbCon.cursor()
# Read in minimal set of node names
print("Getting minimal name set")
iterNum = 0
with open(nodeNamesFile) as file:
	for line in file:
		iterNum += 1
		if iterNum % 100 == 0:
			print(f"Iteration {iterNum}")
		#
		row = dbCur.execute("SELECT name from nodes WHERE name = ?", (line.rstrip(),)).fetchone()
		if row == None:
			row = dbCur.execute("SELECT name from names WHERE alt_name = ?", (line.rstrip(),)).fetchone()
		if row != None:
			minimalNames.add(row[0])
if len(minimalNames) == 0:
	print("ERROR: No names found", file=sys.stderr)
	sys.exit(1)
print(f"Name set has {len(minimalNames)} names")
# Add nodes that connect up to root
print("Getting connected nodes set")
iterNum = 0
rootName = None
for name in minimalNames:
	iterNum += 1
	if iterNum % 100 == 0:
		print(f"Iteration {iterNum}")
	#
	prevName = None
	while name != None:
		if name not in nodeMap:
			(id, tips) = dbCur.execute("SELECT id, tips from nodes where name = ?", (name,)).fetchone()
			row = dbCur.execute("SELECT node, p_support from edges where child = ?", (name,)).fetchone()
			parent = None if row == None or row[0] == "" else row[0]
			pSupport = 1 if row == None or row[1] == 1 else 0
			nodeMap[name] = {
				"id": id,
				"children": [] if prevName == None else [prevName],
				"parent": parent,
				"tips": 0,
				"pSupport": pSupport,
			}
			prevName = name
			name = parent
		else:
			if prevName != None:
				nodeMap[name]["children"].append(prevName)
			break
	if name == None:
		rootName = prevName
print(f"New node set has {len(nodeMap)} nodes")
# Merge-upward compsite-named nodes
print("Merging-upward composite-named nodes")
namesToRemove = set()
for (name, nodeObj) in nodeMap.items():
	parent = nodeObj["parent"]
	if parent != None and compNameRegex.fullmatch(name) != None:
		# Connect children to parent
		nodeMap[parent]["children"].remove(name)
		nodeMap[parent]["children"].extend(nodeObj["children"])
		for n in nodeObj["children"]:
			nodeMap[n]["parent"] = parent
			nodeMap[n]["pSupport"] &= nodeObj["pSupport"]
		# Remember for removal
		namesToRemove.add(name)
for name in namesToRemove:
	del nodeMap[name]
print(f"New node set has {len(nodeMap)} nodes")
# Remove certain 'chain collapsible' nodes
print("Removing 'chain collapsible' nodes")
namesToRemove2 = set()
for (name, nodeObj) in nodeMap.items():
	hasOneChild = len(nodeObj["children"]) == 1
	isOnlyChild = nodeObj["parent"] != None and len(nodeMap[nodeObj["parent"]]["children"]) == 1
	if name not in minimalNames and (hasOneChild or isOnlyChild):
		parentName = nodeObj["parent"]
		children = nodeObj["children"]
		# Connect parent and children
		nodeMap[parentName]["children"].remove(name)
		nodeMap[parentName]["children"].extend(children)
		for n in children:
			nodeMap[n]["parent"] = parentName
			# Adjust child pSupport
			nodeMap[n]["pSupport"] &= nodeObj["pSupport"]
		# Remember for removal
		namesToRemove2.add(name)
for name in namesToRemove2:
	del nodeMap[name]
	namesToRemove.add(name)
print(f"New node set has {len(nodeMap)} nodes")
# Add some connected children
print("Adding additional nearby children")
namesToAdd = []
iterNum = 0
for (name, nodeObj) in nodeMap.items():
	iterNum += 1
	if iterNum % 100 == 0:
		print(f"Iteration {iterNum}")
	#
	numChildren = len(nodeObj["children"])
	if numChildren < PREF_NUM_CHILDREN:
		children = [row[0] for row in dbCur.execute("SELECT child FROM edges where node = ?", (name,))]
		newChildren = [n for n in children if
			not (n in nodeMap or n in namesToRemove) and
			(dbCur.execute("SELECT name from node_imgs WHERE name = ?", (n,)).fetchone() != None or
				dbCur.execute("SELECT name from linked_imgs WHERE name = ? AND otol_id2 IS NULL", (n,)).fetchone() != None)]
		newChildNames = newChildren[:max(0, PREF_NUM_CHILDREN - numChildren)]
		nodeObj["children"].extend(newChildNames)
		namesToAdd.extend(newChildNames)
for name in namesToAdd:
	(parent, pSupport) = dbCur.execute("SELECT node, p_support from edges WHERE child = ?", (name,)).fetchone()
	(id,) = dbCur.execute("SELECT id FROM nodes WHERE name = ?", (name,)).fetchone()
	parent = None if parent == "" else parent
	nodeMap[name] = {
		"id": id,
		"children": [],
		"parent": parent,
		"tips": 0,
		"pSupport": pSupport == 1,
	}
print(f"New node set has {len(nodeMap)} nodes")
# set tips vals
print("Setting tips vals")
def setTips(nodeName):
	nodeObj = nodeMap[nodeName]
	if len(nodeObj["children"]) == 0:
		nodeObj["tips"] = 1
		return 1
	tips = sum([setTips(childName) for childName in nodeObj["children"]])
	nodeObj["tips"] = tips
	return tips
setTips(rootName)
# Add new nodes to db
print("Adding to db")
dbCur.execute("CREATE TABLE r_nodes (name TEXT PRIMARY KEY, id TEXT UNIQUE, tips INT)")
dbCur.execute("CREATE INDEX r_nodes_idx_nc ON r_nodes(name COLLATE NOCASE)")
dbCur.execute("CREATE TABLE r_edges (node TEXT, child TEXT, p_support INT, PRIMARY KEY (node, child))")
dbCur.execute("CREATE INDEX r_edges_child_idx ON r_edges(child)")
for (name, nodeObj) in nodeMap.items():
	parentName = "" if nodeObj["parent"] == None else nodeObj["parent"]
	dbCur.execute("INSERT INTO r_nodes VALUES (?, ?, ?)", (name, nodeObj["id"], nodeObj["tips"]))
	for childName in nodeObj["children"]:
		pSupport = 1 if nodeMap[childName]["pSupport"] else 0
		dbCur.execute("INSERT INTO r_edges VALUES (?, ?, ?)", (name, childName, pSupport))
# Close db
dbCon.commit()
dbCon.close()
