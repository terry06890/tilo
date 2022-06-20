#!/usr/bin/python3

import sys, re, sqlite3
import os.path
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import gzip, jsonpickle

hostname = "localhost"
port = 8000
dbFile = "data/data.db"
imgDir = "../public/img/"
SEARCH_SUGG_LIMIT = 5

usageInfo =  f"usage: {sys.argv[0]}\n"
usageInfo += "Starts a server that listens for GET requests to http://" + hostname + ":" + str(port) + ".\n"
usageInfo += "Responds to path+query /data/type1?name=name1 with JSON data.\n"
usageInfo += "An additional query parameter tree=reduced is usable to get reduced-tree data\n"
usageInfo += "\n"
usageInfo += "If type1 is 'node': Responds with map from names to TolNode objects for node name1 and it's children.\n"
usageInfo += "If type1 is 'chain': Like 'node', but gets nodes from name1 up to the root, and their direct children.\n"
usageInfo += "If type1 is 'search': Responds with a SearchSuggResponse object.\n"
usageInfo += "If type1 is 'info': Responds with a TileInfoResponse object.\n"
usageInfo += "(Object type information can be found in src/)\n"
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

# Classes for objects sent as responses (matches lib.ts types in client-side code)
class TolNode:
	""" Used when responding to 'node' and 'chain' requests """
	def __init__(self, otolId, children, parent=None, tips=0, pSupport=False, commonName=None, imgName=None):
		self.otolId = otolId         # string | null
		self.children = children     # string[]
		self.parent = parent         # string | null
		self.tips = tips             # number
		self.pSupport = pSupport     # boolean
		self.commonName = commonName # null | string
		self.imgName = imgName       # null | string | [string,string] | [null, string] | [string, null]
class SearchSugg:
	""" Represents a search suggestion """
	def __init__(self, name, canonicalName=None):
		self.name = name                   # string
		self.canonicalName = canonicalName # string | null
class SearchSuggResponse:
	""" Sent as responses to 'search' requests """
	def __init__(self, searchSuggs, hasMore):
		self.suggs = searchSuggs # SearchSugg[]
		self.hasMore = hasMore   # boolean
class DescInfo:
	""" Represents a tol-node's associated description """
	def __init__(self, text, wikiId, fromRedirect, fromDbp):
		self.text = text                 # string
		self.wikiId = wikiId             # number
		self.fromRedirect = fromRedirect # boolean
		self.fromDbp = fromDbp           # boolean
class ImgInfo:
	""" Represents a tol-node's associated image """
	def __init__(self, id, src, url, license, artist, credit):
		self.id = id           # number
		self.src = src         # string
		self.url = url         # string
		self.license = license # string
		self.artist = artist   # string
		self.credit = credit   # string
class InfoResponse:
	""" Sent as responses to 'info' requests """
	def __init__(self, tolNode, descData, imgData):
		self.tolNode = tolNode   # null | TolNode
		self.descData = descData # null | DescInfo | [DescInfo, DescInfo]
		self.imgData = imgData   # null | ImgInfo | [ImgInfo, ImgInfo]

# Connect to db
dbCon = sqlite3.connect(dbFile)
# Some functions
def lookupNodes(names, useReducedTree):
	# Get node info
	nameToNodes = {}
	cur = dbCon.cursor()
	nodesTable = "nodes" if not useReducedTree else "r_nodes"
	edgesTable = "edges" if not useReducedTree else "r_edges"
	queryParamStr = ",".join(["?"] * len(names))
	query = f"SELECT name, id, tips FROM {nodesTable} WHERE name IN ({queryParamStr})"
	for (nodeName, otolId, tips) in cur.execute(query, names):
		nameToNodes[nodeName] = TolNode(otolId, [], tips=tips)
	# Get child info
	query = f"SELECT node, child FROM {edgesTable} WHERE node IN ({queryParamStr})"
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
	query = f"SELECT node, child, p_support FROM {edgesTable} WHERE child IN ({queryParamStr})"
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
		if altName != name:
			nameToNodes[name].commonName = altName
	#
	return nameToNodes
