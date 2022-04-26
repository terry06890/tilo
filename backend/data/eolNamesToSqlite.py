#!/usr/bin/python3

import sys, re
import csv, sqlite3

vnamesFile = "eol/vernacular_names.csv"
dbFile = "data.db"

# Read in vernacular-names data
nameToPids = {}
pidToNames = {}
def updateMaps(name, pid):
	if name not in nameToPids:
		nameToPids[name] = {pid}
	elif pid not in nameToPids[name]:
		nameToPids[name].add(pid)
	if pid not in pidToNames:
		pidToNames[pid] = {name}
	elif name not in pidToNames[pid]:
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
		updateMaps(name1, pid)
		updateMaps(name2, pid)
# Open db connection
dbCon = sqlite3.connect(dbFile)
cur = dbCon.cursor()
# Create 'names' table
cur.execute("CREATE TABLE names(name TEXT, alt_name TEXT, eol_id INT, PRIMARY KEY(name, alt_name))")
# Iterate through 'nodes' table
cur2 = dbCon.cursor()
iterationNum = 0
for row in cur2.execute("SELECT name FROM nodes"):
	name = row[0]
	iterationNum += 1
	if iterationNum % 10000 == 0:
		print("Iteration {}".format(iterationNum))
	# If name matches a vernacular-names name, add alt-name entries to the 'names' table
	if name in nameToPids:
		altNames = {name}
		for pid in nameToPids[name]:
			for n in pidToNames[pid]:
				altNames.add(n)
		for n in altNames:
			cur.execute("INSERT INTO names VALUES (?, ?, ?)", (name, n, pid))
dbCon.commit()
dbCon.close()
