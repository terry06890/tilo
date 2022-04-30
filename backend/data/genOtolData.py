#!/usr/bin/python3

import sys, re, json, sqlite3
import os.path

usageInfo =  f"usage: {sys.argv[0]}\n"
usageInfo += "Reads labelled_supertree_ottnames.tre & annotations.json (from an Open Tree of Life release), \n"
usageInfo += "and creates a sqlite database, which holds entries of the form (name text, data text).\n"
usageInfo += "Each row holds a tree-of-life node name, and a JSON string with the form \n"
usageInfo += "{\"children\": [name1, ...], \"parent\": name1, \"tips\": int1, \"pSupport\": bool1}, holding \n"
usageInfo += "child names, a parent name or null, descendant 'tips', and a phylogeny-support indicator\n"
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

if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

treeFile = "otol/labelled_supertree_ottnames.tre"
annFile = "otol/annotations.json"
dbFile = "data.db"
nodeMap = {} # Maps node names to node objects
idToName = {} # Maps node IDs to names

# Check for existing db
if os.path.exists(dbFile):
	print("ERROR: Existing {} db".format(dbFile), file=sys.stderr)
	sys.exit(1)

# Parse treeFile
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
		childNames = []
		while True:
			# Read child
			childName = parseNewick()
			if childName == None:
				return None
			childNames.append(childName)
			if (dataIdx == len(data)):
				print("ERROR: Unexpected EOF", file=sys.stderr)
				return None
			# Check for next child
			if (data[dataIdx] == ","):
				dataIdx += 1
				continue
			else:
				# Get node name
				dataIdx += 1 # Consume an expected ')'
				[name, id] = parseNewickName()
				idToName[id] = name
				# Get child num-tips total
				tips = 0
				for childName in childNames:
					tips += nodeMap[childName]["tips"]
				# Add node to nodeMap
				if name in nodeMap: # Turns out the names might not actually be unique
					count = 2
					name2 = name + " [" + str(count) + "]"
					while name2 in nodeMap:
						count += 1
						name2 = name + " [" + str(count) + "]"
					name = name2
				nodeMap[name] = {
					"n": name, "id": id, "children": childNames, "parent": None, "tips": tips, "pSupport": False
				}
				# Update childrens' parent reference
				for childName in childNames:
					nodeMap[childName]["parent"] = name
				return name
	else: # Parse node name
		[name, id] = parseNewickName()
		idToName[id] = name
		nodeMap[name] = {"n": name, "id": id, "children": [], "parent": None, "tips": 1, "pSupport": False}
		return name
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
			raise Exception("ERROR: invalid name \"{}\"".format(name))
		name = match.group(1).replace("''", "'")
		return [name, match.group(2)]
	else:
		match = re.fullmatch(r"([^\\\"]+)_(ott\d+)", name)
		if match == None:
			raise Exception("ERROR: invalid name \"{}\"".format(name))
		return [match.group(1).replace("_", " "), match.group(2)]
rootName = parseNewick()

# Parse annFile
data = None
with open(annFile) as file:
	data = file.read()
obj = json.loads(data)
nodeAnnsMap = obj['nodes']

# Change mrca* names
def applyMrcaNameConvert(name, namesToSwap):
	"""
	Given an mrca* name, makes namesToSwap map it to an expanded version with the form [childName1 + childName2].
	May recurse on child nodes with mrca* names.
	Also returns the name of the highest-tips child (used when recursing).
	"""
	node = nodeMap[name]
	childNames = node["children"]
	if len(childNames) < 2:
		print("WARNING: MRCA node \"{}\" has less than 2 children".format(name), file=sys.stderr)
		return name
	# Get 2 children with most tips
	childTips = []
	for n in childNames:
		childTips.append(nodeMap[n]["tips"])
	maxTips = max(childTips)
	maxIdx = childTips.index(maxTips)
	childTips[maxIdx] = 0
	maxTips2 = max(childTips)
	maxIdx2 = childTips.index(maxTips2)
	childName1 = node["children"][maxIdx]
	childName2 = node["children"][maxIdx2]
	# Check for composite child names
	if childName1.startswith("mrca"):
		childName1 = applyMrcaNameConvert(childName1, namesToSwap)
	if childName2.startswith("mrca"):
		childName2 = applyMrcaNameConvert(childName2, namesToSwap)
	# Create composite name
	namesToSwap[name] = "[{} + {}]".format(childName1, childName2)
	return childName1
namesToSwap = {} # Maps mrca* names to replacement names
for node in nodeMap.values():
	name = node["n"]
	if (name.startswith("mrca") and name not in namesToSwap):
		applyMrcaNameConvert(name, namesToSwap)
for [oldName, newName] in namesToSwap.items():
	nodeMap[newName] = nodeMap[oldName]
	del nodeMap[oldName]
for node in nodeMap.values():
	parentName = node["parent"]
	if (parentName in namesToSwap):
		node["parent"] = namesToSwap[parentName]
	childNames = node["children"]
	for i in range(len(childNames)):
		childName = childNames[i]
		if (childName in namesToSwap):
			childNames[i] = namesToSwap[childName]

# Add annotations data, and delete certain fields
for node in nodeMap.values():
	# Set has-support value using annotations
	id = node["id"]
	if id in nodeAnnsMap:
		nodeAnns = nodeAnnsMap[id]
		supportQty = len(nodeAnns["supported_by"]) if "supported_by" in nodeAnns else 0
		conflictQty = len(nodeAnns["conflicts_with"]) if "conflicts_with" in nodeAnns else 0
		node["pSupport"] = supportQty > 0 and conflictQty == 0
	# Root node gets support
	if node["parent"] == None:
		node["pSupport"] = True
	# Delete some no-longer-needed fields
	del node["n"]
	del node["id"]

# Create db
dbCon = sqlite3.connect(dbFile)
dbCur = dbCon.cursor()
dbCur.execute("CREATE TABLE nodes (name TEXT PRIMARY KEY, data TEXT)")
for name in nodeMap.keys():
	dbCur.execute("INSERT INTO nodes VALUES (?, ?)", (name, json.dumps(nodeMap[name])))
dbCon.commit()
dbCon.close()
