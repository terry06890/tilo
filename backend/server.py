#!/usr/bin/python3

import sys, re, sqlite3, time
import os.path
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import gzip, jsonpickle

hostname = "localhost"
port = 8000
dbFile = "data/data.db"
imgDir = "../public/img/"
DEFAULT_SUGG_LIM = 5
MAX_SUGG_LIM = 50

usageInfo = f"""
Usage: {sys.argv[0]}

Starts a server that listens for GET requests to http://" + hostname + ":" + str(port) + ".
Responds to path+query /data/type1?name=name1 with JSON data.
The 'name' parameter can be omitted, which specifies the root node.
An additional query parameter tree=reduced is usable to get reduced-tree data.

If type1 is 'node': Responds with a name-to-TolNode map, describing the node and it's children.
If type1 is 'chain': Like 'node', but also gets nodes upward to the root, and their direct children.
If type1 is 'search': Responds with a SearchSuggResponse.
    A query parameter 'limit=n1' specifies the max number of suggestions (default 5).
If type1 is 'info': Responds with an InfoResponse.
"""
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

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
	" Sent as responses to 'search' requests "
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
	def __init__(self, nodeInfo, subNodesInfo = None):
		self.nodeInfo = nodeInfo         # NodeInfo
		self.subNodesInfo = subNodesInfo # [] | [NodeInfo, NodeInfo]

# Connect to db
dbCon = sqlite3.connect(dbFile)
# Get root node
dbCur = dbCon.cursor()
query = "SELECT name FROM nodes LEFT JOIN edges ON nodes.name = edges.child WHERE edges.parent IS NULL LIMIT 1"
(rootName,) = dbCur.execute(query).fetchone()

# Some helper functions
def lookupNodes(names, useReducedTree):
	" For a set of node names, returns a name-to-TolNode map that describes those nodes "
	global dbCon
	cur = dbCon.cursor()
	# Get node info
	nameToNodes = {}
	nodesTable = "nodes" if not useReducedTree else "r_nodes"
	edgesTable = "edges" if not useReducedTree else "r_edges"
	queryParamStr = ",".join(["?"] * len(names))
	query = f"SELECT name, id, tips FROM {nodesTable} WHERE name IN ({queryParamStr})"
	for (nodeName, otolId, tips) in cur.execute(query, names):
		nameToNodes[nodeName] = TolNode(otolId, [], tips=tips)
	# Get child info
	query = f"SELECT parent, child FROM {edgesTable} WHERE parent IN ({queryParamStr})"
	for (nodeName, childName) in cur.execute(query, names):
		nameToNodes[nodeName].children.append(childName)
	# Order children by tips
	for (nodeName, node) in nameToNodes.items():
		childToTips = {}
		query = "SELECT name, tips FROM {} WHERE name IN ({})"
		query = query.format(nodesTable, ",".join(["?"] * len(node.children)))
		for (n, tips) in cur.execute(query, node.children):
			childToTips[n] = tips
		node.children.sort(key=lambda n: childToTips[n], reverse=True)
	# Get parent info
	query = f"SELECT parent, child, p_support FROM {edgesTable} WHERE child IN ({queryParamStr})"
	for (nodeName, childName, pSupport) in cur.execute(query, names):
		nameToNodes[childName].parent = nodeName
		nameToNodes[childName].pSupport = (pSupport == 1)
	# Get image names
	idsToNames = {nameToNodes[n].otolId: n for n in nameToNodes.keys()}
	query = "SELECT nodes.id from nodes INNER JOIN node_imgs ON nodes.name = node_imgs.name" \
		" WHERE nodes.id IN ({})".format(",".join(["?"] * len(idsToNames)))
	for (otolId,) in cur.execute(query, list(idsToNames.keys())):
		nameToNodes[idsToNames[otolId]].imgName = otolId + ".jpg"
	# Get 'linked' images for unresolved names
	unresolvedNames = [n for n in nameToNodes if nameToNodes[n].imgName == None]
	query = "SELECT name, otol_ids from linked_imgs WHERE name IN ({})"
	query = query.format(",".join(["?"] * len(unresolvedNames)))
	for (name, otolIds) in cur.execute(query, unresolvedNames):
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
	for (name, altName) in cur.execute(query, names):
		nameToNodes[name].commonName = altName
	#
	return nameToNodes
