#!/usr/bin/python3

import sys, re
import csv, sqlite3

vnamesFile = "eol/vernacular_names.csv"
dbFile = "data.db"

# Read in vernacular-names data
	# Note: Canonical-names may have multiple pids
	# Note: A canonical-name's associated pids might all have other associated names
nameToPids = {}
pidToNames = {}
canonicalNameToPids = {}
def updateMaps(name, pid, canonical):
	if name not in nameToPids:
		nameToPids[name] = {pid}
	else:
		nameToPids[name].add(pid)
	if canonical:
		if name not in canonicalNameToPids:
			canonicalNameToPids[name] = {pid}
		else:
			canonicalNameToPids[name].add(pid)
	if pid not in pidToNames:
		pidToNames[pid] = {name}
	else:
		pidToNames[pid].add(name)
with open(vnamesFile, newline="") as csvfile:
	reader = csv.reader(csvfile)
	lineNum = 0
	for row in reader:
		lineNum += 1
		if lineNum == 1:
			continue
		pid = int(row[0])
		name1 = re.sub(r"<[^>]+>", "", row[1].lower())
		name2 = row[2].lower()
		# Add to maps
		updateMaps(name1, pid, True)
		updateMaps(name2, pid, False)
# Open db connection
dbCon = sqlite3.connect(dbFile)
cur = dbCon.cursor()
# Create 'names' table
cur.execute("CREATE TABLE names(name TEXT, alt_name TEXT, eol_id INT, PRIMARY KEY(name, alt_name))")
# Iterate through 'nodes' table, resolving to canonical-names
usedPids = set()
unresolvedNodeNames = set()
cur2 = dbCon.cursor()
iterationNum = 0
for row in cur2.execute("SELECT name FROM nodes"):
	name = row[0]
	iterationNum += 1
	if iterationNum % 10000 == 0:
		print("Loop 1 iteration {}".format(iterationNum))
	# If name matches a canonical-name, add alt-name entries to 'names' table
	if name in canonicalNameToPids:
		pidToUse = 0
		for pid in canonicalNameToPids[name]:
			if pid not in usedPids:
				pidToUse = pid
				break
		if pidToUse > 0:
			usedPids.add(pidToUse)
			altNames = {name}
			for n in pidToNames[pidToUse]:
				altNames.add(n)
			for n in altNames:
				cur.execute("INSERT INTO names VALUES (?, ?, ?)", (name, n, pidToUse))
	elif name in nameToPids:
		unresolvedNodeNames.add(name)
# Iterate through unresolved nodes, resolving to vernacular-names
iterationNum = 0
for name in unresolvedNodeNames:
	iterationNum += 1
	if iterationNum % 10000 == 0:
		print("Loop 2 iteration {}".format(iterationNum))
	# Add alt-name entries to 'names' table for first corresponding pid
	pidToUse = 0
	for pid in nameToPids[name]:
		if pid not in usedPids:
			pidToUse = pid
			break
	if pidToUse > 0:
		usedPids.add(pidToUse)
		altNames = {name}
		for n in pidToNames[pidToUse]:
			altNames.add(n)
		for n in altNames:
			cur.execute("INSERT INTO names VALUES (?, ?, ?)", (name, n, pidToUse))
dbCon.commit()
dbCon.close()
