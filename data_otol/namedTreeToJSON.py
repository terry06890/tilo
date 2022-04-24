#!/usr/bin/python3

import sys, re, json

usageInfo =  f"usage: {sys.argv[0]}\n"
usageInfo += "Reads labelled_supertree_ottnames.tre & annotations.json (from an Open Tree of Life release), \n"
usageInfo += "and prints a JSON object, which maps node names to objects of the form \n"
usageInfo += "{\"children\": [name1, ...], \"parent\": name1, \"tips\": int1, \"pSupport\": bool1}, which holds \n"
usageInfo += "child names, a parent name or null, descendant 'tips', and a phylogeny-support indicator\n"
usageInfo += "\n"
usageInfo += "This script was adapted to handle Open Tree of Life version 13.4.\n"
usageInfo += "Link: https://tree.opentreeoflife.org/about/synthesis-release/v13.4\n"
usageInfo += "\n"
usageInfo += "labelled_supertree_ottnames.tre format:\n"
usageInfo += "    Represents a tree-of-life in Newick format, roughly like (n1,n2,(n3,n4)n5)n6,\n"
usageInfo += "    where root node is named n6, and has children n1, n2, and n5.\n"
usageInfo += "    Name forms include Homo_sapiens_ott770315, mrcaott6ott22687, and 'Oxalis san-miguelii ott5748753'\n"
usageInfo += "    Some names can be split up into a 'simple' name (like Homo_sapiens) and an id (like ott770315)\n"
usageInfo += "annotations.json format:\n"
usageInfo += "    JSON object holding information about the tree-of-life release.\n"
usageInfo += "    The object's 'nodes' field maps node IDs to objects holding information about that node,\n"
usageInfo += "    such as phylogenetic trees that support/conflict with it's placement.\n"

if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

nodeMap = {} # The JSON object to output
idToName = {} # Maps node IDs to names

# Parse labelled_supertree_ottnames.tre
data = None
with open("labelled_supertree_ottnames.tre") as file:
	data = file.read()
dataIdx = 0
def parseNewick():
	"""Parses a node using 'data' and 'dataIdx', updates nodeMap accordingly, and returns the node name or None"""
	global dataIdx
	# Check for EOF
	if dataIdx == len(data):
		print("ERROR: Unexpected EOF at index " + str(dataIdx), file=sys.stderr)
		return None
	# Check for inner-node start
	if data[dataIdx] == "(":
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
				nodeMap[name] = {
					"n": name, "id": id, "children": childNames, "parent": None, "tips": tips, "pSupport": False
				}
				# Update childrens' parent reference
				for childName in childNames:
					nodeMap[childName]["parent"] = name
				return name
	else:
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

# Parse annotations.json
data = None
with open("annotations.json") as file:
	data = file.read()
obj = json.loads(data)
nodeAnnsMap = obj['nodes']

# Do some more postprocessing on each node
def convertMrcaName(name):
	"""Given an mrca* name, returns an expanded version with the form [name1 + name2]"""
	match = re.fullmatch(r"mrca(ott\d+)(ott\d+)", name)
	if match == None:
		print("ERROR: Invalid name \"{}\"".format(name), file=sys.stderr)
	else:
		subName1 = match.group(1)
		subName2 = match.group(2)
		if subName1 not in idToName:
			print("ERROR: MRCA name \"{}\" sub-name \"{}\" not found".format(subName1), file=sys.stderr)
		elif subName2 not in idToName:
			print("ERROR: MRCA name \"{}\" sub-name \"{}\" not found".format(subName2), file=sys.stderr)
		else:
			return "[{} + {}]".format(idToName[subName1], idToName[subName2])
namesToSwap = [] # Will hold [oldName, newName] pairs, for renaming nodes in nodeMap
for node in nodeMap.values():
	# Set has-support value using annotations
	id = node["id"]
	if id in nodeAnnsMap:
		nodeAnns = nodeAnnsMap[id]
		supportQty = len(nodeAnns["supported_by"]) if "supported_by" in nodeAnns else 0
		conflictQty = len(nodeAnns["conflicts_with"]) if "conflicts_with" in nodeAnns else 0
		node["pSupport"] = supportQty > 0 and conflictQty == 0
	# Change mrca* names
	name = node["n"]
	if (name.startswith("mrca")):
		namesToSwap.append([name, convertMrcaName(name)])
	parentName = node["parent"]
	if (parentName != None and parentName.startswith("mrca")):
		node["parent"] = convertMrcaName(parentName)
	childNames = node["children"]
	for i in range(len(childNames)):
		if (childNames[i].startswith("mrca")):
			childNames[i] = convertMrcaName(childNames[i])
	# Delete some no-longer-needed fields
	del node["n"]
	del node["id"]
# Finish mrca* renamings
for [oldName, newName] in namesToSwap:
	nodeMap[newName] = nodeMap[oldName]
	del nodeMap[oldName]

# Output JSON
print(json.dumps(nodeMap))
