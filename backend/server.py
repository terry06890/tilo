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
usageInfo += "\n"
usageInfo += "If type1 is 'node': Responds with map from names to objects representing node name1 and it's children.\n"
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
def lookupNodes(names):
	nodeObjs = {}
	cur = dbCon.cursor()
	query = "SELECT name, children, parent, tips, p_support FROM nodes WHERE" \
		" name IN ({})".format(",".join(["?"] * len(names)))
	for row in cur.execute(query, names):
		name = row[0]
		nodeObj = {
			"children": json.loads(row[1]),
			"parent": None if row[2] == "" else row[2],
			"tips": row[3],
			"pSupport": True if row[4] == 1 else False,
		}
		# Check for image file
		match = re.fullmatch(r"\[(.+) \+ (.+)]", name)
		if match == None:
			nodeObj["imgName"] = getNodeImg(name)
		else:
			nodeObj["imgName"] = getNodeImg(match.group(1))
			if nodeObj["imgName"] == None:
				nodeObj["imgName"] = getNodeImg(match.group(2))
		# Add node object
		nodeObjs[name] = nodeObj
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
	return [results, hasMore]
def lookupNodeInfo(name):
	cur = dbCon.cursor()
	# Get node desc
	row = cur.execute("SELECT desc, redirected from descs WHERE descs.name = ?", (name,)).fetchone()
	desc = {"text": row[0], "fromRedirect": row[1] == 1} if row != None else None
	# Get img info
	imgInfoQuery = "SELECT eol_id, source_url, license, copyright_owner FROM" \
		" images INNER JOIN eol_ids ON images.eol_id = eol_ids.id WHERE eol_ids.name = ?"
	row = cur.execute(imgInfoQuery, (name,)).fetchone()
	imgInfo = None
	if row != None:
		imgInfo = {"eolId": row[0], "sourceUrl": row[1], "license": row[2], "copyrightOwner": row[3]}
	#
	return {"desc": desc, "imgInfo": imgInfo}

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
				nodeObjs = lookupNodes([name])
				if len(nodeObjs) > 0:
					nodeObj = nodeObjs[name]
					childNodeObjs = lookupNodes(nodeObj["children"])
					childNodeObjs[name] = nodeObj
					self.respondJson(childNodeObjs)
					return
			elif reqType == "chain":
				results = {}
				ranOnce = False
				while True:
					# Get node
					nodeObjs = lookupNodes([name])
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
						childNodeObjs = lookupNodes(childNamesToAdd)
						results.update(childNodeObjs)
					# Check if root
					if nodeObj["parent"] == None:
						self.respondJson(results)
						return
					else:
						name = nodeObj["parent"]
			elif reqType == "search":
				self.respondJson(lookupName(name))
				return
			elif reqType == "info":
				self.respondJson(lookupNodeInfo(name))
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
