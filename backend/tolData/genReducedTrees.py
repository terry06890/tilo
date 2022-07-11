#!/usr/bin/python3

import sys, os.path, re
import json, sqlite3

usageInfo = f"""
Usage: {sys.argv[0]} [tree1]

Creates reduced versions of the tree in the database:
- A 'picked nodes' tree:
    Created from a minimal set of node names read from a file,
    possibly with some extra randmly-picked children.
- An 'images only' tree:
    Created by removing nodes without an image or presence in the
    'picked' tree.
- A 'weakly trimmed' tree:
    Created by removing nodes that lack an image or description, or
    presence in the 'picked' tree. And, for nodes with 'many' children,
    removing some more, despite any node descriptions.

If tree1 is specified, as 'picked', 'images', or 'trimmed', only that
tree is generated.
"""
if len(sys.argv) > 2 or len(sys.argv) == 2 and re.fullmatch(r"picked|images|trimmed", sys.argv[1]) == None:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

tree = sys.argv[1] if len(sys.argv) > 1 else None
dbFile = "data.db"
pickedNodesFile = "pickedNodes.txt"
COMP_NAME_REGEX = re.compile(r"\[.+ \+ .+]") # Used to recognise composite nodes

class Node:
	def __init__(self, id, children, parent, tips, pSupport):
		self.id = id
		self.children = children
		self.parent = parent
		self.tips = tips
		self.pSupport = pSupport

print("Opening database")
dbCon = sqlite3.connect(dbFile)
dbCur = dbCon.cursor()

def genPickedNodeTree(dbCur, pickedNames, rootName):
	global COMP_NAME_REGEX
	PREF_NUM_CHILDREN = 3 # Include extra children up to this limit
	nodeMap = {} # Maps node names to Nodes
	print("Getting ancestors")
	nodeMap = genNodeMap(dbCur, pickedNames, 100)
	print(f"Result has {len(nodeMap)} nodes")
	print("Removing composite nodes")
	removedNames = removeCompositeNodes(nodeMap)
	print(f"Result has {len(nodeMap)} nodes")
	print("Removing 'collapsible' nodes")
	temp = removeCollapsibleNodes(nodeMap, pickedNames)
	removedNames.update(temp)
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
				if n in nodeMap or n in removedNames:
					continue
				if COMP_NAME_REGEX.fullmatch(n) != None:
					continue
				if dbCur.execute("SELECT name from node_imgs WHERE name = ?", (n,)).fetchone() == None and \
					dbCur.execute("SELECT name from linked_imgs WHERE name = ?", (n,)).fetchone() == None:
					continue
				newChildren.append(n)
			newChildNames = newChildren[:(PREF_NUM_CHILDREN - numChildren)]
			node.children.extend(newChildNames)
			namesToAdd.extend(newChildNames)
	for name in namesToAdd:
		parent, pSupport = dbCur.execute("SELECT parent, p_support from edges WHERE child = ?", (name,)).fetchone()
		(id,) = dbCur.execute("SELECT id FROM nodes WHERE name = ?", (name,)).fetchone()
		parent = None if parent == "" else parent
		nodeMap[name] = Node(id, [], parent, 0, pSupport == 1)
	print(f"Result has {len(nodeMap)} nodes")
	print("Updating 'tips' values")
	updateTips(rootName, nodeMap)
	print("Creating table")
	addTreeTables(nodeMap, dbCur, "p")
def genImagesOnlyTree(dbCur, nodesWithImgOrPicked, pickedNames, rootName):
	print("Getting ancestors")
	nodeMap = genNodeMap(dbCur, nodesWithImgOrPicked, 1e4)
	print(f"Result has {len(nodeMap)} nodes")
	print("Removing composite nodes")
	removeCompositeNodes(nodeMap)
	print(f"Result has {len(nodeMap)} nodes")
	print("Removing 'collapsible' nodes")
	removeCollapsibleNodes(nodeMap, pickedNames)
	print(f"Result has {len(nodeMap)} nodes")
	print(f"Updating 'tips' values") # Needed for next trimming step
	updateTips(rootName, nodeMap)
	print(f"Trimming from nodes with 'many' children")
	trimIfManyChildren(nodeMap, rootName, 300, pickedNames)
	print(f"Result has {len(nodeMap)} nodes")
	print(f"Updating 'tips' values")
	updateTips(rootName, nodeMap)
	print("Creating table")
	addTreeTables(nodeMap, dbCur, "i")
