#!/usr/bin/python3

import sys, re, sqlite3, json
import os.path
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

hostname = "localhost"
port = 8000
dbFile = "data/data.db"
imgDir = "../public/img/"
NODE_REQ_DEPTH = 1
	# For a /node?name=name1 request, respond with name1's node, and descendent nodes in a subtree to some depth > 0
SEARCH_SUGG_LIMIT = 5

usageInfo =  f"usage: {sys.argv[0]}\n"
usageInfo += "Starts a server that listens for GET requests to http://" + hostname + ":" + str(port) + ".\n"
usageInfo += "Responds to path+query /data/type1?name=name1 with JSON data.\n"
usageInfo += "\n"
usageInfo += "If type1 is 'node': \n"
usageInfo += "    Responds with a map from names to node objects, representing\n"
usageInfo += "    nodes name1, and child nodes up to depth " + str(NODE_REQ_DEPTH) + ".\n"
usageInfo += "If type1 is 'children': Like 'node', but excludes node name1.\n"
usageInfo += "If type1 is 'chain': Like 'node', but gets nodes from name1 up to the root, and their direct children.\n"
usageInfo += "If type1 is 'search': Responds with a tolnode name that has alt-name name1, or null.\n"
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

# Connect to db, and load spellfix extension
dbCon = sqlite3.connect(dbFile)
dbCon.enable_load_extension(True)
dbCon.load_extension('./data/spellfix')
# Some functions
def lookupNode(name):
	# Get from db
	cur = dbCon.cursor()
	row = cur.execute("SELECT name, children, parent, tips, p_support FROM nodes WHERE name = ?", (name,)).fetchone()
	if row == None:
		return None
	nodeObj = {
		"children": json.loads(row[1]),
		"parent": None if row[2] == "" else row[2],
		"tips": row[3],
		"pSupport": True if row[4] == 1 else False,
	}
	# Check for image file
	match = re.fullmatch(r"\[(.+) \+ (.+)]", name)
	if match == None:
		nodeObj["img"] = nodeNameToFile(name, cur)
	else:
		nodeObj["img"] = nodeNameToFile(match.group(1), cur)
		if nodeObj["img"] == None:
			nodeObj["img"] = nodeNameToFile(match.group(2), cur)
	#
	return nodeObj;
def nodeNameToFile(name, cur):
	row = cur.execute("SELECT name, id FROM eol_ids WHERE name = ?", (name,)).fetchone()
	if row == None:
		return None
	eolId = row[1]
	filename = str(eolId) + ".jpg"
	if not os.path.exists(imgDir + filename):
		return None
	row = cur.execute(
		"SELECT eol_id, source_url, license, copyright_owner FROM images WHERE eol_id = ?", (eolId,)).fetchone()
	if row == None:
		print("ERROR: No 'images' entry for image file {}".format(imgDir + filename), file=sys.stderr)
		return None
	[eolId, sUrl, license, cOwner] = row
	return {"filename": filename, "eolId": eolId, "sourceUrl": sUrl, "license": license, "copyrightOwner": cOwner}
def lookupName(name):
	cur = dbCon.cursor()
	results = []
	hasMore = False
	#for row in cur.execute(
	#	"SELECT DISTINCT name, alt_name FROM names WHERE alt_name LIKE ? LIMIT ?",
	#	(name, SEARCH_SUGG_LIMIT)):
	#	results.append({"name": row[0], "altName": row[1]})
	#for row in cur.execute(
	#	"SELECT DISTINCT names.name, names.alt_name, nodes.tips FROM" \
	#		" names INNER JOIN nodes ON names.name = nodes.name " \
	#		" WHERE alt_name LIKE ? ORDER BY nodes.tips DESC LIMIT ?",
	#	(name, SEARCH_SUGG_LIMIT)):
	#	results.append({"name": row[0], "altName": row[1]})
	for row in cur.execute(
		"SELECT word, alt_name, name FROM" \
			" spellfix_alt_names INNER JOIN names ON alt_name = word" \
			" WHERE word MATCH ? LIMIT ?",
		(name, SEARCH_SUGG_LIMIT)):
		results.append({"name": row[2], "altName": row[0]})
	if len(results) > SEARCH_SUGG_LIMIT:
		hasMore = True
		del results[-1]
	return json.dumps([results, hasMore])
def lookupDesc(name):
	cur = dbCon.cursor()
	row = cur.execute("SELECT desc, redirected from descs WHERE descs.name = ?", (name,)).fetchone()
	return json.dumps([row[0], row[1] == 1] if row != None else None)

class DbServer(BaseHTTPRequestHandler):
	def do_GET(self):
		# Parse URL
		urlParts = urllib.parse.urlparse(self.path)
		path = urllib.parse.unquote(urlParts.path)
		queryDict = urllib.parse.parse_qs(urlParts.query)
		# Check first element of path
		match = re.match(r"/([^/]+)/(.+)", path)
		if match != None and match.group(1) == "data" and "name" in queryDict:
			reqType = match.group(2)
			name = queryDict["name"][0]
			# Check query string
			if reqType == "node":
				nodeObj = lookupNode(name)
				if nodeObj != None:
					results = {}
					getResultsUntilDepth(name, nodeObj, NODE_REQ_DEPTH, results)
					self.respondJson(json.dumps(results))
					return
			elif reqType == "children":
				nodeObj = lookupNode(name)
				if nodeObj != None:
					results = {}
					for childName in nodeObj["children"]:
						nodeObj = lookupNode(childName)
						if nodeObj != None:
							getResultsUntilDepth(childName, nodeObj, NODE_REQ_DEPTH, results)
					self.respondJson(json.dumps(results))
					return
			elif reqType == "chain":
				results = {}
				ranOnce = False
				while True:
					# Get node
					nodeObj = lookupNode(name)
					if nodeObj == None:
						if not ranOnce:
							self.respondJson(json.dumps(results))
							return
						print("ERROR: Parent-chain node {} not found".format(name), file=sys.stderr)
						break
					results[name] = nodeObj
					# Conditionally add children
					if not ranOnce:
						ranOnce = True
					else:
						internalFail = False
						for childName in nodeObj["children"]:
							if childName in results:
								continue
							nodeObj = lookupNode(childName)
							if nodeObj == None:
								print("ERROR: Parent-chain-child node {} not found".format(name), file=sys.stderr)
								internalFail = True
								break
							results[childName] = nodeObj
						if internalFail:
							break
					# Check if root
					if nodeObj["parent"] == None:
						self.respondJson(json.dumps(results))
						return
					else:
						name = nodeObj["parent"]
			elif reqType == "search":
				self.respondJson(lookupName(name))
				return
			elif reqType == "desc":
				self.respondJson(lookupDesc(name))
				return
		self.send_response(404)
		self.end_headers()
		self.end_headers()
	def respondJson(self, jsonStr):
		self.send_response(200)
		self.send_header("Content-type", "application/json")
		self.end_headers()
		self.wfile.write(jsonStr.encode("utf-8"))
def getResultsUntilDepth(name, nodeObj, depth, results):
	"""Given a node [name, nodeObj] pair, adds child node pairs to 'results', up until 'depth'"""
	results[name] = nodeObj
	if depth > 0:
		for childName in nodeObj["children"]:
			childObj = lookupNode(childName)
			if childObj != None:
				getResultsUntilDepth(childName, childObj, depth-1, results)

server = HTTPServer((hostname, port), DbServer)
print("Server started at http://{}:{}".format(hostname, port))
try:
	server.serve_forever()
except KeyboardInterrupt:
	pass
server.server_close()
dbCon.close()
print("Server stopped")
