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
			print("Iteration {}".format(iterNum))
		#
		row = dbCur.execute("SELECT name, alt_name from names WHERE alt_name = ?", (line.rstrip(),)).fetchone()
		if row != None:
			minimalNames.add(row[0])
if len(minimalNames) == 0:
	print("ERROR: No names found", file=sys.stderr)
	sys.exit(1)
print("Name set has {} names".format(len(minimalNames)))
# Add nodes that connect up to root
print("Getting connected nodes set")
iterNum = 0
rootName = None
for name in minimalNames:
	iterNum += 1
	if iterNum % 100 == 0:
		print("Iteration {}".format(iterNum))
	#
	prevName = None
	while name != None:
		if name not in nodeMap:
			(parent, tips, p_support) = dbCur.execute(
				"SELECT parent, tips, p_support from nodes WHERE name = ?", (name,)).fetchone()
			parent = None if parent == "" else parent
			nodeMap[name] = {
				"children": [] if prevName == None else [prevName],
				"parent": parent,
				"tips": 0,
				"pSupport": p_support == 1,
			}
			prevName = name
			name = parent
		else:
			if prevName != None:
				nodeMap[name]["children"].append(prevName)
			break
	if name == None:
		rootName = prevName
print("New node set has {} nodes".format(len(nodeMap)))
# Remove certain 'chain collapsible' nodes
print("Removing 'chain collapsible' nodes")
namesToRemove = set()
for (name, nodeObj) in nodeMap.items():
	if name not in minimalNames and len(nodeObj["children"]) == 1:
		parentName = nodeObj["parent"]
		childName = nodeObj["children"][0]
		# Connect parent and child
		nodeMap[parentName]["children"].remove(name)
		nodeMap[parentName]["children"].append(childName)
		nodeMap[childName]["parent"] = parentName
		# Adjust child pSupport
		nodeMap[childName]["pSupport"] &= nodeObj["pSupport"]
		# Remember for removal
		namesToRemove.add(name)
for name in namesToRemove:
	del nodeMap[name]
print("New node set has {} nodes".format(len(nodeMap)))
# Merge-upward compsite-named nodes
print("Merging-upward composite-named nodes")
namesToRemove2 = set()
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
		namesToRemove2.add(name)
for name in namesToRemove2:
	del nodeMap[name]
	namesToRemove.add(name)
print("New node set has {} nodes".format(len(nodeMap)))
# Add some connected children
print("Adding additional nearby children")
namesToAdd = []
iterNum = 0
for (name, nodeObj) in nodeMap.items():
	iterNum += 1
	if iterNum % 100 == 0:
		print("Iteration {}".format(iterNum))
	#
	numChildren = len(nodeObj["children"])
	if numChildren < PREF_NUM_CHILDREN:
		row = dbCur.execute("SELECT children from nodes WHERE name = ?", (name,)).fetchone()
		newChildren = [n for n in json.loads(row[0]) if
			not (n in nodeMap or n in namesToRemove) and
			compNameRegex.fullmatch(n) == None]
		newChildNames = newChildren[:max(0, PREF_NUM_CHILDREN - numChildren)]
		nodeObj["children"].extend(newChildNames)
		namesToAdd.extend(newChildNames)
for name in namesToAdd:
	(parent, pSupport) = dbCur.execute("SELECT parent, p_support from nodes WHERE name = ?", (name,)).fetchone()
	nodeMap[name] = {
		"children": [],
		"parent": parent,
		"tips": 0,
		"pSupport": pSupport,
	}
print("New node set has {} nodes".format(len(nodeMap)))
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
dbCur.execute(
	"CREATE TABLE reduced_nodes (name TEXT PRIMARY KEY, children TEXT, parent TEXT, tips INT, p_support INT)")
for (name, nodeObj) in nodeMap.items():
	parentName = "" if nodeObj["parent"] == None else nodeObj["parent"]
	dbCur.execute("INSERT INTO reduced_nodes VALUES (?, ?, ?, ?, ?)",
		(name, json.dumps(nodeObj["children"]), parentName, nodeObj["tips"], 1 if nodeObj["pSupport"] else 0))
# Close db
dbCon.commit()
dbCon.close()
