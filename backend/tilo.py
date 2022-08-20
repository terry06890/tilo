#!/usr/bin/python3

import sys, os.path, re, time
import urllib.parse
import sqlite3
import gzip, jsonpickle

HELP_INFO = """
WSGI script that serves tree-of-life data, in JSON form.

Expected HTTP query parameters:
- name: Provides a name, or partial name, of a tree-of-life node. If absent, the root node is used.
- type: Specifies what data to reply with.
    If 'node', reply with a name-to-TolNode map, describing the named node and it's children.
    If 'sugg', reply with a SearchSuggResponse, describing search suggestions for the possibly-partial name.
    If 'info', reply with an InfoResponse, describing the named node.
- toroot: Used with type=node, and causes inclusion of ancestors, and their children.
    A value of 1 indicates true, and other indicate false
- excl: Used with toroot, and names a node whose ancestors need not be included.
- limit: Used with type=sugg to specify the max number of suggestions.
- tree: Specifies which tree should be used.
    May be 'trimmed', 'images', or 'picked', corresponding to the
    weakly-trimmed, images-only, and picked-nodes trees. The default
    is 'images'.
"""
if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser(description=HELP_INFO, formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.parse_args()

DB_FILE = "tolData/data.db"
DEFAULT_SUGG_LIM = 5
MAX_SUGG_LIM = 50
ROOT_NAME = "cellular organisms"

# Classes for objects sent as responses (matches lib.ts types in client-side code)
class TolNode:
	" Used when responding to 'node' and 'chain' requests "
	def __init__(self, otolId, children, parent=None, tips=0, pSupport=False, commonName=None, imgName=None):
		self.otolId = otolId         # string | null
		self.children = children     # string[]
		self.parent = parent         # string | null
		self.tips = tips             # number
		self.pSupport = pSupport     # boolean
		self.commonName = commonName # null | string
		self.imgName = imgName       # null | string | [string,string] | [null, string] | [string, null]
class SearchSugg:
	" Represents a search suggestion "
	def __init__(self, name, canonicalName=None):
		self.name = name                   # string
		self.canonicalName = canonicalName # string | null
class SearchSuggResponse:
	" Sent as responses to 'sugg' requests "
	def __init__(self, searchSuggs, hasMore):
		self.suggs = searchSuggs # SearchSugg[]
		self.hasMore = hasMore   # boolean
class DescInfo:
	" Represents a node's associated description "
	def __init__(self, text, wikiId, fromRedirect, fromDbp):
		self.text = text                 # string
		self.wikiId = wikiId             # number
		self.fromRedirect = fromRedirect # boolean
		self.fromDbp = fromDbp           # boolean
class ImgInfo:
	" Represents a node's associated image "
	def __init__(self, id, src, url, license, artist, credit):
		self.id = id           # number
		self.src = src         # string
		self.url = url         # string
		self.license = license # string
		self.artist = artist   # string
		self.credit = credit   # string
class NodeInfo:
	" Represents info about a node "
	def __init__(self, tolNode, descInfo, imgInfo):
		self.tolNode = tolNode   # TolNode
		self.descInfo = descInfo # null | DescInfo
		self.imgInfo = imgInfo   # null | ImgInfo
class InfoResponse:
	" Sent as responses to 'info' requests "
	def __init__(self, nodeInfo, subNodesInfo):
		self.nodeInfo = nodeInfo         # NodeInfo
		self.subNodesInfo = subNodesInfo # [] | [NodeInfo | null, NodeInfo | null]

# For data lookup
def lookupNodes(names, tree, dbCur):
	" For a set of node names, returns a name-to-TolNode map that describes those nodes "
	# Get node info
	nameToNodes = {}
	tblSuffix = getTableSuffix(tree)
	nodesTable = f"nodes_{tblSuffix}"
	edgesTable = f"edges_{tblSuffix}"
	queryParamStr = ",".join(["?"] * len(names))
	query = f"SELECT name, id, tips FROM {nodesTable} WHERE name IN ({queryParamStr})"
	for (nodeName, otolId, tips) in dbCur.execute(query, names):
		nameToNodes[nodeName] = TolNode(otolId, [], tips=tips)
	# Get child info
	query = f"SELECT parent, child FROM {edgesTable} WHERE parent IN ({queryParamStr})"
	for (nodeName, childName) in dbCur.execute(query, names):
		nameToNodes[nodeName].children.append(childName)
	# Order children by tips
	for (nodeName, node) in nameToNodes.items():
		childToTips = {}
		query = "SELECT name, tips FROM {} WHERE name IN ({})"
		query = query.format(nodesTable, ",".join(["?"] * len(node.children)))
		for (n, tips) in dbCur.execute(query, node.children):
			childToTips[n] = tips
		node.children.sort(key=lambda n: childToTips[n], reverse=True)
	# Get parent info
	query = f"SELECT parent, child, p_support FROM {edgesTable} WHERE child IN ({queryParamStr})"
	for (nodeName, childName, pSupport) in dbCur.execute(query, names):
		nameToNodes[childName].parent = nodeName
		nameToNodes[childName].pSupport = (pSupport == 1)
	# Get image names
	idsToNames = {nameToNodes[n].otolId: n for n in nameToNodes.keys()}
	query = "SELECT nodes.id from nodes INNER JOIN node_imgs ON nodes.name = node_imgs.name" \
		" WHERE nodes.id IN ({})".format(",".join(["?"] * len(idsToNames)))
	for (otolId,) in dbCur.execute(query, list(idsToNames.keys())):
		nameToNodes[idsToNames[otolId]].imgName = otolId + ".jpg"
	# Get 'linked' images for unresolved names
	unresolvedNames = [n for n in nameToNodes if nameToNodes[n].imgName == None]
	query = "SELECT name, otol_ids from linked_imgs WHERE name IN ({})"
	query = query.format(",".join(["?"] * len(unresolvedNames)))
	for (name, otolIds) in dbCur.execute(query, unresolvedNames):
		if "," not in otolIds:
			nameToNodes[name].imgName = otolIds + ".jpg"
		else:
			id1, id2 = otolIds.split(",")
			nameToNodes[name].imgName = [
				id1 + ".jpg" if id1 != "" else None,
				id2 + ".jpg" if id2 != "" else None,
			]
	# Get preferred-name info
	query = f"SELECT name, alt_name FROM names WHERE pref_alt = 1 AND name IN ({queryParamStr})"
	for (name, altName) in dbCur.execute(query, names):
		nameToNodes[name].commonName = altName
	#
	return nameToNodes
def lookupSuggs(searchStr, suggLimit, tree, dbCur):
	" For a search string, returns a SearchSuggResponse describing search suggestions "
	results = []
	hasMore = False
	# Get node names and alt-names
	query1, query2 = (None, None)
	nodesTable = f"nodes_{getTableSuffix(tree)}"
	query1 = f"SELECT DISTINCT name FROM {nodesTable}" \
		f" WHERE name LIKE ? AND name NOT LIKE '[%' ORDER BY length(name) LIMIT ?"
	query2 = f"SELECT DISTINCT alt_name, names.name FROM" \
		f" names INNER JOIN {nodesTable} ON names.name = {nodesTable}.name" \
		f" WHERE alt_name LIKE ? ORDER BY length(alt_name) LIMIT ?"
	# Join results, and get shortest
	suggs = []
	for (nodeName,) in dbCur.execute(query1, (searchStr + "%", suggLimit + 1)):
		suggs.append(SearchSugg(nodeName))
	for (altName, nodeName) in dbCur.execute(query2, (searchStr + "%", suggLimit + 1)):
		suggs.append(SearchSugg(altName, nodeName))
	# If insufficient results, try substring-search
	foundNames = {n.name for n in suggs}
	suggs2 = []
	if len(suggs) < suggLimit:
		newLim = suggLimit + 1 - len(suggs)
		for (nodeName,) in dbCur.execute(query1, ("%" + searchStr + "%", newLim)):
			if nodeName not in foundNames:
				suggs2.append(SearchSugg(nodeName))
				foundNames.add(nodeName)
	if len(suggs) + len(suggs2) < suggLimit:
		newLim = suggLimit + 1 - len(suggs) - len(suggs2)
		for (altName, nodeName) in dbCur.execute(query2, ("%" + searchStr + "%", suggLimit + 1)):
			if altName not in foundNames:
				suggs2.append(SearchSugg(altName, nodeName))
				foundNames.add(altName)
	# Sort results
	suggs.sort(key=lambda x: x.name)
	suggs.sort(key=lambda x: len(x.name))
	suggs2.sort(key=lambda x: x.name)
	suggs2.sort(key=lambda x: len(x.name))
	suggs.extend(suggs2)
	# Apply suggestion-quantity limit
	results = suggs[:suggLimit]
	if len(suggs) > suggLimit:
		hasMore = True
	#
	return SearchSuggResponse(results, hasMore)
def lookupInfo(name, tree, dbCur):
	" For a node name, returns an InfoResponse, or None "
	# Get node info
	nameToNodes = lookupNodes([name], tree, dbCur)
	tolNode = nameToNodes[name] if name in nameToNodes else None
	if tolNode == None:
		return None
	# Check for compound node
	match = re.fullmatch(r"\[(.+) \+ (.+)]", name)
	subNames = [match.group(1), match.group(2)] if match != None else []
	if len(subNames) > 0:
		nameToSubNodes = lookupNodes(subNames, tree, dbCur)
		if len(nameToSubNodes) < 2: # Possible when a subname-denoted node has been trimmed away
			subNames = [n if n in nameToSubNodes else None for n in subNames]
		nameToNodes.update(nameToSubNodes)
	namesToLookup = [name] if len(subNames) == 0 else [n for n in subNames if n != None]
	# Get desc info
	nameToDescInfo = {}
	query = "SELECT name, desc, wiki_id, redirected, from_dbp FROM" \
		" wiki_ids INNER JOIN descs ON wiki_ids.id = descs.wiki_id" \
		" WHERE wiki_ids.name IN ({})".format(",".join(["?"] * len(namesToLookup)))
	for (nodeName, desc, wikiId, redirected, fromDbp) in dbCur.execute(query, namesToLookup):
		nameToDescInfo[nodeName] = DescInfo(desc, wikiId, redirected == 1, fromDbp == 1)
	# Get image info
	nameToImgInfo = {}
	idsToNames = {nameToNodes[n].imgName[:-4]: n for n in namesToLookup if nameToNodes[n].imgName != None}
	idsToLookup = list(idsToNames.keys()) # Lookup using IDs avoids having to check linked_imgs
	query = "SELECT nodes.id, images.id, images.src, url, license, artist, credit FROM" \
		" nodes INNER JOIN node_imgs ON nodes.name = node_imgs.name" \
		" INNER JOIN images ON node_imgs.img_id = images.id AND node_imgs.src = images.src" \
		" WHERE nodes.id IN ({})".format(",".join(["?"] * len(idsToLookup)))
	for (id, imgId, imgSrc, url, license, artist, credit) in dbCur.execute(query, idsToLookup):
		nameToImgInfo[idsToNames[id]] = ImgInfo(imgId, imgSrc, url, license, artist, credit)
	# Construct response
	nodeInfoObjs = [
		NodeInfo(
			nameToNodes[n],
			nameToDescInfo[n] if n in nameToDescInfo else None,
			nameToImgInfo[n] if n in nameToImgInfo else None
		) if n != None else None for n in [name] + subNames
	]
	return InfoResponse(nodeInfoObjs[0], nodeInfoObjs[1:])
def getTableSuffix(tree):
	return "t" if tree == "trimmed" else "i" if tree == "images" else "p"

# Queries the database, and constructs a response object
def handleReq(dbCur, environ):
	# Get query params
	queryStr = environ["QUERY_STRING"] if "QUERY_STRING" in environ else ""
	queryDict = urllib.parse.parse_qs(queryStr)
	# Set vars from params
	name = queryDict["name"][0] if "name" in queryDict else None
	if name == None: # Get root node
		name = ROOT_NAME # Hard-coding this is significantly faster (in testing, querying could take 0.5 seconds)
		#query = "SELECT name FROM nodes LEFT JOIN edges ON nodes.name = edges.child WHERE edges.parent IS NULL LIMIT 1"
		#(name,) = dbCur.execute(query).fetchone()
	reqType = queryDict["type"][0] if "type" in queryDict else None
	tree = queryDict["tree"][0] if "tree" in queryDict else "images"
	# Check for valid 'tree'
	if tree != None and re.fullmatch(r"trimmed|images|picked", tree) == None:
		return None
	# Get data of requested type
	if reqType == "node":
		toroot = queryDict["toroot"][0] == '1' if "toroot" in queryDict else False
		if not toroot:
			tolNodes = lookupNodes([name], tree, dbCur)
			if len(tolNodes) > 0:
				tolNode = tolNodes[name]
				childNodeObjs = lookupNodes(tolNode.children, tree, dbCur)
				childNodeObjs[name] = tolNode
				return childNodeObjs
		else:
			# Get ancestors to skip inclusion of
			nodesToSkip = set()
			nodeName = queryDict["excl"][0] if "excl" in queryDict else None
			if nodeName != None:
				edgesTable = f"edges_{getTableSuffix(tree)}"
				while True:
					row = dbCur.execute(f"SELECT parent FROM {edgesTable} WHERE child = ?", (nodeName,)).fetchone()
					if row == None:
						break
					parent = row[0]
					nodesToSkip.add(parent)
					nodeName = parent
			#
			results = {}
			ranOnce = False
			while True:
				# Get node
				tolNodes = lookupNodes([name], tree, dbCur)
				if len(tolNodes) == 0:
					if not ranOnce:
						return results
					print(f"ERROR: Parent-chain node {name} not found", file=sys.stderr)
					break
				tolNode = tolNodes[name]
				results[name] = tolNode
				# Potentially add children
				if not ranOnce:
					ranOnce = True
				else:
					childNamesToAdd = []
					for childName in tolNode.children:
						if childName not in results:
							childNamesToAdd.append(childName)
					childNodeObjs = lookupNodes(childNamesToAdd, tree, dbCur)
					results.update(childNodeObjs)
				# Check if root
				if tolNode.parent == None or tolNode.parent in nodesToSkip:
					return results
				else:
					name = tolNode.parent
	elif reqType == "sugg":
		# Check for suggestion-limit
		suggLimit = None
		invalidLimit = False
		try:
			suggLimit = int(queryDict["limit"][0]) if "limit" in queryDict else DEFAULT_SUGG_LIM
			if suggLimit <= 0 or suggLimit > MAX_SUGG_LIM:
				invalidLimit = True
		except ValueError:
			invalidLimit = True
			print(f"INFO: Invalid limit {suggLimit}", file=sys.stderr)
		# Get search suggestions
		if not invalidLimit:
			return lookupSuggs(name, suggLimit, tree, dbCur)
	elif reqType == "info":
		infoResponse = lookupInfo(name, tree, dbCur)
		if infoResponse != None:
			return infoResponse
	# On failure, provide empty response
	return None
# Entry point for the WSGI script
def application(environ, start_response):
	# Open db
	dbCon = sqlite3.connect(DB_FILE)
	dbCur = dbCon.cursor()
	# Get response object
	val = handleReq(dbCur, environ)
	# Construct response
	data = jsonpickle.encode(val, unpicklable=False).encode()
	headers = [("Content-type", "application/json")]
	if "HTTP_ACCEPT_ENCODING" in environ and "gzip" in environ["HTTP_ACCEPT_ENCODING"]:
		if len(data) > 100:
			data = gzip.compress(data, compresslevel=5)
			headers.append(("Content-encoding", "gzip"))
	headers.append(('Content-Length', str(len(data))))
	start_response('200 OK', headers)
	return [data]