def lookupName(name, useReducedTree):
	cur = dbCon.cursor()
	results = []
	hasMore = False
	# Get node names and alt-names
	(query1, query2) = (None, None)
	if not useReducedTree:
		query1 = "SELECT DISTINCT name FROM nodes" \
			" WHERE name LIKE ? ORDER BY length(name) LIMIT ?"
		query2 = "SELECT DISTINCT alt_name, name FROM names" \
			" WHERE alt_name LIKE ? ORDER BY length(alt_name) LIMIT ?"
	else:
		query1 = "SELECT DISTINCT name FROM r_nodes" \
			" WHERE name LIKE ? ORDER BY length(name) LIMIT ?"
		query2 = "SELECT DISTINCT alt_name, names.name FROM" \
			" names INNER JOIN r_nodes ON names.name = r_nodes.name" \
			" WHERE alt_name LIKE ? ORDER BY length(alt_name) LIMIT ?"
	# Join results, and get shortest
	suggs = []
	for (nodeName,) in cur.execute(query1, (name + "%", SEARCH_SUGG_LIMIT + 1)):
		suggs.append(SearchSugg(nodeName))
	for (altName, nodeName) in cur.execute(query2, (name + "%", SEARCH_SUGG_LIMIT + 1)):
		suggs.append(SearchSugg(altName, nodeName))
	# If insufficient results, try substring-search
	foundNames = {n.name for n in suggs}
	if len(suggs) < SEARCH_SUGG_LIMIT:
		newLim = SEARCH_SUGG_LIMIT + 1 - len(suggs)
		for (nodeName,) in cur.execute(query1, ("%" + name + "%", newLim)):
			if nodeName not in foundNames:
				suggs.append(SearchSugg(nodeName))
				foundNames.add(nodeName)
	if len(suggs) < SEARCH_SUGG_LIMIT:
		newLim = SEARCH_SUGG_LIMIT + 1 - len(suggs)
		for (altName, nodeName) in cur.execute(query2, ("%" + name + "%", SEARCH_SUGG_LIMIT + 1)):
			if altName not in foundNames:
				suggs.append(SearchSugg(altName, nodeName))
				foundNames.add(altName)
	#
	suggs.sort(key=lambda x: x.name)
	suggs.sort(key=lambda x: len(x.name))
	results = suggs[:SEARCH_SUGG_LIMIT]
	if len(suggs) > SEARCH_SUGG_LIMIT:
		hasMore = True
	return SearchSuggResponse(results, hasMore)
def lookupNodeInfo(name, useReducedTree):
	cur = dbCon.cursor()
	# Get node-object info
	nameToNodes = lookupNodes([name], useReducedTree)
	tolNode = nameToNodes[name] if name in nameToNodes else None
	# Get node desc
	descData = None
	match = re.fullmatch(r"\[(.+) \+ (.+)]", name)
	if match == None:
		query = "SELECT desc, wiki_id, redirected, from_dbp FROM" \
			" wiki_ids INNER JOIN descs ON wiki_ids.id = descs.wiki_id WHERE wiki_ids.name = ?"
		row = cur.execute(query, (name,)).fetchone()
		if row != None:
			(desc, wikiId, redirected, fromDbp) = row
			descData = DescInfo(desc, wikiId, redirected == 1, fromDbp == 1)
	else:
		# Get descs for compound-node element
		descData = [None, None]
		query = "SELECT name, desc, wiki_id, redirected, from_dbp FROM" \
			" wiki_ids INNER JOIN descs ON wiki_ids.id = descs.wiki_id WHERE wiki_ids.name IN (?, ?)"
		for (nodeName, desc, wikiId, redirected, fromDbp) in cur.execute(query, match.group(1,2)):
			idx = 0 if nodeName == match.group(1) else 1
			descData[idx] = DescInfo(desc, wikiId, redirected == 1, fromDbp == 1)
	# Get img info
	imgData = None
	if tolNode != None:
		if isinstance(tolNode.imgName, str):
			otolId = tolNode.imgName[:-4] # Convert filename excluding .jpg suffix
			query = "SELECT images.id, images.src, url, license, artist, credit FROM" \
				" nodes INNER JOIN node_imgs ON nodes.name = node_imgs.name" \
				" INNER JOIN images ON node_imgs.img_id = images.id AND node_imgs.src = images.src" \
				" WHERE nodes.id = ?"
			(imgId, imgSrc, url, license, artist, credit) = cur.execute(query, (otolId,)).fetchone()
			imgData = ImgInfo(imgId, imgSrc, url, license, artist, credit)
		elif isinstance(tolNode.imgName, list):
			# Get info for compound-image parts
			imgData = [None, None]
			idsToLookup = [n[:-4] for n in tolNode.imgName if n != None]
			query = "SELECT nodes.id, images.id, images.src, url, license, artist, credit FROM" \
				" nodes INNER JOIN node_imgs ON nodes.name = node_imgs.name" \
				" INNER JOIN images ON node_imgs.img_id = images.id AND node_imgs.src = images.src" \
				" WHERE nodes.id IN ({})".format(",".join(["?"] * len(idsToLookup)))
			for (imgOtolId, imgId, imgSrc, url, license, artist, credit) in cur.execute(query, idsToLookup):
				imgName1 = tolNode.imgName[0]
				idx = 0 if (imgName1 != None and imgOtolId == imgName1[:-4]) else 1
				imgData[idx] = ImgInfo(imgId, imgSrc, url, license, artist, credit)
	#
	return InfoResponse(tolNode, descData, imgData)

class DbServer(BaseHTTPRequestHandler):
	def do_GET(self):
		# Parse URL
		urlParts = urllib.parse.urlparse(self.path)
		path = urllib.parse.unquote(urlParts.path)
		queryDict = urllib.parse.parse_qs(urlParts.query)
		# Check first element of path
		match = re.match(r"/([^/]+)/(.+)", path)
		if match != None and match.group(1) == "data" and "name" in queryDict and \
			("tree" not in queryDict or queryDict["tree"][0] == "reduced"):
			reqType = match.group(2)
			name = queryDict["name"][0]
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
					# Conditionally add children
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
				self.respondJson(lookupName(name, useReducedTree))
				return
			elif reqType == "info":
				self.respondJson(lookupNodeInfo(name, useReducedTree))
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
