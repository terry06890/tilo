#!/usr/bin/python3

import sys, re

usageInfo =  f"usage: {sys.argv[0]}\n"
usageInfo += "Reads, from stdin, tab-indented lines representing trees, and outputs corresponding JSON.\n"

if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

lineNum = 0
trees = [] #each node is a pair holding a name and an array of child nodes
nodeList = []
while True: 
	#read line
	line = sys.stdin.readline()
	if line == "": break
	line = line.rstrip()
	lineNum += 1
	#create node
	match = re.match(r"^\t*", line)
	indent = len(match.group())
	newNode = [line[indent:], []]
	#add node
	if indent == len(nodeList): #sibling or new tree
		if len(nodeList) == 0:
			nodeList.append(newNode)
			trees.append(newNode)
		else:
			nodeList[-1] = newNode
			if len(nodeList) == 1:
				trees[-1][1].append(newNode)
			else:
				nodeList[-2][1].append(newNode)
	elif indent == len(nodeList) + 1: #direct child
		if len(nodeList) == 0:
			print(f"ERROR: Child without preceding root (line {lineNum})")
			sys.exit(1)
		nodeList.append(newNode)
		nodeList[-2][1].append(newNode)
	elif indent < len(nodeList): #ancestor sibling or new tree
		nodeList = nodeList[:indent]
		if len(nodeList) == 0:
			nodeList.append(newNode)
			trees.append(newNode)
		else:
			nodeList[-1] = newNode
			if len(nodeList) == 1:
				trees[-1][1].append(newNode)
			else:
				nodeList[-2][1].append(newNode)
	else:
		print(f"ERROR: Child with invalid relative indent (line {lineNum})")
		sys.exit(1)
#print as JSON
if len(trees) > 1:
	print("[")
def printNode(node, indent):
	if len(node[1]) == 0:
		print(indent + "{\"name\": \"" + node[0] + "\"}", end="")
	else:
		print(indent + "{\"name\": \"" + node[0] + "\", \"children\": [")
		for i in range(len(node[1])):
			printNode(node[1][i], indent + "\t")
			if i < len(node[1])-1:
				print(",", end="")
			print()
		print(indent + "]}", end="")
for i in range(len(trees)):
	printNode(trees[i], "")
	if i < len(trees)-1:
		print(",", end="")
	print()
if len(trees) > 1:
	print("]")
