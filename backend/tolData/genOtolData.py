#!/usr/bin/python3

import sys, re, os
import json, sqlite3

usageInfo = f"""
Usage: {sys.argv[0]}

Reads files describing a tree-of-life from an 'Open Tree of Life' release,
and stores tree information in a database.

Reads a labelled_supertree_ottnames.tre file, which is assumed to have this format:
    The tree-of-life is represented in Newick format, which looks like: (n1,n2,(n3,n4)n5)n6
		The root node is named n6, and has children n1, n2, and n5.
    Name examples include: Homo_sapiens_ott770315, mrcaott6ott22687, 'Oxalis san-miguelii ott5748753', 
		'ott770315' and 'mrcaott6ott22687' are node IDs. The latter is for a 'compound node'.
		The node with ID 'ott770315' will get the name 'homo sapiens'.
		A compound node will get a name composed from it's sub-nodes (eg: [name1 + name2]).
	It is possible for multiple nodes to have the same name.
		In these cases, extra nodes will be named sequentially, as 'name1 [2]', 'name1 [3]', etc.
Reads an annotations.json file, which is assumed to have this format:
    Holds a JSON object, whose 'nodes' property maps node IDs to objects holding information about that node,
    such as the properties 'supported_by' and 'conflicts_with', which list phylogenetic trees that
	support/conflict with the node's placement.
Reads from a picked-names file, if present, which specifies name and node ID pairs.
	These help resolve cases where multiple nodes share the same name.
"""
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

treeFile = "otol/labelled_supertree_ottnames.tre" # Had about 2.5e9 nodes
annFile = "otol/annotations.json"
dbFile = "data.db"
nodeMap = {} # Maps node IDs to node objects
nameToFirstId = {} # Maps node names to first found ID (names might have multiple IDs)
dupNameToIds = {} # Maps names of nodes with multiple IDs to those IDs
pickedNamesFile = "pickedOtolNames.txt"

class Node:
	" Represents a tree-of-life node "
	def __init__(self, name, childIds, parentId, tips, pSupport):
		self.name = name
		self.childIds = childIds
		self.parentId = parentId
		self.tips = tips
		self.pSupport = pSupport

print("Parsing tree file")
# Read file
data = None
with open(treeFile) as file:
	data = file.read()
dataIdx = 0
# Parse content
iterNum = 0
def parseNewick():
	" Parses a node using 'data' and 'dataIdx', updates nodeMap accordingly, and returns the node's ID "
	global data, dataIdx, iterNum
	iterNum += 1
	if iterNum % 1e5 == 0:
		print(f"At iteration {iterNum}")
	# Check for EOF
	if dataIdx == len(data):
		raise Exception(f"ERROR: Unexpected EOF at index {dataIdx}")
	# Check for node
	if data[dataIdx] == "(": # parse inner node
		dataIdx += 1
		childIds = []
		while True:
			# Read child
			childId = parseNewick()
			childIds.append(childId)
			if (dataIdx == len(data)):
				raise Exception(f"ERROR: Unexpected EOF at index {dataIdx}")
			# Check for next child
			if (data[dataIdx] == ","):
				dataIdx += 1
				continue
			else:
				# Get node name and id
				dataIdx += 1 # Consume an expected ')'
				name, id = parseNewickName()
				updateNameMaps(name, id)
				# Get child num-tips total
				tips = 0
				for childId in childIds:
					tips += nodeMap[childId].tips
				# Add node to nodeMap
				nodeMap[id] = Node(name, childIds, None, tips, False)
				# Update childrens' parent reference
				for childId in childIds:
					nodeMap[childId].parentId = id
				return id
	else: # Parse node name
		name, id = parseNewickName()
		updateNameMaps(name, id)
		nodeMap[id] = Node(name, [], None, 1, False)
		return id
def parseNewickName():
	" Parses a node name using 'data' and 'dataIdx', and returns a (name, id) pair "
	global data, dataIdx
	name = None
	end = dataIdx
	# Get name
	if (end < len(data) and data[end] == "'"): # Check for quoted name
		end += 1
		inQuote = True
		while end < len(data):
			if (data[end] == "'"):
				if end + 1 < len(data) and data[end + 1] == "'": # Account for '' as escaped-quote
					end += 2
					continue
				else:
					end += 1
					inQuote = False
					break
			end += 1
		if inQuote:
			raise Exception(f"ERROR: Unexpected EOF at index {dataIdx}")
		name = data[dataIdx:end]
		dataIdx = end
	else:
		while end < len(data) and not re.match(r"[(),]", data[end]):
			end += 1
		if (end == dataIdx):
			raise Exception(f"ERROR: Unexpected EOF at index {dataIdx}")
		name = data[dataIdx:end].rstrip()
		if end == len(data): # Ignore trailing input semicolon
			name = name[:-1]
		dataIdx = end
	# Convert to (name, id)
	name = name.lower()
	if name.startswith("mrca"):
		return (name, name)
	elif name[0] == "'":
		match = re.fullmatch(r"'([^\\\"]+) (ott\d+)'", name)
		if match == None:
			raise Exception(f"ERROR: invalid name \"{name}\"")
		name = match.group(1).replace("''", "'")
		return (name, match.group(2))
	else:
		match = re.fullmatch(r"([^\\\"]+)_(ott\d+)", name)
		if match == None:
			raise Exception(f"ERROR: invalid name \"{name}\"")
		return (match.group(1).replace("_", " "), match.group(2))
