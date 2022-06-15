#!/usr/bin/python3

import sys, re, os
import html, csv, sqlite3

usageInfo =  f"usage: {sys.argv[0]}\n"
usageInfo += "Reads vernacular-names CSV data (from the Encyclopedia of Life site),\n"
usageInfo += "makes associations with node data in a sqlite database, and writes\n"
usageInfo += "name data to that database.\n"
usageInfo += "\n"
usageInfo += "Expects a CSV header describing lines with format:\n"
usageInfo += "    page_id, canonical_form, vernacular_string, language_code,\n"
usageInfo += "    resource_name, is_preferred_by_resource, is_preferred_by_eol\n"
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

vnamesFile = "eol/vernacularNames.csv"
dbFile = "data.db"
NAMES_TO_SKIP = {"unknown", "unknown species", "unidentified species"}
pickedIdsFile = "genEolNameDataPickedIds.txt"

# Read in vernacular-names data
	# Note: Canonical-names may have multiple pids
	# Note: A canonical-name's associated pids might all have other associated names
print("Reading in vernacular-names data")
nameToPids = {}
canonicalNameToPids = {}
pidToNames = {}
pidToPreferred = {}
def updateMaps(name, pid, canonical, preferredAlt):
	if name in NAMES_TO_SKIP:
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
# Check for manually-picked pids
print("Checking for manually-picked pids")
nameToPickedPid = {}
if os.path.exists(pickedIdsFile):
	with open(pickedIdsFile) as file:
		for line in file:
			(name, _, eolId) = line.rstrip().partition("|")
			nameToPickedPid[name] = None if eolId == "" else int(eolId)
print(f"Found {len(nameToPickedPid)}")
# Open db connection
dbCon = sqlite3.connect(dbFile)
dbCur = dbCon.cursor()
# Create tables
dbCur.execute("CREATE TABLE names(name TEXT, alt_name TEXT, pref_alt INT, src TEXT, PRIMARY KEY(name, alt_name))")
dbCur.execute("CREATE INDEX names_idx ON names(name)")
dbCur.execute("CREATE INDEX names_alt_idx ON names(alt_name)")
dbCur.execute("CREATE INDEX names_alt_idx_nc ON names(alt_name COLLATE NOCASE)")
dbCur.execute("CREATE TABLE eol_ids(id INT PRIMARY KEY, name TEXT)")
dbCur.execute("CREATE INDEX eol_name_idx ON eol_ids(name)")
# Iterate through 'nodes' table, resolving to canonical-names
usedPids = set()
unresolvedNodeNames = set()
dbCur2 = dbCon.cursor()
def addToDb(nodeName, pidToUse):
	altNames = set()
	preferredName = pidToPreferred[pidToUse] if (pidToUse in pidToPreferred) else None
	dbCur.execute("INSERT INTO eol_ids VALUES (?, ?)", (pidToUse, nodeName))
	for n in pidToNames[pidToUse]:
		if dbCur.execute("SELECT name FROM nodes WHERE name = ?", (n,)).fetchone() == None:
			altNames.add(n)
	for n in altNames:
		isPreferred = 1 if (n == preferredName) else 0
		dbCur.execute("INSERT INTO names VALUES (?, ?, ?, 'eol')", (nodeName, n, isPreferred))
for name in nameToPickedPid: # Add manually-picked pids
	pickedPid = nameToPickedPid[name]
	usedPids.add(pickedPid)
	if pickedPid != None:
		addToDb(name, pickedPid)
iterationNum = 0
for (name,) in dbCur2.execute("SELECT name FROM nodes"):
	iterationNum += 1
	if iterationNum % 10000 == 0:
		print(f"Loop 1 iteration {iterationNum}")
	if name in nameToPickedPid:
		continue
	# If name matches a canonical-name, add alt-name entries to 'names' table
	if name in canonicalNameToPids:
		pidToUse = None
		for pid in canonicalNameToPids[name]:
			hasLowerPrio = pid not in pidToPreferred and pidToUse in pidToPreferred
			hasHigherPrio = pid in pidToPreferred and pidToUse not in pidToPreferred
			if hasLowerPrio:
				continue
			if pid not in usedPids and (pidToUse == None or pid < pidToUse or hasHigherPrio):
				pidToUse = pid
		if pidToUse != None:
			usedPids.add(pidToUse)
			addToDb(name, pidToUse)
	elif name in nameToPids:
		unresolvedNodeNames.add(name)
# Iterate through unresolved nodes, resolving to vernacular-names
iterationNum = 0
for name in unresolvedNodeNames:
	iterationNum += 1
	if iterationNum % 100 == 0:
		print(f"Loop 2 iteration {iterationNum}")
	# Add alt-name entries to 'names' table for first corresponding pid
	pidToUse = None
	for pid in nameToPids[name]:
		if pid not in usedPids and (pidToUse == None or pid < pidToUse):
			pidToUse = pid
	if pidToUse != None:
		usedPids.add(pidToUse)
		addToDb(name, pidToUse)
# Close db
dbCon.commit()
dbCon.close()
