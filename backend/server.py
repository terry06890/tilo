#!/usr/bin/python3

import sys, re, sqlite3, json
import os.path
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

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

# Connect to db
dbCon = sqlite3.connect(dbFile)
# Some functions
def lookupNodes(names, useReducedTree):
	# Get node info
	nodeObjs = {}
	cur = dbCon.cursor()
	nodesTable = "nodes" if not useReducedTree else "r_nodes"
	edgesTable = "edges" if not useReducedTree else "r_edges"
	queryParamStr = ",".join(["?"] * len(names))
	query = f"SELECT name, id, tips FROM {nodesTable} WHERE name IN ({queryParamStr})"
	for (nodeName, otolId, tips) in cur.execute(query, names):
		nodeObjs[nodeName] = {
			"otolId": otolId,
			"children": [],
			"parent": None,
			"tips": tips,
			"pSupport": False,
			"commonName": None,
			"imgName": None,
		}
	query = f"SELECT node, child FROM {edgesTable} WHERE node IN ({queryParamStr})"
	for (nodeName, childName) in cur.execute(query, names):
		nodeObjs[nodeName]["children"].append(childName)
	query = f"SELECT node, child, p_support FROM {edgesTable} WHERE child IN ({queryParamStr})"
	for (nodeName, childName, pSupport) in cur.execute(query, names):
		nodeObjs[childName]["parent"] = None if nodeName == "" else nodeName
		nodeObjs[childName]["pSupport"] = (pSupport == 1)
	# Get image names
	idsToNames = {nodeObjs[n]["otolId"]: n for n in nodeObjs.keys()}
	query = "SELECT id FROM node_imgs WHERE id IN ({})".format(",".join(["?"] * len(idsToNames)))
	for (otolId,) in cur.execute(query, list(idsToNames.keys())):
		nodeObjs[idsToNames[otolId]]["imgName"] = otolId + ".jpg"
	## Get 'linked' images for unresolved names
	#unresolvedNames = [n for n in nodeObjs if nodeObjs[n]["imgName"] == None]
	#query = "SELECT name, eol_id, eol_id2 from linked_imgs WHERE name IN ({})"
	#query = query.format(",".join(["?"] * len(unresolvedNames)))
	#for (name, eolId, eolId2) in cur.execute(query, unresolvedNames):
	#	if eolId2 == None:
	#		nodeObjs[name]["imgName"] = str(eolId) + ".jpg"
	#	else:
	#		nodeObjs[name]["imgName"] = [
	#			str(eolId) + ".jpg" if eolId != 0 else None,
	#			str(eolId2) + ".jpg" if eolId2 != 0 else None,
	#		]
	# Get preferred-name info
	query = f"SELECT name, alt_name FROM names WHERE pref_alt = 1 AND name IN ({queryParamStr})"
	for (name, altName) in cur.execute(query, names):
		if altName != name:
			nodeObjs[name]["commonName"] = altName
	#
	return nodeObjs
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
	temp = []
	for row in cur.execute(query1, (name + "%", SEARCH_SUGG_LIMIT + 1)):
		temp.append({"name": row[0], "canonicalName": None})
	for row in cur.execute(query2, (name + "%", SEARCH_SUGG_LIMIT + 1)):
		temp.append({"name": row[0], "canonicalName": row[1]})
	temp.sort(key=lambda x: x["name"])
	temp.sort(key=lambda x: len(x["name"]))
	results = temp[:SEARCH_SUGG_LIMIT]
	if len(temp) > SEARCH_SUGG_LIMIT:
		hasMore = True
	#
	return [results, hasMore]