def updateNameMaps(name, id):
	global nameToFirstId, dupNameToIds
	if name not in nameToFirstId:
		nameToFirstId[name] = id
	else:
		if name not in dupNameToIds:
			dupNameToIds[name] = [nameToFirstId[name], id]
		else:
			dupNameToIds[name].append(id)
rootId = parseNewick()

print("Resolving duplicate names")
# Read picked-names file
nameToPickedId = {}
if os.path.exists(pickedNamesFile):
	with open(pickedNamesFile) as file:
		for line in file:
			(name, _, otolId) = line.rstrip().partition("|")
			nameToPickedId[name] = otolId
# Resolve duplicates
for (dupName, ids) in dupNameToIds.items():
	# Check for picked id
	if dupName in nameToPickedId:
		idToUse = nameToPickedId[dupName]
	else:
		# Get conflicting node with most tips
		tipNums = [nodeMap[id].tips for id in ids]
		maxIdx = tipNums.index(max(tipNums))
		idToUse = ids[maxIdx]
	# Adjust name of other conflicting nodes
	counter = 2
	for id in ids:
		if id != idToUse:
			nodeMap[id].name += f" [{counter}]"
			counter += 1

print("Changing mrca* names")
def convertMrcaName(id):
	node = nodeMap[id]
	name = node.name
	childIds = node.childIds
	if len(childIds) < 2:
		print(f"WARNING: MRCA node \"{name}\" has less than 2 children")
		return
	# Get 2 children with most tips
	childTips = [nodeMap[id].tips for id in childIds]
	maxIdx1 = childTips.index(max(childTips))
	childTips[maxIdx1] = 0
	maxIdx2 = childTips.index(max(childTips))
	childId1 = childIds[maxIdx1]
	childId2 = childIds[maxIdx2]
	childName1 = nodeMap[childId1].name
	childName2 = nodeMap[childId2].name
	# Check for mrca* child names
	if childName1.startswith("mrca"):
		childName1 = convertMrcaName(childId1)
	if childName2.startswith("mrca"):
		childName2 = convertMrcaName(childId2)
	# Check for composite names
	match = re.fullmatch(r"\[(.+) \+ (.+)]", childName1)
	if match != None:
		childName1 = match.group(1)
	match = re.fullmatch(r"\[(.+) \+ (.+)]", childName2)
	if match != None:
		childName2 = match.group(1)
	# Create composite name
	node.name = f"[{childName1} + {childName2}]"
	return childName1
for (id, node) in nodeMap.items():
	if node.name.startswith("mrca"):
		convertMrcaName(id)

print("Parsing annotations file")
# Read file
data = None
with open(annFile) as file:
	data = file.read()
obj = json.loads(data)
nodeAnnsMap = obj["nodes"]
# Find relevant annotations
for (id, node) in nodeMap.items():
	# Set has-support value using annotations
	if id in nodeAnnsMap:
		nodeAnns = nodeAnnsMap[id]
		supportQty = len(nodeAnns["supported_by"]) if "supported_by" in nodeAnns else 0
		conflictQty = len(nodeAnns["conflicts_with"]) if "conflicts_with" in nodeAnns else 0
		node.pSupport = supportQty > 0 and conflictQty == 0

print("Creating nodes and edges tables")
dbCon = sqlite3.connect(dbFile)
dbCur = dbCon.cursor()
dbCur.execute("CREATE TABLE nodes (name TEXT PRIMARY KEY, id TEXT UNIQUE, tips INT)")
dbCur.execute("CREATE INDEX nodes_idx_nc ON nodes(name COLLATE NOCASE)")
dbCur.execute("CREATE TABLE edges (parent TEXT, child TEXT, p_support INT, PRIMARY KEY (parent, child))")
dbCur.execute("CREATE INDEX edges_child_idx ON edges(child)")
for (otolId, node) in nodeMap.items():
	dbCur.execute("INSERT INTO nodes VALUES (?, ?, ?)", (node.name, otolId, node.tips))
	for childId in node.childIds:
		childNode = nodeMap[childId]
		dbCur.execute("INSERT INTO edges VALUES (?, ?, ?)",
			(node.name, childNode.name, 1 if childNode.pSupport else 0))
print("Closing database")
dbCon.commit()
dbCon.close()
