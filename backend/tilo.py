#!/usr/bin/python3

from typing import Iterable, cast
import sys, re
import urllib.parse, sqlite3
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

DB_FILE = 'tol_data/data.db'
DEFAULT_SUGG_LIM = 5
MAX_SUGG_LIM = 50
ROOT_NAME = 'cellular organisms'

# Classes for objects sent as responses (matches lib.ts types in client-side code)
class TolNode:
	""" Used when responding to 'node' and 'chain' requests """
	def __init__(
			self,
			otolId: str | None,
			children: list[str],
			parent: str | None = None,
			tips=0,
			pSupport=False,
			commonName: str | None = None,
			imgName: None | str | tuple[str, str] | tuple[None, str] | tuple[str, None] = None,
			iucn: str | None = None):
		self.otolId = otolId
		self.children = children
		self.parent = parent
		self.tips = tips
		self.pSupport = pSupport
		self.commonName = commonName
		self.imgName = imgName
		self.iucn = iucn
	# Used in unit testing
	def __eq__(self, other):
		return isinstance(other, TolNode) and \
			(self.otolId, set(self.children), self.parent, self.tips, \
				self.pSupport, self.commonName, self.imgName, self.iucn) == \
			(other.otolId, set(other.children), other.parent, other.tips, \
				other.pSupport, other.commonName, other.imgName, other.iucn)
	def __repr__(self):
		return str(self.__dict__)
class SearchSugg:
	""" Represents a search suggestion """
	def __init__(self, name: str, canonicalName: str | None = None, pop=0):
		self.name = name
		self.canonicalName = canonicalName
		self.pop = pop if pop is not None else 0
	# Used in unit testing
	def __eq__(self, other):
		return isinstance(other, SearchSugg) and \
			(self.name, self.canonicalName, self.pop) == (other.name, other.canonicalName, other.pop)
	def __repr__(self):
		return str(self.__dict__)
	def __hash__(self):
		return (self.name, self.canonicalName, self.pop).__hash__()
class SearchSuggResponse:
	""" Sent as responses to 'sugg' requests """
	def __init__(self, searchSuggs: list[SearchSugg], hasMore: bool):
		self.suggs = searchSuggs
		self.hasMore = hasMore
	# Used in unit testing
	def __eq__(self, other):
		return isinstance(other, SearchSuggResponse) and \
			(set(self.suggs), self.hasMore) == (set(other.suggs), other.hasMore)
	def __repr__(self):
		return str(self.__dict__)
class DescInfo:
	""" Represents a node's associated description """
	def __init__(self, text: str, wikiId: int, fromDbp: bool):
		self.text = text
		self.wikiId = wikiId
		self.fromDbp = fromDbp
	# Used in unit testing
	def __eq__(self, other):
		return isinstance(other, DescInfo) and \
			(self.text, self.wikiId, self.fromDbp) == (other.text, other.wikiId, other.fromDbp)
	def __repr__(self):
		return str(self.__dict__)
class ImgInfo:
	""" Represents a node's associated image """
	def __init__(self, id: int, src: str, url: str, license: str, artist: str, credit: str):
		self.id = id
		self.src = src
		self.url = url
		self.license = license
		self.artist = artist
		self.credit = credit
	# Used in unit testing
	def __eq__(self, other):
		return isinstance(other, ImgInfo) and \
			(self.id, self.src, self.url, self.license, self.artist, self.credit) == \
			(other.id, other.src, other.url, other.license, other.artist, other.credit)
	def __repr__(self):
		return str(self.__dict__)
class NodeInfo:
	""" Represents info about a node """
	def __init__(self, tolNode: TolNode, descInfo: DescInfo | None, imgInfo: ImgInfo | None):
		self.tolNode = tolNode
		self.descInfo = descInfo
		self.imgInfo = imgInfo
	# Used in unit testing
	def __eq__(self, other):
		return isinstance(other, NodeInfo) and \
			(self.tolNode, self.descInfo, self.imgInfo) == (other.tolNode, other.descInfo, other.imgInfo)
	def __repr__(self):
		return str(self.__dict__)
class InfoResponse:
	""" Sent as responses to 'info' requests """
	def __init__(self, nodeInfo: NodeInfo, subNodesInfo: tuple[()] | tuple[NodeInfo | None, NodeInfo | None]):
		self.nodeInfo = nodeInfo
		self.subNodesInfo = subNodesInfo
	# Used in unit testing
	def __eq__(self, other):
		return isinstance(other, InfoResponse) and \
			(self.nodeInfo, self.subNodesInfo) == (other.nodeInfo, other.subNodesInfo)
	def __repr__(self):
		return str(self.__dict__)