def genWeaklyTrimmedTree(dbCur, nodesWithImgDescOrPicked, nodesWithImgOrPicked, rootName):
	print("Getting ancestors")
	nodeMap = genNodeMap(dbCur, nodesWithImgDescOrPicked, 1e5)
	print(f"Result has {len(nodeMap)} nodes")
	print("Getting nodes to 'strongly keep'")
	iterNum = 0
	nodesFromImgOrPicked = set()
	for name in nodesWithImgOrPicked:
		iterNum += 1
		if iterNum % 1e4 == 0:
			print(f"At iteration {iterNum}")
		#
		while name != None:
			if name not in nodesFromImgOrPicked:
				nodesFromImgOrPicked.add(name)
				name = nodeMap[name].parent
			else:
				break
	print(f"Node set has {len(nodesFromImgOrPicked)} nodes")
	print("Removing 'collapsible' nodes")
	removeCollapsibleNodes(nodeMap, nodesWithImgDescOrPicked)
	print(f"Result has {len(nodeMap)} nodes")
	print(f"Updating 'tips' values") # Needed for next trimming step
	updateTips(rootName, nodeMap)
	print(f"Trimming from nodes with 'many' children")
	trimIfManyChildren(nodeMap, rootName, 600, nodesFromImgOrPicked)
	print(f"Result has {len(nodeMap)} nodes")
	print(f"Updating 'tips' values")
	updateTips(rootName, nodeMap)
	print("Creating table")
	addTreeTables(nodeMap, dbCur, "t")
# Helper functions
def genNodeMap(dbCur, nameSet, itersBeforePrint = 1):
	" Returns a subtree that includes nodes in 'nameSet', as a name-to-Node map "
	nodeMap = {}
	iterNum = 0
	for name in nameSet:
		iterNum += 1
		if iterNum % itersBeforePrint == 0:
			print(f"At iteration {iterNum}")
		#
		prevName = None
		while name != None:
			if name not in nodeMap:
				# Add node
				(id, tips) = dbCur.execute("SELECT id, tips from nodes where name = ?", (name,)).fetchone()
				row = dbCur.execute("SELECT parent, p_support from edges where child = ?", (name,)).fetchone()
				parent = None if row == None or row[0] == "" else row[0]
				pSupport = row == None or row[1] == 1
				children = [] if prevName == None else [prevName]
				nodeMap[name] = Node(id, children, parent, 0, pSupport)
				# Iterate to parent
				prevName = name
				name = parent
			else:
				# Just add as child
				if prevName != None:
					nodeMap[name].children.append(prevName)
				break
	return nodeMap
def removeCompositeNodes(nodeMap):
	" Given a tree, removes composite-name nodes, and returns the removed nodes' names "
	global COMP_NAME_REGEX
	namesToRemove = set()
	for (name, node) in nodeMap.items():
		parent = node.parent
		if parent != None and COMP_NAME_REGEX.fullmatch(name) != None:
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
	return namesToRemove
def removeCollapsibleNodes(nodeMap, nodesToKeep = {}):
	""" Given a tree, removes single-child parents, then only-childs,
		with given exceptions, and returns the set of removed nodes' names """
	namesToRemove = set()
	# Remove single-child parents
	for (name, node) in nodeMap.items():
		if len(node.children) == 1 and node.parent != None and name not in nodesToKeep:
			# Connect parent and children
			parent = node.parent
			child = node.children[0]
			nodeMap[parent].children.remove(name)
			nodeMap[parent].children.append(child)
			nodeMap[child].parent = parent
			nodeMap[child].pSupport &= node.pSupport
			# Remember for removal
			namesToRemove.add(name)
	for name in namesToRemove:
		del nodeMap[name]
	# Remove only-childs (not redundant because 'nodesToKeep' can cause single-child parents to be kept)
	namesToRemove.clear()
	for (name, node) in nodeMap.items():
		isOnlyChild = node.parent != None and len(nodeMap[node.parent].children) == 1
		if isOnlyChild and name not in nodesToKeep:
			# Connect parent and children
			parent = node.parent
			nodeMap[parent].children = node.children
			for n in node.children:
				nodeMap[n].parent = parent
				nodeMap[n].pSupport &= node.pSupport
			# Remember for removal
			namesToRemove.add(name)
	for name in namesToRemove:
		del nodeMap[name]
	#
	return namesToRemove
def trimIfManyChildren(nodeMap, rootName, childThreshold, nodesToKeep = {}):
	namesToRemove = set()
	def findTrimmables(nodeName):
		nonlocal nodeMap, nodesToKeep
		node = nodeMap[nodeName]
		if len(node.children) > childThreshold:
			numToTrim = len(node.children) - childThreshold
			# Try removing nodes, preferring those with less tips
			candidatesToTrim = [n for n in node.children if n not in nodesToKeep]
			childToTips = {n: nodeMap[n].tips for n in candidatesToTrim}
			candidatesToTrim.sort(key=lambda n: childToTips[n], reverse=True)
			childrenToRemove = set(candidatesToTrim[-numToTrim:])
			node.children = [n for n in node.children if n not in childrenToRemove]
			# Mark nodes for deletion
			for n in childrenToRemove:
				markForRemoval(n)
		# Recurse on children
		for n in node.children:
			findTrimmables(n)
	def markForRemoval(nodeName):
		nonlocal nodeMap, namesToRemove
		namesToRemove.add(nodeName)
		for child in nodeMap[nodeName].children:
			markForRemoval(child)
	findTrimmables(rootName)
	for nodeName in namesToRemove:
		del nodeMap[nodeName]
