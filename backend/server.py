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
usageInfo += "If type1 is 'node': Responds with map from names to objects representing node name1 and it's children.\n"
usageInfo += "If type1 is 'chain': Like 'node', but gets nodes from name1 up to the root, and their direct children.\n"
usageInfo += "If type1 is 'search': Responds with a tolnode name that has alt-name name1, or null.\n"
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

# Connect to db, and load spellfix extension
dbCon = sqlite3.connect(dbFile)
# Some functions
def lookupNodes(names, useReducedTree):
	# Get node info
	nodeObjs = {}
	cur = dbCon.cursor()
	nodesTable = "nodes" if not useReducedTree else "r_nodes"
	edgesTable = "edges" if not useReducedTree else "r_edges"
	queryParamStr = ",".join(["?"] * len(names))
	query = "SELECT name, tips FROM {} WHERE name IN ({})".format(nodesTable, queryParamStr)
	for (nodeName, tips) in cur.execute(query, names):
		nodeObjs[nodeName] = {
			"children": [],
			"parent": None,
			"tips": tips,
			"pSupport": False,
			"commonName": None,
			"imgName": None,
		}
	query = "SELECT node, child FROM {} WHERE node IN ({})".format(edgesTable, queryParamStr)
	for (nodeName, childName) in cur.execute(query, names):
		nodeObjs[nodeName]["children"].append(childName)
	query = "SELECT node, child, p_support FROM {} WHERE child IN ({})".format(edgesTable, queryParamStr)
	for (nodeName, childName, pSupport) in cur.execute(query, names):
		nodeObjs[childName]["parent"] = None if nodeName == "" else nodeName
		nodeObjs[childName]["pSupport"] = (pSupport == 1)
	# Get names for image files
	namesForImgs = []
	firstSubnames = {}
	secondSubnames = {}
	for (name, nodeObj) in nodeObjs.items():
		match = re.fullmatch(r"\[(.+) \+ (.+)]", name)
		if match == None:
			namesForImgs.append(name)
		else:
			name1 = match.group(1)
			name2 = match.group(2)
			namesForImgs.extend([name1, name2])
			firstSubnames[name1] = name
			secondSubnames[name2] = name
	# Get image names
	query = "SELECT name, id FROM eol_ids WHERE" \
		" name IN ({})".format(",".join(["?"] * len(namesForImgs)))
	for [n, id] in cur.execute(query, namesForImgs):
		filename = str(id) + ".jpg"
		if not os.path.exists(imgDir + filename):
			continue
		if n in firstSubnames:
			nodeName = firstSubnames[n]
			nodeObjs[nodeName]["imgName"] = filename
		elif n in secondSubnames:
			nodeName = secondSubnames[n]
			if nodeObjs[nodeName]["imgName"] == None:
				nodeObjs[nodeName]["imgName"] = filename
		else:
			nodeObjs[n]["imgName"] = filename
	# Get preferred-name info
	query = "SELECT name, alt_name FROM names WHERE pref_alt = 1 AND name IN ({})".format(queryParamStr)
	for (name, altName) in cur.execute(query, names):
		if altName != name:
			nodeObjs[name]["commonName"] = altName
	#
	return nodeObjs
def getNodeImg(name):
	cur = dbCon.cursor()
	row = cur.execute("SELECT name, id FROM eol_ids WHERE name = ?", (name,)).fetchone()
	if row != None:
		eolId = row[1]
		filename = str(eolId) + ".jpg"
		if os.path.exists(imgDir + filename):
			return filename
	return None
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
	row = cur.execute("SELECT desc, redirected, wiki_id, from_dbp from descs WHERE descs.name = ?", (name,)).fetchone()
	descObj = None
	if row != None:
		descObj = {"text": row[0], "fromRedirect": row[1] == 1, "wikiId": row[2], "fromDbp": row[3] == 1}
	# Get img info
	imgInfo = None
	if nodeObj != None and nodeObj["imgName"] != None:
		eolId = int(nodeObj["imgName"][:-4]) # Convert filename excluding .jpg suffix
		imgInfoQuery = "SELECT eol_id, source_url, license, copyright_owner FROM images WHERE eol_id = ?"
		row = cur.execute(imgInfoQuery, (eolId,)).fetchone()
		imgInfo = {"eolId": row[0], "sourceUrl": row[1], "license": row[2], "copyrightOwner": row[3]}
	#
	return {"descObj": descObj, "imgInfo": imgInfo, "nodeObj": nodeObj}

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
						print("ERROR: Parent-chain node {} not found".format(name), file=sys.stderr)
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
print("Server started at http://{}:{}".format(hostname, port))
try:
	server.serve_forever()
except KeyboardInterrupt:
	pass
server.server_close()
dbCon.close()
print("Server stopped")