# For data lookup
def lookupNodes(names: list[str], tree: str, dbCur: sqlite3.Cursor) -> dict[str, TolNode]:
	""" For a set of node names, returns a name-to-TolNode map that describes those nodes """
	# Get node info
	nameToNodes: dict[str, TolNode] = {}
	tblSuffix = getTableSuffix(tree)
	nodesTable = f'nodes_{tblSuffix}'
	edgesTable = f'edges_{tblSuffix}'
	queryParamStr = ','.join(['?'] * len(names))
	query = f'SELECT name, id, tips FROM {nodesTable} WHERE name IN ({queryParamStr})'
	for nodeName, otolId, tips in dbCur.execute(query, names):
		nameToNodes[nodeName] = TolNode(otolId, [], tips=tips)
	# Get child info
	query = f'SELECT parent, child FROM {edgesTable} WHERE parent IN ({queryParamStr})'
	for nodeName, childName in dbCur.execute(query, names):
		nameToNodes[nodeName].children.append(childName)
	# Order children by tips
	for nodeName, node in nameToNodes.items():
		childToTips: dict[str, int] = {}
		query = 'SELECT name, tips FROM {} WHERE name IN ({})'
		query = query.format(nodesTable, ','.join(['?'] * len(node.children)))
		for n, tips in dbCur.execute(query, node.children):
			childToTips[n] = tips
		node.children.sort(key=lambda n: childToTips[n], reverse=True)
	# Get parent info
	query = f'SELECT parent, child, p_support FROM {edgesTable} WHERE child IN ({queryParamStr})'
	for nodeName, childName, pSupport in dbCur.execute(query, names):
		nameToNodes[childName].parent = nodeName
		nameToNodes[childName].pSupport = pSupport == 1
	# Get image names
	idsToNames = {nameToNodes[n].otolId: n for n in nameToNodes.keys()}
	query = f'SELECT {nodesTable}.id from {nodesTable}' \
		f' INNER JOIN node_imgs ON {nodesTable}.name = node_imgs.name' \
		f' WHERE {nodesTable}.id IN ' '({})'.format(','.join(['?'] * len(idsToNames)))
	for (otolId,) in dbCur.execute(query, list(idsToNames.keys())):
		nameToNodes[idsToNames[otolId]].imgName = otolId + '.jpg'
	# Get 'linked' images for unresolved names
	unresolvedNames = [n for n in nameToNodes if nameToNodes[n].imgName is None]
	query = 'SELECT name, otol_ids from linked_imgs WHERE name IN ({})'
	query = query.format(','.join(['?'] * len(unresolvedNames)))
	for name, otolIds in dbCur.execute(query, unresolvedNames):
		if ',' not in otolIds:
			nameToNodes[name].imgName = otolIds + '.jpg'
		else:
			id1, id2 = otolIds.split(',')
			nameToNodes[name].imgName = (
				id1 + '.jpg' if id1 != '' else None,
				id2 + '.jpg' if id2 != '' else None,
			)
	# Get preferred-name info
	query = f'SELECT name, alt_name FROM names WHERE pref_alt = 1 AND name IN ({queryParamStr})'
	for name, altName in dbCur.execute(query, names):
		if name in nameToNodes:
			nameToNodes[name].commonName = altName
	# Get IUCN status
	query = f'SELECT name, iucn FROM node_iucn WHERE name IN ({queryParamStr})'
	for name, iucn in dbCur.execute(query, names):
		if name in nameToNodes:
			nameToNodes[name].iucn = iucn
	#
	return nameToNodes