def lookupName(searchStr, suggLimit, useReducedTree):
	" For a search string, returns a SearchSuggResponse describing search suggestions "
	global dbCon
	cur = dbCon.cursor()
	results = []
	hasMore = False
	# Get node names and alt-names
	query1, query2 = (None, None)
	if not useReducedTree:
		query1 = "SELECT DISTINCT name FROM nodes" \
			" WHERE name LIKE ? AND name NOT LIKE '[%' ORDER BY length(name) LIMIT ?"
		query2 = "SELECT DISTINCT alt_name, name FROM names" \
			" WHERE alt_name LIKE ? ORDER BY length(alt_name) LIMIT ?"
	else:
		query1 = "SELECT DISTINCT name FROM r_nodes" \
			" WHERE name LIKE ? AND name NOT LIKE '[%' ORDER BY length(name) LIMIT ?"
		query2 = "SELECT DISTINCT alt_name, names.name FROM" \
			" names INNER JOIN r_nodes ON names.name = r_nodes.name" \
			" WHERE alt_name LIKE ? ORDER BY length(alt_name) LIMIT ?"
	# Join results, and get shortest
	suggs = []
	for (nodeName,) in cur.execute(query1, (searchStr + "%", suggLimit + 1)):
		suggs.append(SearchSugg(nodeName))
	for (altName, nodeName) in cur.execute(query2, (searchStr + "%", suggLimit + 1)):
		suggs.append(SearchSugg(altName, nodeName))
	# If insufficient results, try substring-search
	foundNames = {n.name for n in suggs}
	if len(suggs) < suggLimit:
		newLim = suggLimit + 1 - len(suggs)
		for (nodeName,) in cur.execute(query1, ("%" + searchStr + "%", newLim)):
			if nodeName not in foundNames:
				suggs.append(SearchSugg(nodeName))
				foundNames.add(nodeName)
	if len(suggs) < suggLimit:
		newLim = suggLimit + 1 - len(suggs)
		for (altName, nodeName) in cur.execute(query2, ("%" + searchStr + "%", suggLimit + 1)):
			if altName not in foundNames:
				suggs.append(SearchSugg(altName, nodeName))
				foundNames.add(altName)
	# Sort results
	suggs.sort(key=lambda x: x.name)
	suggs.sort(key=lambda x: len(x.name))
	# Apply suggestion-quantity limit
	results = suggs[:suggLimit]
	if len(suggs) > suggLimit:
		hasMore = True
	#
	return SearchSuggResponse(results, hasMore)
def lookupNodeInfo(name, useReducedTree):
	" For a node name, returns an InfoResponse, or None "
	global dbCon
	cur = dbCon.cursor()
	# Get node info
	nameToNodes = lookupNodes([name], useReducedTree)
	tolNode = nameToNodes[name] if name in nameToNodes else None
	if tolNode == None:
		return None
	# Check for compound node
	match = re.fullmatch(r"\[(.+) \+ (.+)]", name)
	subNames = [match.group(1), match.group(2)] if match != None else []
	if len(subNames) > 0:
		nameToSubNodes = lookupNodes(subNames, useReducedTree)
		if len(nameToSubNodes) < 2:
			print(f"ERROR: Unable to find sub-names entries for {name}", file=sys.stderr)
			return None
		nameToNodes.update(nameToSubNodes)
	namesToLookup = [name] if len(subNames) == 0 else subNames
	# Get desc info
	nameToDescInfo = {}
	query = "SELECT name, desc, wiki_id, redirected, from_dbp FROM" \
		" wiki_ids INNER JOIN descs ON wiki_ids.id = descs.wiki_id" \
		" WHERE wiki_ids.name IN ({})".format(",".join(["?"] * len(namesToLookup)))
	for (nodeName, desc, wikiId, redirected, fromDbp) in cur.execute(query, namesToLookup):
		nameToDescInfo[nodeName] = DescInfo(desc, wikiId, redirected == 1, fromDbp == 1)
	# Get image info
	nameToImgInfo = {}
	idsToNames = {nameToNodes[n].imgName[:-4]: n for n in namesToLookup if nameToNodes[n].imgName != None}
	idsToLookup = list(idsToNames.keys()) # Lookup using IDs avoids having to check linked_imgs
	query = "SELECT nodes.id, images.id, images.src, url, license, artist, credit FROM" \
		" nodes INNER JOIN node_imgs ON nodes.name = node_imgs.name" \
		" INNER JOIN images ON node_imgs.img_id = images.id AND node_imgs.src = images.src" \
		" WHERE nodes.id IN ({})".format(",".join(["?"] * len(idsToLookup)))
	for (id, imgId, imgSrc, url, license, artist, credit) in cur.execute(query, idsToLookup):
		nameToImgInfo[idsToNames[id]] = ImgInfo(imgId, imgSrc, url, license, artist, credit)
	# Construct response
	nodeInfoObjs = [
		NodeInfo(
			nameToNodes[n],
			nameToDescInfo[n] if n in nameToDescInfo else None,
			nameToImgInfo[n] if n in nameToImgInfo else None
		) for n in [name] + subNames
	]
	return InfoResponse(nodeInfoObjs[0], nodeInfoObjs[1:])

