#!/usr/bin/python3

import sys, re, os
import json, sqlite3

usageInfo =  f"usage: {sys.argv[0]}\n"
usageInfo += "Reads labelled_supertree_ottnames.tre & annotations.json (from an Open Tree of Life release),\n"
usageInfo += "and creates a sqlite database, which holds entries of the form (name text, data text).\n"
usageInfo += "Each row holds a tree-of-life node's name, JSON-encoded child name array, a parent name or '',\n"
usageInfo += "number of descendant 'tips', and a 1 or 0 indicating phylogenetic-support.\n"
usageInfo += "\n"
usageInfo += "Expected labelled_supertree_ottnames.tre format:\n"
usageInfo += "    Represents a tree-of-life in Newick format, roughly like (n1,n2,(n3,n4)n5)n6,\n"
usageInfo += "    where root node is named n6, and has children n1, n2, and n5.\n"
usageInfo += "    Name forms include Homo_sapiens_ott770315, mrcaott6ott22687, and 'Oxalis san-miguelii ott5748753'\n"
usageInfo += "    Some names can be split up into a 'simple' name (like Homo_sapiens) and an id (like ott770315)\n"
usageInfo += "Expected annotations.json format:\n"
usageInfo += "    JSON object holding information about the tree-of-life release.\n"
usageInfo += "    The object's 'nodes' field maps node IDs to objects holding information about that node,\n"
usageInfo += "    such as phylogenetic trees that support/conflict with it's placement.\n"
usageInfo += "\n"
usageInfo += "Some node trimming is done on the extracted tree, for performance and relevance reasons.\n"
usageInfo += "The app can get quite laggy when some nodes in the chain have over 10k children.\n"
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

treeFile = "otol/labelled_supertree_ottnames.tre"
annFile = "otol/annotations.json"
dbFile = "data.db"
nodeMap = {} # Maps node IDs to node objects
nameToFirstId = {} # Maps node names to first found ID (names might have multiple IDs)
dupNameToIds = {} # Maps names of nodes with multiple IDs to those IDs
pickedNamesFile = "pickedOtolNames.txt"

# Parse treeFile
print("Parsing tree file")
data = None
with open(treeFile) as file:
	data = file.read()
dataIdx = 0
def parseNewick():
	"""Parses a node using 'data' and 'dataIdx', updates nodeMap accordingly, and returns the node name or None"""
	global dataIdx
	# Check for EOF
	if dataIdx == len(data):
		print("ERROR: Unexpected EOF at index " + str(dataIdx), file=sys.stderr)
		return None
	# Check for node
	if data[dataIdx] == "(": # parse inner node
		dataIdx += 1
		childIds = []
		while True:
			# Read child
			childId = parseNewick()
			if childId == None:
				return None
			childIds.append(childId)
			if (dataIdx == len(data)):
				print("ERROR: Unexpected EOF", file=sys.stderr)
				return None
			# Check for next child
			if (data[dataIdx] == ","):
				dataIdx += 1
				continue
			else:
				# Get node name and id
				dataIdx += 1 # Consume an expected ')'
				[name, id] = parseNewickName()
				updateNameMaps(name, id)
				# Get child num-tips total
				tips = 0
				for childId in childIds:
					tips += nodeMap[childId]["tips"]
				# Add node to nodeMap
				nodeMap[id] = {"name": name, "children": childIds, "parent": None, "tips": tips, "pSupport": False}
				# Update childrens' parent reference
				for childId in childIds:
					nodeMap[childId]["parent"] = id
				return id
	else: # Parse node name
		[name, id] = parseNewickName()
		updateNameMaps(name, id)
		nodeMap[id] = {"name": name, "children": [], "parent": None, "tips": 1, "pSupport": False}
		return id
def updateNameMaps(name, id):
	if name not in nameToFirstId:
		nameToFirstId[name] = id
	else:
		if name not in dupNameToIds:
			dupNameToIds[name] = [nameToFirstId[name], id]
		else:
			dupNameToIds[name].append(id)