def lookupSuggs(searchStr: str, suggLimit: int, tree: str, dbCur: sqlite3.Cursor) -> SearchSuggResponse:
	""" For a search string, returns a SearchSuggResponse describing search suggestions """
	hasMore = False
	# Get node names and alt-names, ordering by popularity
	nodesTable = f'nodes_{getTableSuffix(tree)}'
	nameQuery = f'SELECT {nodesTable}.name, node_pop.pop FROM {nodesTable}' \
		f' LEFT JOIN node_pop ON {nodesTable}.name = node_pop.name' \
		f' WHERE {nodesTable}.name LIKE ? AND {nodesTable}.name NOT LIKE "[%"' \
		f' ORDER BY node_pop.pop DESC'
	altNameQuery = f'SELECT alt_name, names.name, pref_alt, node_pop.pop FROM' \
		f' names INNER JOIN {nodesTable} ON names.name = {nodesTable}.name' \
		f' LEFT JOIN node_pop ON {nodesTable}.name = node_pop.name' \
		f' WHERE alt_name LIKE ? ORDER BY node_pop.pop DESC'
	suggs: dict[str, SearchSugg] = {}
	tempLimit = suggLimit + 1 # For determining if 'more suggestions exist'
	# Prefix search
	for altName, nodeName, prefAlt, pop in dbCur.execute(altNameQuery, (searchStr + '%',)):
		if nodeName not in suggs or prefAlt == 1 and suggs[nodeName].canonicalName is not None:
			suggs[nodeName] = SearchSugg(altName, nodeName, pop)
			if len(suggs) == tempLimit:
				break
	if len(suggs) < tempLimit:
		# Prefix search of canonical names
		for nodeName, pop in dbCur.execute(nameQuery, (searchStr + '%',)):
			if nodeName not in suggs:
				suggs[nodeName] = SearchSugg(nodeName, pop=pop)
				if len(suggs) == tempLimit:
					break
	suggList = sorted(suggs.values(), key=lambda x: x.pop, reverse=True)
	# If insufficient results, try substring-search
	if len(suggs) < tempLimit:
		newNames: set[str] = set()
		oldNames = suggs.keys()
		for altName, nodeName, prefAlt, pop in dbCur.execute(altNameQuery, ('%' + searchStr + '%',)):
			if nodeName not in suggs or \
				nodeName not in oldNames and prefAlt == 1 and suggs[nodeName].canonicalName is not None:
				suggs[nodeName] = SearchSugg(altName, nodeName, pop)
				newNames.add(nodeName)
				if len(suggs) == tempLimit:
					break
		if len(suggs) < tempLimit:
			for nodeName, pop in dbCur.execute(nameQuery, ('%' + searchStr + '%',)):
				if nodeName not in suggs:
					suggs[nodeName] = SearchSugg(nodeName, pop=pop)
					newNames.add(nodeName)
					if len(suggs) == tempLimit:
						break
		suggList.extend(sorted([suggs[n] for n in newNames], key=lambda x: x.pop, reverse=True))
	#
	if len(suggList) > suggLimit:
		hasMore = True
	return SearchSuggResponse(suggList[:suggLimit], hasMore)
def lookupInfo(name: str, tree: str, dbCur: sqlite3.Cursor) -> InfoResponse | None:
	""" For a node name, returns a descriptive InfoResponse, or None """
	nodesTable = f'nodes_{getTableSuffix(tree)}'
	# Get node info
	nameToNodes = lookupNodes([name], tree, dbCur)
	tolNode = nameToNodes[name] if name in nameToNodes else None
	if tolNode is None:
		return None
	# Check for compound node
	match = re.fullmatch(r'\[(.+) \+ (.+)]', name)
	subNames = [match.group(1), match.group(2)] if match is not None else []
	if subNames:
		nameToSubNodes = lookupNodes(subNames, tree, dbCur)
		if len(nameToSubNodes) < 2: # Possible when a subname-denoted node has been trimmed away
			subNames = [n if n in nameToSubNodes else None for n in subNames]
		nameToNodes.update(nameToSubNodes)
	namesToLookup = [name] if not subNames else [n for n in subNames if n is not None]
	# Get desc info
	nameToDescInfo: dict[str, DescInfo] = {}
	query = 'SELECT name, desc, wiki_id, from_dbp FROM' \
		' wiki_ids INNER JOIN descs ON wiki_ids.id = descs.wiki_id' \
		' WHERE wiki_ids.name IN ({})'.format(','.join(['?'] * len(namesToLookup)))
	for nodeName, desc, wikiId, fromDbp in dbCur.execute(query, namesToLookup):
		nameToDescInfo[nodeName] = DescInfo(desc, wikiId, fromDbp == 1)
	# Get image info
	nameToImgInfo: dict[str, ImgInfo] = {}
	idsToNames = {cast(str, nameToNodes[n].imgName)[:-4]: n
		for n in namesToLookup if nameToNodes[n].imgName is not None}
	idsToLookup = list(idsToNames.keys()) # Lookup using IDs avoids having to check linked_imgs
	query = f'SELECT {nodesTable}.id, images.id, images.src, url, license, artist, credit FROM' \
		f' {nodesTable} INNER JOIN node_imgs ON {nodesTable}.name = node_imgs.name' \
		f' INNER JOIN images ON node_imgs.img_id = images.id AND node_imgs.src = images.src' \
		f' WHERE {nodesTable}.id IN ' '({})'.format(','.join(['?'] * len(idsToLookup)))
	for id, imgId, imgSrc, url, license, artist, credit in dbCur.execute(query, idsToLookup):
		nameToImgInfo[idsToNames[id]] = ImgInfo(imgId, imgSrc, url, license, artist, credit)
	# Construct response
	nodeInfoObjs = [
		NodeInfo(
			nameToNodes[n],
			nameToDescInfo[n] if n in nameToDescInfo else None,
			nameToImgInfo[n] if n in nameToImgInfo else None
		) if n is not None else None for n in [name] + subNames
	]
	return InfoResponse(
		nodeInfoObjs[0],
		cast(tuple[()] | tuple[NodeInfo | None, NodeInfo | None], nodeInfoObjs[1:]))
