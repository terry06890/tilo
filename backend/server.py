#!/usr/bin/python3

import sys, re, sqlite3, json
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

hostname = "localhost"
port = 8000
dbFile = "data/otol.db"
tolnodeReqDepth = 2
	# For a /tolnode/name1 request, respond with name1's node, and descendent nodes in a subtree to some depth
	# A depth of 0 means only respond with one node

usageInfo =  f"usage: {sys.argv[0]}\n"
usageInfo += "Starts a server that listens for GET requests to " + hostname + ":" + str(port) + "/tolnode/name1,\n"
usageInfo += "and responds with JSON representing an object mapping names to node objects.\n"
usageInfo += "Normally, the response includes node name1, and child nodes up to depth " + str(tolnodeReqDepth) + ".\n"
usageInfo += "\n"
usageInfo += "A query section ?type=type1 can be used to affect the result.\n"
usageInfo += "If type1 is 'children', the operation acts on node name1's children, and the results combined.\n"
usageInfo += "If type1 is 'chain', the response includes nodes from name1 up to the root, and their direct children.\n"

dbCon = sqlite3.connect(dbFile)
def lookupName(name):
	cur = dbCon.cursor()
	cur.execute("SELECT name, data FROM nodes WHERE name = ?", (name,))
	row = cur.fetchone()
	return row[1] if row != None else None
#def lookupNameLike(name):
#	cur = dbCon.cursor()
#	found = False
#	cur.execute("SELECT name, data FROM nodes WHERE name like ?", ("%{}%".format(name),))
#	rows = cur.fetchall()
#	if len(rows) == 0:
#		return None
#	else:
#		jsonStr = "{"
#		for i in range(len(rows)):
#			jsonStr += json.dumps(rows[i][0]) + ":" + rows[i][1]
#			if i < len(njList) - 1:
#				jsonStr += ","
#		jsonStr += "}"
#		return jsonFromNameJsonList(rows)

class DbServer(BaseHTTPRequestHandler):
	def do_GET(self):
		# Parse URL
		urlParts = urllib.parse.urlparse(self.path)
		path = urllib.parse.unquote(urlParts.path)
		queryDict = urllib.parse.parse_qs(urlParts.query)
		# Check first element of path
		match = re.match(r"/([^/]+)/(.+)", path)
		if match != None:
			reqType = match.group(1)
			if reqType == "tolnode":
				name = match.group(2)
				# Check query string
				if "type" not in queryDict:
					nodeJson = lookupName(name)
					if nodeJson != None:
						results = []
						getResultsUntilDepth(name, nodeJson, tolnodeReqDepth, results)
						self.respondJson(nodeResultsToJSON(results))
						return
				elif queryDict["type"][0] == "children":
					nodeJson = lookupName(name)
					if nodeJson != None:
						obj = json.loads(nodeJson)
						results = []
						for childName in obj["children"]:
							nodeJson = lookupName(childName)
							if nodeJson != None:
								getResultsUntilDepth(childName, nodeJson, tolnodeReqDepth, results)
						self.respondJson(nodeResultsToJSON(results))
						return
				elif queryDict["type"][0] == "chain":
					results = []
					ranOnce = False
					while True:
						jsonResult = lookupName(name)
						if jsonResult == None:
							if ranOnce:
								print("ERROR: Parent-chain node {} not found".format(name), file=sys.stderr)
							break
						results.append([name, jsonResult])
						obj = json.loads(jsonResult)
						# Add children
						if not ranOnce:
							ranOnce = True
						else:
							internalFail = False
							for childName in obj["children"]:
								jsonResult = lookupName(childName)
								if jsonResult == None:
									print("ERROR: Parent-chain-child node {} not found".format(name), file=sys.stderr)
									internalFail = True
									break
								results.append([childName, jsonResult])
							if internalFail:
								break
						# Check if root
						if obj["parent"] == None:
							self.respondJson(nodeResultsToJSON(results))
							return
						else:
							name = obj["parent"]
		self.send_response(404)
		self.end_headers()
		self.end_headers()
	def respondJson(self, jsonStr):
		self.send_response(200)
		self.send_header("Content-type", "application/json")
		self.end_headers()
		self.wfile.write(jsonStr.encode("utf-8"))
def getResultsUntilDepth(name, nodeJson, depth, results):
	"""Given a node [name, nodeJson] pair, adds child node pairs to 'results', up until 'depth'"""
	results.append([name, nodeJson])
	if depth > 0:
		obj = json.loads(nodeJson)
		for childName in obj["children"]:
			childJson = lookupName(childName)
			if childJson != None:
				getResultsUntilDepth(childName, childJson, depth-1, results)
def nodeResultsToJSON(results):
	"""Given a list of [name, nodeJson] pairs, returns a representative JSON string"""
	jsonStr = "{"
	for i in range(len(results)):
		jsonStr += json.dumps(results[i][0]) + ":" + results[i][1]
		if i < len(results) - 1:
			jsonStr += ","
	jsonStr += "}"
	return jsonStr

server = HTTPServer((hostname, port), DbServer)
print("Server started at http://{}:{}".format(hostname, port))
try:
	server.serve_forever()
except KeyboardInterrupt:
	pass
server.server_close()
dbCon.close()
print("Server stopped")