class DbServer(BaseHTTPRequestHandler):
	" Provides handlers for requests to the server "
	def do_GET(self):
		global rootName
		# Parse URL
		urlParts = urllib.parse.urlparse(self.path)
		path = urllib.parse.unquote(urlParts.path)
		queryDict = urllib.parse.parse_qs(urlParts.query)
		# Check first element of path
		match = re.match(r"/([^/]+)/(.+)", path)
		if match != None and match.group(1) == "data" and \
			("tree" not in queryDict or queryDict["tree"][0] == "reduced"):
			reqType = match.group(2)
			name = queryDict["name"][0] if "name" in queryDict else rootName
			useReducedTree = "tree" in queryDict
			# Check query string
			if reqType == "node":
				tolNodes = lookupNodes([name], useReducedTree)
				if len(tolNodes) > 0:
					tolNode = tolNodes[name]
					childNodeObjs = lookupNodes(tolNode.children, useReducedTree)
					childNodeObjs[name] = tolNode
					self.respondJson(childNodeObjs)
					return
			elif reqType == "chain":
				results = {}
				ranOnce = False
				while True:
					# Get node
					tolNodes = lookupNodes([name], useReducedTree)
					if len(tolNodes) == 0:
						if not ranOnce:
							self.respondJson(results)
							return
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
						childNodeObjs = lookupNodes(childNamesToAdd, useReducedTree)
						results.update(childNodeObjs)
					# Check if root
					if tolNode.parent == None:
						self.respondJson(results)
						return
					else:
						name = tolNode.parent
			elif reqType == "search":
				# Check for suggestion-limit
				suggLimit = None
				invalidLimit = False
				try:
					suggLimit = int(queryDict["limit"][0]) if "limit" in queryDict else DEFAULT_SUGG_LIM
					if suggLimit <= 0 or suggLimit > MAX_SUGG_LIM:
						invalidLimit = True
				except ValueError:
					invalidLimit = True
					print(f"Invalid limit {suggLimit}")
				# Get search suggestions
				if not invalidLimit:
					self.respondJson(lookupName(name, suggLimit, useReducedTree))
					return
			elif reqType == "info":
				infoResponse = lookupNodeInfo(name, useReducedTree)
				if infoResponse != None:
					self.respondJson(infoResponse)
					return
		self.send_response(404)
	def respondJson(self, val):
		content = jsonpickle.encode(val, unpicklable=False).encode("utf-8")
		self.send_response(200)
		self.send_header("Content-type", "application/json")
		if "accept-encoding" in self.headers and "gzip" in self.headers["accept-encoding"]:
			if len(content) > 100:
				content = gzip.compress(content, compresslevel=5)
				self.send_header("Content-length", str(len(content)))
				self.send_header("Content-encoding", "gzip")
		self.end_headers()
		self.wfile.write(content)

server = HTTPServer((hostname, port), DbServer)
print(f"Server started at http://{hostname}:{port}")
try:
	server.serve_forever()
except KeyboardInterrupt:
	pass
server.server_close()
dbCon.close()
print("Server stopped")
