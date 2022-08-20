#!/usr/bin/python3

import sys, re, os
import html, csv, sqlite3

import argparse
parser = argparse.ArgumentParser(description="""
Reads files describing name data from the 'Encyclopedia of Life' site,
tries to associate names with nodes in the tree-of-life database,
and adds tables to represent associated names.

Reads a vernacularNames.csv file:
    Starts with a header line containing:
        page_id, canonical_form, vernacular_string, language_code,
        resource_name, is_preferred_by_resource, is_preferred_by_eol
    The canonical_form and vernacular_string fields contain names
        associated with the page ID. Names are not always unique to
        particular page IDs.
""", formatter_class=argparse.RawDescriptionHelpFormatter)
parser.parse_args()

vnamesFile = "eol/vernacularNames.csv" # Had about 2.8e6 entries
dbFile = "data.db"
namesToSkip = {"unknown", "unknown species", "unidentified species"}
pickedIdsFile = "pickedEolIds.txt"
altsToSkipFile = "pickedEolAltsToSkip.txt"

print("Reading in vernacular-names data")
nameToPids = {} # 'pid' means 'Page ID'
canonicalNameToPids = {}
pidToNames = {}
pidToPreferred = {} # Maps pids to 'preferred' names
def updateMaps(name, pid, canonical, preferredAlt):
	global namesToSkip, nameToPids, canonicalNameToPids, pidToNames, pidToPreferred
	if name in namesToSkip:
		return
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
	if preferredAlt:
		pidToPreferred[pid] = name
with open(vnamesFile, newline="") as csvfile:
	reader = csv.reader(csvfile)
	lineNum = 0
	for row in reader:
		lineNum += 1
		if lineNum % 1e5 == 0:
			print(f"At line {lineNum}")
		# Skip header line
		if lineNum == 1:
			continue
		# Parse line
		pid = int(row[0])
		name1 = re.sub(r"<[^>]+>", "", row[1].lower()) # Remove tags
		name2 = html.unescape(row[2]).lower()
		lang = row[3]
		preferred = row[6] == "preferred"
		# Add to maps
		updateMaps(name1, pid, True, False)
		if lang == "eng" and name2 != "":
			updateMaps(name2, pid, False, preferred)

print("Checking for manually-picked pids")
nameToPickedPid = {}
if os.path.exists(pickedIdsFile):
	with open(pickedIdsFile) as file:
		for line in file:
			(name, _, eolId) = line.rstrip().partition("|")
			nameToPickedPid[name] = None if eolId == "" else int(eolId)
print(f"Found {len(nameToPickedPid)}")

print("Checking for alt-names to skip")
nameToAltsToSkip = {}
numToSkip = 0
if os.path.exists(altsToSkipFile):
	with open(altsToSkipFile) as file:
		for line in file:
			(name, _, altName) = line.rstrip().partition("|")
			if name not in nameToAltsToSkip:
				nameToAltsToSkip[name] = [altName]
			else:
				nameToAltsToSkip[name].append(altName)
			numToSkip += 1
print(f"Found {numToSkip} alt-names to skip")

print("Creating database tables")
dbCon = sqlite3.connect(dbFile)
dbCur = dbCon.cursor()
dbCur.execute("CREATE TABLE names(name TEXT, alt_name TEXT, pref_alt INT, src TEXT, PRIMARY KEY(name, alt_name))")
dbCur.execute("CREATE INDEX names_idx ON names(name)")
dbCur.execute("CREATE INDEX names_alt_idx ON names(alt_name)")
dbCur.execute("CREATE INDEX names_alt_idx_nc ON names(alt_name COLLATE NOCASE)")
dbCur.execute("CREATE TABLE eol_ids(id INT PRIMARY KEY, name TEXT)")
dbCur.execute("CREATE INDEX eol_name_idx ON eol_ids(name)")

print("Associating nodes with names")
usedPids = set()
unresolvedNodeNames = set()
dbCur2 = dbCon.cursor()
def addToDb(nodeName, pidToUse):
	" Adds page-ID-associated name data to a node in the database "
	global dbCur, pidToPreferred
	dbCur.execute("INSERT INTO eol_ids VALUES (?, ?)", (pidToUse, nodeName))
	# Get alt-names
	altNames = set()
	for n in pidToNames[pidToUse]:
		# Avoid alt-names with >3 words
		if len(n.split(" ")) > 3:
			continue
		# Avoid alt-names that already name a node in the database
		if dbCur.execute("SELECT name FROM nodes WHERE name = ?", (n,)).fetchone() != None:
			continue
		# Check for picked alt-name-to-skip
		if nodeName in nameToAltsToSkip and n in nameToAltsToSkip[nodeName]:
			print(f"Excluding alt-name {n} for node {nodeName}")
			continue
		#
		altNames.add(n)
	# Add alt-names to db
	preferredName = pidToPreferred[pidToUse] if (pidToUse in pidToPreferred) else None
	for n in altNames:
		isPreferred = 1 if (n == preferredName) else 0
		dbCur.execute("INSERT INTO names VALUES (?, ?, ?, 'eol')", (nodeName, n, isPreferred))
print("Adding picked IDs")
for (name, pid) in nameToPickedPid.items():
	if pid != None:
		addToDb(name, pid)
		usedPids.add(pid)
print("Associating nodes with canonical names")
iterNum = 0
for (nodeName,) in dbCur2.execute("SELECT name FROM nodes"):
	iterNum += 1
	if iterNum % 1e5 == 0:
		print(f"At iteration {iterNum}")
	if nodeName in nameToPickedPid:
		continue
	# Check for matching canonical name
	if nodeName in canonicalNameToPids:
		pidToUse = None
		# Pick an associated page ID
		for pid in canonicalNameToPids[nodeName]:
			hasLowerPrio = pid not in pidToPreferred and pidToUse in pidToPreferred
			hasHigherPrio = pid in pidToPreferred and pidToUse not in pidToPreferred
			if hasLowerPrio:
				continue
			if pid not in usedPids and (pidToUse == None or pid < pidToUse or hasHigherPrio):
				pidToUse = pid
		if pidToUse != None:
			addToDb(nodeName, pidToUse)
			usedPids.add(pidToUse)
	elif nodeName in nameToPids:
		unresolvedNodeNames.add(nodeName)
print("Associating leftover nodes with other names")
iterNum = 0
for nodeName in unresolvedNodeNames:
	iterNum += 1
	if iterNum % 100 == 0:
		print(f"At iteration {iterNum}")
	# Check for matching name
	pidToUse = None
	for pid in nameToPids[nodeName]:
		# Pick an associated page ID
		if pid not in usedPids and (pidToUse == None or pid < pidToUse):
			pidToUse = pid
	if pidToUse != None:
		addToDb(nodeName, pidToUse)
		usedPids.add(pidToUse)

print("Closing database")
dbCon.commit()
dbCon.close()
