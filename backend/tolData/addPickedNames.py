#!/usr/bin/python3

import sys
import sqlite3

usageInfo = f"""
Usage: {sys.argv[0]}

Reads alt-name data from a file, and adds it to the database's 'names' table.
"""
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

dbFile = "data.db"
pickedNamesFile = "pickedNames.txt"

print("Opening database")
dbCon = sqlite3.connect(dbFile)
dbCur = dbCon.cursor()

print("Iterating through picked-names file")
with open(pickedNamesFile) as file:
	for line in file:
		# Get record data
		nodeName, altName, prefAlt = line.lower().rstrip().split("|")
		prefAlt = int(prefAlt)
		# Check whether there exists a node with the name
		row = dbCur.execute("SELECT name from nodes where name = ?", (nodeName,)).fetchone()
		if row == None:
			print(f"ERROR: No node with name \"{nodeName}\" exists")
			break
		# Remove any existing preferred-alt status
		if prefAlt == 1:
			query = "SELECT name, alt_name FROM names WHERE name = ? AND pref_alt = 1"
			row = dbCur.execute(query, (nodeName,)).fetchone()
			if row != None and row[1] != altName:
				print(f"Removing pref-alt status from alt-name {row[1]} for {nodeName}")
				dbCur.execute("UPDATE names SET pref_alt = 0 WHERE name = ? AND alt_name = ?", row)
		# Check for an existing record
		if nodeName == altName:
			continue
		query = "SELECT name, alt_name, pref_alt FROM names WHERE name = ? AND alt_name = ?"
		row = dbCur.execute(query, (nodeName, altName)).fetchone()
		if row == None:
			print(f"Adding record for alt-name {altName} for {nodeName}")
			dbCur.execute("INSERT INTO names VALUES (?, ?, ?, 'picked')", (nodeName, altName, prefAlt))
		else:
			# Update existing record
			if row[2] != prefAlt:
				print(f"Updating record for alt-name {altName} for {nodeName}")
				dbCur.execute("UPDATE names SET pref_alt = ?, src = 'picked' WHERE name = ? AND alt_name = ?",
					(prefAlt, nodeName, altName))

print("Closing database")
dbCon.commit()
dbCon.close()
