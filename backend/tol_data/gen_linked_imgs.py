#!/usr/bin/python3

"""
Look for nodes without images in the database, and tries to
associate them with images from their children
"""

import argparse
import re
import sqlite3

DB_FILE = 'data.db'

COMPOUND_NAME_REGEX = re.compile(r'\[(.+) \+ (.+)]')
UP_PROPAGATE_COMPOUND_IMGS = False

def genData(dbFile: str) -> None:
	print('Opening database')
	dbCon = sqlite3.connect(dbFile)
	dbCur = dbCon.cursor()
	dbCur.execute('CREATE TABLE linked_imgs (name TEXT PRIMARY KEY, otol_ids TEXT)')

	print('Getting nodes with images')
	nodeToUsedId: dict[str, str] = {} # Maps name of node to otol ID of node to use image for
	query = 'SELECT nodes.name, nodes.id FROM nodes INNER JOIN node_imgs ON nodes.name = node_imgs.name'
	for name, otolId in dbCur.execute(query):
		nodeToUsedId[name] = otolId
	print(f'Found {len(nodeToUsedId)}')

	print('Getting node depths')
	nodeToDepth: dict[str, int] = {}
	maxDepth = 0
	nodeToParent: dict[str, str | None] = {} # Maps name of node to name of parent
	for nodeName in nodeToUsedId.keys():
		nodeChain = [nodeName]
		lastDepth = 0

		# Add ancestors
		while True:
			row = dbCur.execute('SELECT parent FROM edges WHERE child = ?', (nodeName,)).fetchone()
			if row is None:
				nodeToParent[nodeName] = None
				break
			nodeToParent[nodeName] = row[0]
			nodeName = row[0]
			nodeChain.append(nodeName)
			if nodeName in nodeToDepth:
				lastDepth = nodeToDepth[nodeName]
				break

		# Add depths
		for i in range(len(nodeChain)):
			nodeToDepth[nodeChain[-i-1]] = i + lastDepth
		maxDepth = max(maxDepth, lastDepth + len(nodeChain) - 1)

	print('Finding ancestors to give linked images')
	depthToNodes: dict[int, list[str]] = {depth: [] for depth in range(maxDepth + 1)}
	for nodeName, depth in nodeToDepth.items():
		depthToNodes[depth].append(nodeName)
	parentToCandidate: dict[str, tuple[str, int]] = {} # Maps parent node name to candidate child name and tips-val
	iterNum = 0
	for depth in range(maxDepth, -1, -1):
		for node in depthToNodes[depth]:
			iterNum += 1
			if iterNum % 1e4 == 0:
				print(f'At iteration {iterNum}')
			#
			if node in parentToCandidate:
				nodeToUsedId[node] = nodeToUsedId[parentToCandidate[node][0]]
				dbCur.execute('INSERT INTO linked_imgs VALUES (?, ?)', (node, nodeToUsedId[node]))
			parent = nodeToParent[node]
			if parent is not None and parent not in nodeToUsedId:
				(tips,) = dbCur.execute('SELECT tips FROM nodes WHERE name == ?', (node,)).fetchone()
				if parent not in parentToCandidate or parentToCandidate[parent][1] < tips:
					parentToCandidate[parent] = (node, tips)

	print('Replacing linked-images for compound nodes')
	for iterNum, node in enumerate(parentToCandidate.keys(), 1):
		if iterNum % 1e4 == 0:
			print(f'At iteration {iterNum}')

		match = COMPOUND_NAME_REGEX.fullmatch(node)
		if match is not None:
			# Replace associated image with subname images
			subName1, subName2 = match.group(1,2)
			otolIdPair = ['', '']
			if subName1 in nodeToUsedId:
				otolIdPair[0] = nodeToUsedId[subName1]
			if subName2 in nodeToUsedId:
				otolIdPair[1] = nodeToUsedId[subName2]

			# Use no image if both subimages not found
			if otolIdPair[0] == '' and otolIdPair[1] == '':
				dbCur.execute('DELETE FROM linked_imgs WHERE name = ?', (node,))
				continue

			# Add to db
			dbCur.execute('UPDATE linked_imgs SET otol_ids = ? WHERE name = ?', (','.join(otolIdPair), node))

			# Possibly repeat operation upon parent/ancestors
			if UP_PROPAGATE_COMPOUND_IMGS:
				while True:
					parent = nodeToParent[node]
					if parent is not None:
						(tips,) = dbCur.execute('SELECT tips from nodes WHERE name = ?', (node,)).fetchone()
						if parent in parentToCandidate and parentToCandidate[parent][1] <= tips:
							# Replace associated image
							dbCur.execute(
								'UPDATE linked_imgs SET otol_ids = ? WHERE name = ?', (','.join(otolIdPair), parent))
							node = parent
							continue
					break

	print('Closing database')
	dbCon.commit()
	dbCon.close()

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.parse_args()

	genData(DB_FILE)