def parseNewickName():
	"""Helper that parses an input node name, and returns a [name,id] pair"""
	global data, dataIdx
	name = None
	end = dataIdx
	# Get name
	if (end < len(data) and data[end] == "'"): # Check for quoted name
		end += 1
		inQuote = True
		while end < len(data):
			if (data[end] == "'"):
				if end + 1 < len(data) and data[end+1] == "'": # Account for '' as escaped-quote
					end += 2
					continue
				else:
					end += 1
					inQuote = False
					break
			end += 1
		if inQuote:
			raise Exception("ERROR: Unexpected EOF")
		name = data[dataIdx:end]
		dataIdx = end
	else:
		while end < len(data) and not re.match(r"[(),]", data[end]):
			end += 1
		if (end == dataIdx):
			raise Exception("ERROR: Unexpected EOF")
		name = data[dataIdx:end].rstrip()
		if end == len(data): # Ignore trailing input semicolon
			name = name[:-1]
		dataIdx = end
	# Convert to [name, id]
	name = name.lower()
	if name.startswith("mrca"):
		return [name, name]
	elif name[0] == "'":
		match = re.fullmatch(r"'([^\\\"]+) (ott\d+)'", name)
		if match == None:
			raise Exception(f"ERROR: invalid name \"{name}\"")
		name = match.group(1).replace("''", "'")
		return [name, match.group(2)]
	else:
		match = re.fullmatch(r"([^\\\"]+)_(ott\d+)", name)
		if match == None:
			raise Exception(f"ERROR: invalid name \"{name}\"")
		return [match.group(1).replace("_", " "), match.group(2)]
rootId = parseNewick()
# Resolve duplicate names
print("Resolving duplicates")
nameToPickedId = {}
if os.path.exists(pickedNamesFile):
	with open(pickedNamesFile) as file:
		for line in file:
			(name, _, otolId) = line.rstrip().partition("|")
			nameToPickedId[name] = otolId
for [dupName, ids] in dupNameToIds.items():
	# Check for picked id
	if dupName in nameToPickedId:
		idToUse = nameToPickedId[dupName]
	else:
		# Get conflicting node with most tips
		tipNums = [nodeMap[id]["tips"] for id in ids]
		maxIdx = tipNums.index(max(tipNums))
		idToUse = ids[maxIdx]
	# Adjust name of other conflicting nodes
	counter = 2
	for id in ids:
		if id != idToUse:
			nodeMap[id]["name"] += " [" + str(counter)+ "]"
			counter += 1
# Change mrca* names
print("Changing mrca* names")
def convertMrcaName(id):
	node = nodeMap[id]
	name = node["name"]
	childIds = node["children"]
	if len(childIds) < 2:
		print(f"WARNING: MRCA node \"{name}\" has less than 2 children", file=sys.stderr)
		return
	# Get 2 children with most tips
	childTips = [nodeMap[id]["tips"] for id in childIds]
	maxIdx = childTips.index(max(childTips))
	childTips[maxIdx] = 0
	maxIdx2 = childTips.index(max(childTips))
	childId1 = childIds[maxIdx]
	childId2 = childIds[maxIdx2]
	childName1 = nodeMap[childId1]["name"]
	childName2 = nodeMap[childId2]["name"]
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
	node["name"] = f"[{childName1} + {childName2}]"
	return childName1
for [id, node] in nodeMap.items():
	if node["name"].startswith("mrca"):
		convertMrcaName(id)
# Parse annFile
print("Parsing annotations file")
data = None
with open(annFile) as file:
	data = file.read()
obj = json.loads(data)
nodeAnnsMap = obj['nodes']
# Add annotations data
print("Adding annotation data")
for [id, node] in nodeMap.items():
	# Set has-support value using annotations
	if id in nodeAnnsMap:
		nodeAnns = nodeAnnsMap[id]
		supportQty = len(nodeAnns["supported_by"]) if "supported_by" in nodeAnns else 0
		conflictQty = len(nodeAnns["conflicts_with"]) if "conflicts_with" in nodeAnns else 0
		node["pSupport"] = supportQty > 0 and conflictQty == 0
	# Root node gets support
	if node["parent"] == None:
		node["pSupport"] = True
# Create db
print("Creating nodes and edges tables")
dbCon = sqlite3.connect(dbFile)
dbCur = dbCon.cursor()
dbCur.execute("CREATE TABLE nodes (name TEXT PRIMARY KEY, id TEXT UNIQUE, tips INT)")
dbCur.execute("CREATE INDEX nodes_idx_nc ON nodes(name COLLATE NOCASE)")
dbCur.execute("CREATE TABLE edges (node TEXT, child TEXT, p_support INT, PRIMARY KEY (node, child))")
dbCur.execute("CREATE INDEX edges_child_idx ON edges(child)")
for (otolId, node) in nodeMap.items():
	dbCur.execute("INSERT INTO nodes VALUES (?, ?, ?)", (node["name"], otolId, node["tips"]))
	childIds = node["children"]
	for childId in childIds:
		childNode = nodeMap[childId]
		dbCur.execute("INSERT INTO edges VALUES (?, ?, ?)",
			(node["name"], childNode["name"], 1 if childNode["pSupport"] else 0))
dbCon.commit()
dbCon.close()
