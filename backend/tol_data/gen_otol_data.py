#!/usr/bin/python3

"""
Reads files describing a tree-of-life from an 'Open Tree of Life' release,
and stores tree info in a database.

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

import re, os
import json, sqlite3

TREE_FILE = os.path.join('otol', 'labelled_supertree_ottnames.tre') # Had about 2.5e9 nodes
ANN_FILE = os.path.join('otol', 'annotations.json')
DB_FILE = 'data.db'
PICKED_NAMES_FILE = 'picked_otol_names.txt'

class Node:
	""" Represents a tree-of-life node """
	def __init__(self, name, childIds, parentId, tips, pSupport):
		self.name = name
		self.childIds = childIds
		self.parentId = parentId
		self.tips = tips
		self.pSupport = pSupport
class BasicStream:
	""" Represents a basic data stream, using a string and index. Used for parsing text with lookahead. """
	def __init__(self, data, idx=0):
		self.data = data
		self.idx = idx
	def hasNext(self) -> bool:
		return self.idx < len(self.data)
	def next(self) -> str:
		if self.hasNext():
			char = self.data[self.idx]
			self.idx += 1
			return char;
		else:
			return '';
	def peek(self) -> str:
		if self.hasNext():
			return self.data[self.idx]
		else:
			return '';
	def skipWhitespace(self) -> None:
		while self.hasNext() and self.data[self.idx].isspace():
			self.idx += 1
	def progress(self) -> float:
		return (self.idx / len(self.data))

def genData(treeFile: str, annFile: str, pickedNamesFile: str, dbFile: str) -> None:
	""" Reads the files and stores the tree info """
	nodeMap: dict[str, Node] = {} # Maps node IDs to node objects
	nameToFirstId: dict[str, str] = {} # Maps node names to first found ID (names might have multiple IDs)
	dupNameToIds: dict[str, list[str]] = {} # Maps names of nodes with multiple IDs to those IDs
	#
	print('Parsing tree file')
	treeStream: BasicStream
	with open(treeFile) as file:
		treeStream = BasicStream(file.read())
	# Parse content
	parseNewick(treeStream, nodeMap, nameToFirstId, dupNameToIds)
	print('Resolving duplicate names')
	# Read picked-names file
	nameToPickedId: dict[str, str] = {}
	if os.path.exists(pickedNamesFile):
		with open(pickedNamesFile) as file:
			for line in file:
				name, _, otolId = line.strip().partition('|')
				nameToPickedId[name] = otolId
	# Resolve duplicates
	for dupName, ids in dupNameToIds.items():
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
				nodeMap[id].name += f' [{counter}]'
				counter += 1
	print('Changing mrca* names')
	for id, node in nodeMap.items():
		if node.name.startswith('mrca'):
			convertMrcaName(id, nodeMap)
	print('Parsing annotations file')
	# Read file
	with open(annFile) as file:
		data = file.read()
	obj = json.loads(data)
	nodeAnnsMap = obj['nodes']
	# Find relevant annotations
	for id, node in nodeMap.items():
		# Set has-support value using annotations
		if id in nodeAnnsMap:
			nodeAnns = nodeAnnsMap[id]
			supportQty = len(nodeAnns['supported_by']) if 'supported_by' in nodeAnns else 0
			conflictQty = len(nodeAnns['conflicts_with']) if 'conflicts_with' in nodeAnns else 0
			node.pSupport = supportQty > 0 and conflictQty == 0
	print('Creating nodes and edges tables')
	dbCon = sqlite3.connect(dbFile)
	dbCur = dbCon.cursor()
	dbCur.execute('CREATE TABLE nodes (name TEXT PRIMARY KEY, id TEXT UNIQUE, tips INT)')
	dbCur.execute('CREATE INDEX nodes_idx_nc ON nodes(name COLLATE NOCASE)')
	dbCur.execute('CREATE TABLE edges (parent TEXT, child TEXT, p_support INT, PRIMARY KEY (parent, child))')
	dbCur.execute('CREATE INDEX edges_child_idx ON edges(child)')
	for otolId, node in nodeMap.items():
		dbCur.execute('INSERT INTO nodes VALUES (?, ?, ?)', (node.name, otolId, node.tips))
		for childId in node.childIds:
			childNode = nodeMap[childId]
			dbCur.execute('INSERT INTO edges VALUES (?, ?, ?)',
				(node.name, childNode.name, 1 if childNode.pSupport else 0))
	print('Closing database')
	dbCon.commit()
	dbCon.close()
def parseNewick(
		stream: BasicStream,
		nodeMap: dict[str, Node],
		nameToFirstId: dict[str, str],
		dupNameToIds: dict[str, list[str]]) -> str:
	""" Parses a node using 'data' and 'dataIdx', updates nodeMap accordingly, and returns the node's ID """
	if stream.idx % 1e5 == 0:
		print(f'Progress: {stream.progress() * 100:.2f}%')
	# Find node
	stream.skipWhitespace()
	if stream.peek() == '':
		raise Exception(f'ERROR: Unexpected EOF at index {stream.idx}')
	elif stream.peek() == '(': # Start of inner node
		stream.next()
		childIds: list[str] = []
		while True:
			# Read child
			childId = parseNewick(stream, nodeMap, nameToFirstId, dupNameToIds)
			childIds.append(childId)
			# Check for next child or end of node
			stream.skipWhitespace()
			if stream.peek() == '':
				raise Exception(f'ERROR: Unexpected EOF at index {stream.idx}')
			elif stream.peek() == ',': # Expect another child
				stream.next()
				continue
			else: # End of child list
				# Get node name and id
				stream.next() # Consume an expected ')'
				stream.skipWhitespace()
				name, id = parseNewickName(stream)
				updateNameMaps(name, id, nameToFirstId, dupNameToIds)
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
		name, id = parseNewickName(stream)
		updateNameMaps(name, id, nameToFirstId, dupNameToIds)
		nodeMap[id] = Node(name, [], None, 1, False)
		return id