def getTableSuffix(tree: str) -> str:
	""" converts a reduced-tree descriptor into a sql-table-suffix """
	return 't' if tree == 'trimmed' else 'i' if tree == 'images' else 'p'

def handleReq(dbFile: str, environ: dict[str, str]) -> None | dict[str, TolNode] | SearchSuggResponse | InfoResponse:
	""" Queries the database, and constructs a response object """
	# Open db
	dbCon = sqlite3.connect(dbFile)
	dbCur = dbCon.cursor()
	# Get query params
	queryStr = environ['QUERY_STRING'] if 'QUERY_STRING' in environ else ''
	queryDict = urllib.parse.parse_qs(queryStr)
	# Set vars from params
	name = queryDict['name'][0] if 'name' in queryDict else None
	if name is None: # Get root node
		name = ROOT_NAME # Hard-coding this is significantly faster (in testing, querying could take 0.5 seconds)
		#query = 'SELECT name FROM nodes LEFT JOIN edges ON nodes.name = edges.child WHERE edges.parent IS NULL LIMIT 1'
		#(name,) = dbCur.execute(query).fetchone()
	reqType = queryDict['type'][0] if 'type' in queryDict else None
	tree = queryDict['tree'][0] if 'tree' in queryDict else 'images'
	# Check for valid 'tree'
	if tree is not None and re.fullmatch(r'trimmed|images|picked', tree) is None:
		return None
	# Get data of requested type
	if reqType == 'node':
		toroot = queryDict['toroot'][0] == '1' if 'toroot' in queryDict else False
		if not toroot:
			tolNodes = lookupNodes([name], tree, dbCur)
			if tolNodes:
				tolNode = tolNodes[name]
				childNodeObjs = lookupNodes(tolNode.children, tree, dbCur)
				childNodeObjs[name] = tolNode
				return childNodeObjs
		else:
			# Get ancestors to skip inclusion of
			nodesToSkip: set[str] = set()
			nodeName = queryDict['excl'][0] if 'excl' in queryDict else None
			if nodeName is not None:
				edgesTable = f'edges_{getTableSuffix(tree)}'
				while True:
					row = dbCur.execute(f'SELECT parent FROM {edgesTable} WHERE child = ?', (nodeName,)).fetchone()
					if row is None:
						break
					parent = row[0]
					nodesToSkip.add(parent)
					nodeName = parent
			#
			results: dict[str, TolNode] = {}
			ranOnce = False
			while True:
				# Get node
				tolNodes = lookupNodes([name], tree, dbCur)
				if not tolNodes:
					if not ranOnce:
						return results
					print(f'ERROR: Parent-chain node {name} not found', file=sys.stderr)
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
				if tolNode.parent is None or tolNode.parent in nodesToSkip:
					return results
				else:
					name = tolNode.parent
	elif reqType == 'sugg':
		# Check for suggestion-limit
		suggLimit: int
		invalidLimit = False
		try:
			suggLimit = int(queryDict['limit'][0]) if 'limit' in queryDict else DEFAULT_SUGG_LIM
			if suggLimit <= 0 or suggLimit > MAX_SUGG_LIM:
				invalidLimit = True
		except ValueError:
			invalidLimit = True
			print(f'INFO: Invalid limit {suggLimit}', file=sys.stderr)
		# Get search suggestions
		if not invalidLimit:
			return lookupSuggs(name, suggLimit, tree, dbCur)
	elif reqType == 'info':
		infoResponse = lookupInfo(name, tree, dbCur)
		if infoResponse is not None:
			return infoResponse
	# On failure, provide empty response
	return None
def application(environ: dict[str, str], start_response) -> Iterable[bytes]:
	""" Entry point for the WSGI script """
	# Get response object
	val = handleReq(DB_FILE, environ)
	# Construct response
	data = jsonpickle.encode(val, unpicklable=False).encode()
	headers = [('Content-type', 'application/json')]
	if 'HTTP_ACCEPT_ENCODING' in environ and 'gzip' in environ['HTTP_ACCEPT_ENCODING']:
		if len(data) > 100:
			data = gzip.compress(data, compresslevel=5)
			headers.append(('Content-encoding', 'gzip'))
	headers.append(('Content-Length', str(len(data))))
	start_response('200 OK', headers)
	return [data]