def lookupNodeInfo(name, useReducedTree):
	cur = dbCon.cursor()
	# Get node-object info
	temp = lookupNodes([name], useReducedTree)
	nodeObj = temp[name] if name in temp else None
	# Get node desc
	descData = None
	match = re.fullmatch(r"\[(.+) \+ (.+)]", name)
	if match == None:
		query = "SELECT desc, redirected, wiki_id, from_dbp from descs WHERE descs.name = ?"
		row = cur.execute(query, (name,)).fetchone()
		if row != None:
			descData = {"text": row[0], "fromRedirect": row[1] == 1, "wikiId": row[2], "fromDbp": row[3] == 1}
	else:
		# Get descs for compound-node element
		descData = [None, None]
		query = "SELECT name, desc, redirected, wiki_id, from_dbp from descs WHERE descs.name IN (?, ?)"
		for row in cur.execute(query, match.group(1,2)):
			if row[0] == match.group(1):
				descData[0] = {"text": row[1], "fromRedirect": row[2] == 1, "wikiId": row[3], "fromDbp": row[4] == 1}
			else:
				descData[1] = {"text": row[1], "fromRedirect": row[2] == 1, "wikiId": row[3], "fromDbp": row[4] == 1}
	# Get img info
	imgData = None
	if nodeObj != None:
		if isinstance(nodeObj["imgName"], str):
			otolId = nodeObj["imgName"][:-4] # Convert filename excluding .jpg suffix
			print(otolId)
			query = "SELECT images.id, images.src, url, license, artist, credit FROM" \
				" node_imgs INNER JOIN images ON node_imgs.img_id = images.id AND node_imgs.src = images.src" \
				" WHERE node_imgs.id = ?"
			(imgId, imgSrc, url, license, artist, credit) = cur.execute(query, (otolId,)).fetchone()
			imgData = {"imgId": imgId, "imgSrc": imgSrc,
				"url": url, "license": license, "artist": artist, "credit": credit}
		elif isinstance(nodeObj["imgName"], list):
			# Get info for compound-image parts
			imgData = [None, None]
			idsToLookup = [n[:-4] for n in nodeObj["imgName"] if n != None]
			query = "SELECT images.img_id, images.src, url, license, artist, credit FROM" \
				" node_imgs INNER JOIN images ON node_imgs.img_id = images.id AND node_imgs.src = images.src" \
				" WHERE node_imgs.id IN ({})".format(",".join(["?"] * len(idsToLookup)))
			for (imgId, imgSrc, url, license, artist, credit) in cur.execute(query, idsToLookup):
				imgData = {"imgId": imgId, "imgSrc": imgSrc,
					"url": url, "license": license, "artist": artist, "credit": credit}
				imgName1 = nodeObj["imgName"][0]
				if imgName1 != None and str(imgId) == imgName1[:-4]:
					imgData[0] = imgData
				else:
					imgData[1] = imgData
	#
	return {"descData": descData, "imgData": imgData, "nodeObj": nodeObj}

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
				nodeObjs = lookupNodes([name], useReducedTree)
				if len(nodeObjs) > 0:
					nodeObj = nodeObjs[name]
					childNodeObjs = lookupNodes(nodeObj["children"], useReducedTree)
					childNodeObjs[name] = nodeObj
					self.respondJson(childNodeObjs)
					return
			elif reqType == "chain":
				results = {}
				ranOnce = False
				while True:
					# Get node
					nodeObjs = lookupNodes([name], useReducedTree)
					if len(nodeObjs) == 0:
						if not ranOnce:
							self.respondJson(results)
							return
						print(f"ERROR: Parent-chain node {name} not found", file=sys.stderr)
						break
					nodeObj = nodeObjs[name]
					results[name] = nodeObj
					# Conditionally add children
					if not ranOnce:
						ranOnce = True
					else:
						childNamesToAdd = []
						for childName in nodeObj["children"]:
							if childName not in results:
								childNamesToAdd.append(childName)
						childNodeObjs = lookupNodes(childNamesToAdd, useReducedTree)
						results.update(childNodeObjs)
					# Check if root
					if nodeObj["parent"] == None:
						self.respondJson(results)
						return
					else:
						name = nodeObj["parent"]
			elif reqType == "search":
				self.respondJson(lookupName(name, useReducedTree))
				return
			elif reqType == "info":
				self.respondJson(lookupNodeInfo(name, useReducedTree))
				return
		self.send_response(404)
		self.end_headers()
		self.end_headers()
	def respondJson(self, val):
		self.send_response(200)
		self.send_header("Content-type", "application/json")
		self.end_headers()
		self.wfile.write(json.dumps(val).encode("utf-8"))

server = HTTPServer((hostname, port), DbServer)
print(f"Server started at http://{hostname}:{port}")
try:
	server.serve_forever()
except KeyboardInterrupt:
	pass
server.server_close()
dbCon.close()
print("Server stopped")
