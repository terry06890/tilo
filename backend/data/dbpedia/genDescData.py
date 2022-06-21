#!/usr/bin/python3

import sys, re
import bz2, sqlite3

usageInfo =  f"usage: {sys.argv[0]}\n"
usageInfo += "Reads DBpedia labels/types/abstracts/etc data,\n"
usageInfo += "and creates a sqlite db containing that data.\n"
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

labelsFile = "labels_lang=en.ttl.bz2" # Has about 16e6 lines
idsFile = "page_lang=en_ids.ttl.bz2"
redirectsFile = "redirects_lang=en_transitive.ttl.bz2"
disambigFile = "disambiguations_lang=en.ttl.bz2"
typesFile = "instance-types_lang=en_specific.ttl.bz2"
abstractsFile = "short-abstracts_lang=en.ttl.bz2"
dbFile = "descData.db"

# Open db
dbCon = sqlite3.connect(dbFile)
dbCur = dbCon.cursor()
# Read/store labels
print("Reading/storing label data")
dbCur.execute("CREATE TABLE labels (iri TEXT PRIMARY KEY, label TEXT)")
dbCur.execute("CREATE INDEX labels_idx ON labels(label)")
dbCur.execute("CREATE INDEX labels_idx_nc ON labels(label COLLATE NOCASE)")
labelLineRegex = re.compile(r'<([^>]+)> <[^>]+> "((?:[^"]|\\")+)"@en \.\n')
lineNum = 0
with bz2.open(labelsFile, mode='rt') as file:
	for line in file:
		lineNum += 1
		if lineNum % 1e5 == 0:
			print(f"Processing line {lineNum}")
		#
		match = labelLineRegex.fullmatch(line)
		if match == None:
			print(f"ERROR: Line {lineNum} has unexpected format", file=sys.stderr)
			sys.exit(1)
		else:
			dbCur.execute("INSERT INTO labels VALUES (?, ?)", (match.group(1), match.group(2)))
dbCon.commit()
# Read/store wiki page ids
print("Reading/storing wiki page ids")
dbCur.execute("CREATE TABLE ids (iri TEXT PRIMARY KEY, id INT)")
idLineRegex = re.compile(r'<([^>]+)> <[^>]+> "(\d+)".*\n')
lineNum = 0
with bz2.open(idsFile, mode='rt') as file:
	for line in file:
		lineNum += 1
		if lineNum % 1e5 == 0:
			print(f"Processing line {lineNum}")
		#
		match = idLineRegex.fullmatch(line)
		if match == None:
			print(f"ERROR: Line {lineNum} has unexpected format", file=sys.stderr)
			sys.exit(1)
		else:
			try:
				dbCur.execute("INSERT INTO ids VALUES (?, ?)", (match.group(1), int(match.group(2))))
			except sqlite3.IntegrityError as e:
				# Accounts for certain lines that have the same IRI
				print(f"Failed to add entry with IRI \"{match.group(1)}\": {e}")
dbCon.commit()
# Read/store redirects
print("Reading/storing redirection data")
dbCur.execute("CREATE TABLE redirects (iri TEXT PRIMARY KEY, target TEXT)")
redirLineRegex = re.compile(r'<([^>]+)> <[^>]+> <([^>]+)> \.\n')
lineNum = 0
with bz2.open(redirectsFile, mode='rt') as file:
	for line in file:
		lineNum += 1
		if lineNum % 1e5 == 0:
			print(f"Processing line {lineNum}")
		#
		match = redirLineRegex.fullmatch(line)
		if match == None:
			print(f"ERROR: Line {lineNum} has unexpected format", file=sys.stderr)
			sys.exit(1)
		else:
			dbCur.execute("INSERT INTO redirects VALUES (?, ?)", (match.group(1), match.group(2)))
dbCon.commit()
# Read/store diambiguation-page data
print("Reading/storing diambiguation-page data")
disambigNames = set()
disambigLineRegex = redirLineRegex
lineNum = 0
with bz2.open(disambigFile, mode='rt') as file:
	for line in file:
		lineNum += 1
		if lineNum % 1e5 == 0:
			print(f"Processing line {lineNum}")
		#
		match = disambigLineRegex.fullmatch(line)
		if match == None:
			print(f"ERROR: Line {lineNum} has unexpected format", file=sys.stderr)
			sys.exit(1)
		else:
			disambigNames.add(match.group(1))
dbCur.execute("CREATE TABLE disambiguations (iri TEXT PRIMARY KEY)")
for name in disambigNames:
	dbCur.execute("INSERT INTO disambiguations VALUES (?)", (name,))
dbCon.commit()
# Read/store instance-type
print("Reading/storing instance-type data")
dbCur.execute("CREATE TABLE types (iri TEXT, type TEXT)")
dbCur.execute("CREATE INDEX types_iri_idx ON types(iri)")
typeLineRegex = redirLineRegex
lineNum = 0
with bz2.open(typesFile, mode='rt') as file:
	for line in file:
		lineNum += 1
		if lineNum % 1e5 == 0:
			print(f"Processing line {lineNum}")
		#
		match = typeLineRegex.fullmatch(line)
		if match == None:
			print(f"ERROR: Line {lineNum} has unexpected format", file=sys.stderr)
			sys.exit(1)
		else:
			dbCur.execute("INSERT INTO types VALUES (?, ?)", (match.group(1), match.group(2)))
dbCon.commit()
# Read/store abstracts
print("Reading/storing abstracts")
dbCur.execute("CREATE TABLE abstracts (iri TEXT PRIMARY KEY, abstract TEXT)")
descLineRegex = labelLineRegex
lineNum = 0
with bz2.open(abstractsFile, mode='rt') as file:
	for line in file:
		lineNum += 1
		if lineNum % 1e5 == 0:
			print(f"Processing line {lineNum}")
		#
		if line[0] == "#":
			continue
		match = descLineRegex.fullmatch(line)
		if match == None:
			print(f"ERROR: Line {lineNum} has unexpected format", file=sys.stderr)
			sys.exit(1)
		else:
			dbCur.execute("INSERT INTO abstracts VALUES (?, ?)",
				(match.group(1), match.group(2).replace(r'\"', '"')))
# Close db
dbCon.commit()
dbCon.close()