def parseNewickName(stream: BasicStream) -> tuple[str, str]:
	""" Parses a node name from 'stream', and returns a (name, id) pair """
	name: str
	nameChars = []
	if stream.peek() == '':
		raise Exception(f'ERROR: Unexpected EOF at index {stream.idx}')
	elif stream.peek() == "'": # Quoted name
		nameChars.append(stream.next())
		while True:
			if stream.peek() == '':
				raise Exception(f'ERROR: Unexpected EOF at index {stream.idx}')
			elif stream.peek() == "'":
				nameChars.append(stream.next())
				if stream.peek() == "'": # '' is escaped-quote
					nameChars.append(stream.next())
					continue
				break
			nameChars.append(stream.next())
	else:
		while stream.hasNext() and not re.match(r'[(),;]', stream.peek()):
			nameChars.append(stream.next())
		if stream.peek() == ';': # Ignore trailing input semicolon
			stream.next()
	# Convert to (name, id)
	name = ''.join(nameChars).rstrip().lower()
	if name.startswith('mrca'):
		return (name, name)
	elif name[0] == "'":
		match = re.fullmatch(r"'([^\\\"]+) (ott\d+)'", name)
		if match is None:
			raise Exception(f'ERROR: invalid name \'{name}\'')
		name = match.group(1).replace("''", "'")
		return (name, match.group(2))
	else:
		match = re.fullmatch(r"([^\\\"]+)_(ott\d+)", name)
		if match is None:
			raise Exception(f'ERROR: invalid name \'{name}\'')
		return (match.group(1).replace('_', ' '), match.group(2))
def updateNameMaps(name: str, id: str, nameToFirstId: dict[str, str], dupNameToIds: dict[str, list[str]]) -> None:
	""" Update maps upon a newly parsed name """
	if name not in nameToFirstId:
		nameToFirstId[name] = id
	else:
		if name not in dupNameToIds:
			dupNameToIds[name] = [nameToFirstId[name], id]
		else:
			dupNameToIds[name].append(id)
def convertMrcaName(id: str, nodeMap: dict[str, Node]) -> str:
	""" Update a node in a tree to be named after 2 descendants.
		Returns the name of one such descendant, for use during recursion. """
	node = nodeMap[id]
	name = node.name
	childIds = node.childIds
	if len(childIds) < 2:
		raise Exception(f'ERROR: MRCA node \'{name}\' has less than 2 children')
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
	if childName1.startswith('mrca'):
		childName1 = convertMrcaName(childId1, nodeMap)
	if childName2.startswith('mrca'):
		childName2 = convertMrcaName(childId2, nodeMap)
	# Check for composite names
	match = re.fullmatch(r'\[(.+) \+ (.+)]', childName1)
	if match is not None:
		childName1 = match.group(1)
	match = re.fullmatch(r'\[(.+) \+ (.+)]', childName2)
	if match is not None:
		childName2 = match.group(1)
	# Create composite name
	node.name = f'[{childName1} + {childName2}]'
	return childName1

if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.parse_args()
	# 
	genData(TREE_FILE, ANN_FILE, PICKED_NAMES_FILE, DB_FILE)
