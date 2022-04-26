#!/usr/bin/python3

import sys, re, sqlite3, json
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

hostname = "localhost"
port = 8000
dbFile = "data/data.db"
tolnodeReqDepth = 1
	# For a /node?name=name1 request, respond with name1's node, and descendent nodes in a subtree to some depth > 0

usageInfo =  f"usage: {sys.argv[0]}\n"
usageInfo += "Starts a server that listens for GET requests to http://" + hostname + ":" + str(port) + ".\n"
usageInfo += "Responds to path+query /data/type1?name=name1 with JSON data.\n"
usageInfo += "\n"
usageInfo += "If type1 is 'node': \n"
usageInfo += "    Responds with a map from names to node objects, representing\n"
usageInfo += "    nodes name1, and child nodes up to depth " + str(tolnodeReqDepth) + ".\n"
usageInfo += "If type1 is 'children': Like 'node', but excludes node name1.\n"
usageInfo += "If type1 is 'chain': Like 'node', but gets nodes from name1 up to the root, and their direct children.\n"
usageInfo += "If type1 is 'search': Responds with a tolnode name that has alt-name name1, or null.\n"

dbCon = sqlite3.connect(dbFile)
def lookupNode(name):
	cur = dbCon.cursor()
	cur.execute("SELECT name, data FROM nodes WHERE name = ?", (name,))
	row = cur.fetchone()
	return row[1] if row != None else None
def lookupName(name):
	cur = dbCon.cursor()
	cur.execute("SELECT name, alt_name FROM names WHERE alt_name = ?", (name,))
	row = cur.fetchone()
	return json.dumps(row[0]) if row != None else None

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
			print(name)
			# Check query string
			if reqType == "node":
				nodeJson = lookupNode(name)
				if nodeJson != None:
					results = []
					getResultsUntilDepth(name, nodeJson, tolnodeReqDepth, results)
					self.respondJson(nodeResultsToJSON(results))
					return
			elif reqType == "children":
				nodeJson = lookupNode(name)
				if nodeJson != None:
					obj = json.loads(nodeJson)
					results = []
					for childName in obj["children"]:
						nodeJson = lookupNode(childName)
						if nodeJson != None:
							getResultsUntilDepth(childName, nodeJson, tolnodeReqDepth, results)
					self.respondJson(nodeResultsToJSON(results))
					return
			elif reqType == "chain":
				results = []
				ranOnce = False
				while True:
					jsonResult = lookupNode(name)
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
							jsonResult = lookupNode(childName)
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
			elif reqType == "search":
				nameJson = lookupName(name)
				if nameJson != None:
					self.respondJson(nameJson)
					return
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
			childJson = lookupNode(childName)
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
