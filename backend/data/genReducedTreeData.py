#!/usr/bin/python3

import sys, os.path, re
import json, sqlite3

usageInfo = f"""
Usage: {sys.argv[0]}

Creates a reduced version of the tree in the database.
Reads a subset of the node names from a file, and creates a
minimal tree that contains them, possibly with a few extras.
"""
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

dbFile = "data.db"
nodeNamesFile = "pickedReducedNodes.txt"
minimalNames = set()
nodeMap = {} # Maps node names to node objects
PREF_NUM_CHILDREN = 3 # Attempt inclusion of children up to this limit
compNameRegex = re.compile(r"\[.+ \+ .+]") # Used to recognise composite nodes

class Node:
	" Represents a node from the database "
	def __init__(self, id, children, parent, tips, pSupport):
		self.id = id
		self.children = children
		self.parent = parent
		self.tips = tips
		self.pSupport = pSupport

print("Opening database")
dbCon = sqlite3.connect(dbFile)
dbCur = dbCon.cursor()

print("Getting minimal name set")
iterNum = 0
with open(nodeNamesFile) as file:
	for line in file:
		iterNum += 1
		if iterNum % 100 == 0:
			print(f"At iteration {iterNum}")
		#
		name = line.rstrip()
		row = dbCur.execute("SELECT name from nodes WHERE name = ?", (name,)).fetchone()
		if row == None:
			row = dbCur.execute("SELECT name from names WHERE alt_name = ?", (name,)).fetchone()
		if row != None:
			minimalNames.add(row[0])
if len(minimalNames) == 0:
	print("No names found")
	sys.exit(0)
print(f"Result has {len(minimalNames)} names")

print("Getting ancestor nodes")
rootName = None
iterNum = 0
for name in minimalNames:
	iterNum += 1
	if iterNum % 100 == 0:
		print(f"At iteration {iterNum}")
	#
	prevName = None
	while name != None:
		if name not in nodeMap:
			(id, tips) = dbCur.execute("SELECT id, tips from nodes where name = ?", (name,)).fetchone()
			row = dbCur.execute("SELECT parent, p_support from edges where child = ?", (name,)).fetchone()
			parent = None if row == None or row[0] == "" else row[0]
			pSupport = row == None or row[1] == 1
			children = [] if prevName == None else [prevName]
			nodeMap[name] = Node(id, children, parent, 0, pSupport)
			prevName = name
			name = parent
		else:
			if prevName != None:
				nodeMap[name].children.append(prevName)
			break
	if name == None:
		rootName = prevName
print(f"Result has {len(nodeMap)} nodes")

print("Merging-upward composite nodes")
namesToRemove = set()
for (name, node) in nodeMap.items():
	parent = node.parent
	if parent != None and compNameRegex.fullmatch(name) != None:
		# Connect children to parent
		nodeMap[parent].children.remove(name)
		nodeMap[parent].children.extend(node.children)
		for n in node.children:
			nodeMap[n].parent = parent
			nodeMap[n].pSupport &= node.pSupport
		# Remember for removal
		namesToRemove.add(name)
for name in namesToRemove:
	del nodeMap[name]
print(f"Result has {len(nodeMap)} nodes")

print("Removing 'chain collapsible' nodes")
namesToRemove2 = set()
for (name, node) in nodeMap.items():
	hasOneChild = len(node.children) == 1
	isOnlyChild = node.parent != None and len(nodeMap[node.parent].children) == 1
	if name not in minimalNames and (hasOneChild or isOnlyChild):
		parent = node.parent
		# Connect parent and children
		nodeMap[parent].children.remove(name)
		nodeMap[parent].children.extend(node.children)
		for n in node.children:
			nodeMap[n].parent = parent
			nodeMap[n].pSupport &= node.pSupport
		# Remember for removal
		namesToRemove2.add(name)
for name in namesToRemove2:
	del nodeMap[name]
	namesToRemove.add(name)
print(f"Result has {len(nodeMap)} nodes")

print("Adding some additional nearby children")
namesToAdd = []
iterNum = 0
for (name, node) in nodeMap.items():
	iterNum += 1
	if iterNum % 100 == 0:
		print(f"At iteration {iterNum}")
	#
	numChildren = len(node.children)
	if numChildren < PREF_NUM_CHILDREN:
		children = [row[0] for row in dbCur.execute("SELECT child FROM edges where parent = ?", (name,))]
		newChildren = []
		for n in children:
			if n in nodeMap or n in namesToRemove:
				continue
			if compNameRegex.fullmatch(name) != None:
				continue
			if dbCur.execute("SELECT name from node_imgs WHERE name = ?", (n,)).fetchone() == None:
				continue
			if dbCur.execute("SELECT name from linked_imgs WHERE name = ?", (n,)).fetchone() == None:
				continue
			newChildren.append(n)
		newChildNames = newChildren[:max(0, PREF_NUM_CHILDREN - numChildren)]
		node.children.extend(newChildNames)
		namesToAdd.extend(newChildNames)
for name in namesToAdd:
	parent, pSupport = dbCur.execute("SELECT parent, p_support from edges WHERE child = ?", (name,)).fetchone()
	(id,) = dbCur.execute("SELECT id FROM nodes WHERE name = ?", (name,)).fetchone()
	parent = None if parent == "" else parent
	nodeMap[name] = Node(id, [], parent, 0, pSupport == 1)
print(f"Result has {len(nodeMap)} nodes")

print("Setting 'tips' values")
def setTips(nodeName):
	node = nodeMap[nodeName]
	if len(node.children) == 0:
		node.tips = 1
		return 1
	tips = sum([setTips(childName) for childName in node.children])
	node.tips = tips
	return tips
setTips(rootName)

print("Adding reduced tree to database")
dbCur.execute("CREATE TABLE r_nodes (name TEXT PRIMARY KEY, id TEXT UNIQUE, tips INT)")
dbCur.execute("CREATE INDEX r_nodes_idx_nc ON r_nodes(name COLLATE NOCASE)")
dbCur.execute("CREATE TABLE r_edges (parent TEXT, child TEXT, p_support INT, PRIMARY KEY (parent, child))")
dbCur.execute("CREATE INDEX r_edges_child_idx ON r_edges(child)")
for (name, node) in nodeMap.items():
	parentName = "" if node.parent == None else node.parent
	dbCur.execute("INSERT INTO r_nodes VALUES (?, ?, ?)", (name, node.id, node.tips))
	for childName in node.children:
		pSupport = 1 if nodeMap[childName].pSupport else 0
		dbCur.execute("INSERT INTO r_edges VALUES (?, ?, ?)", (name, childName, pSupport))

print("Closing database")
dbCon.commit()
dbCon.close()