def updateTips(nodeName, nodeMap):
	" Updates the 'tips' values for a node and it's descendants, returning the node's new 'tips' value "
	node = nodeMap[nodeName]
	tips = sum([updateTips(childName, nodeMap) for childName in node.children])
	tips = max(1, tips)
	node.tips = tips
	return tips
def addTreeTables(nodeMap, dbCur, suffix):
	" Adds a tree to the database, as tables nodes_X and edges_X, where X is the given suffix "
	nodesTbl = f"nodes_{suffix}"
	edgesTbl = f"edges_{suffix}"
	dbCur.execute(f"CREATE TABLE {nodesTbl} (name TEXT PRIMARY KEY, id TEXT UNIQUE, tips INT)")
	dbCur.execute(f"CREATE INDEX {nodesTbl}_idx_nc ON {nodesTbl}(name COLLATE NOCASE)")
	dbCur.execute(f"CREATE TABLE {edgesTbl} (parent TEXT, child TEXT, p_support INT, PRIMARY KEY (parent, child))")
	dbCur.execute(f"CREATE INDEX {edgesTbl}_child_idx ON {edgesTbl}(child)")
	for (name, node) in nodeMap.items():
		dbCur.execute(f"INSERT INTO {nodesTbl} VALUES (?, ?, ?)", (name, node.id, node.tips))
		for childName in node.children:
			pSupport = 1 if nodeMap[childName].pSupport else 0
			dbCur.execute(f"INSERT INTO {edgesTbl} VALUES (?, ?, ?)", (name, childName, pSupport))

print(f"Finding root node")
query = "SELECT name FROM nodes LEFT JOIN edges ON nodes.name = edges.child WHERE edges.parent IS NULL LIMIT 1"
(rootName,) = dbCur.execute(query).fetchone()
print(f"Found \"{rootName}\"")

print('=== Getting picked-nodes ===')
pickedNames = set()
pickedTreeExists = False
if dbCur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='nodes_p'").fetchone() == None:
	print(f"Reading from {pickedNodesFile}")
	with open(pickedNodesFile) as file:
		for line in file:
			name = line.rstrip()
			row = dbCur.execute("SELECT name from nodes WHERE name = ?", (name,)).fetchone()
			if row == None:
				row = dbCur.execute("SELECT name from names WHERE alt_name = ?", (name,)).fetchone()
			if row != None:
				pickedNames.add(row[0])
	if len(pickedNames) == 0:
		raise Exception("ERROR: No picked names found")
else:
	pickedTreeExists = True
	print("Picked-node tree already exists")
	if tree == 'picked':
		sys.exit()
	for (name,) in dbCur.execute("SELECT name FROM nodes_p"):
		pickedNames.add(name)
print(f"Found {len(pickedNames)} names")

if (tree == 'picked' or tree == None) and not pickedTreeExists:
	print("=== Generating picked-nodes tree ===")
	genPickedNodeTree(dbCur, pickedNames, rootName)
if tree != 'picked':
	print("=== Finding 'non-low significance' nodes ===")
	nodesWithImgOrPicked = set()
	nodesWithImgDescOrPicked = set()
	print("Finding nodes with descs")
	for (name,) in dbCur.execute("SELECT name FROM wiki_ids"): # Can assume the wiki_id has a desc
		nodesWithImgDescOrPicked.add(name)
	print("Finding nodes with images")
	for (name,) in dbCur.execute("SELECT name FROM node_imgs"):
		nodesWithImgDescOrPicked.add(name)
		nodesWithImgOrPicked.add(name)
	print("Adding picked nodes")
	for name in pickedNames:
		nodesWithImgDescOrPicked.add(name)
		nodesWithImgOrPicked.add(name)
	if tree == 'images' or tree == None:
		print("=== Generating images-only tree ===")
		genImagesOnlyTree(dbCur, nodesWithImgOrPicked, pickedNames, rootName)
	if tree == 'trimmed' or tree == None:
		print("=== Generating weakly-trimmed tree ===")
		genWeaklyTrimmedTree(dbCur, nodesWithImgDescOrPicked, nodesWithImgOrPicked, rootName)

print("Closing database")
dbCon.commit()
dbCon.close()
