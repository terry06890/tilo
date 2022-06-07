#!/usr/bin/python3

import sys, os, re
import sqlite3

usageInfo =  f"usage: {sys.argv[0]}\n"
usageInfo += "Reads DBpedia data from dbpedia/*, along with tree-of-life\n"
usageInfo += "node and name data from a sqlite database, associates nodes with\n"
usageInfo += "DBpedia IRIs, and adds alt-name and description information for\n"
usageInfo += "those nodes.\n"
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

dbpediaDb = "dbpedia/dbpData.db"
namesToSkipFile = "dbpNamesToSkip.txt"
pickedLabelsFile = "dbpPickedLabels.txt"
dbFile = "data.db"

# Open dbs
dbpCon = sqlite3.connect(dbpediaDb)
dbpCur = dbpCon.cursor()
dbCon = sqlite3.connect(dbFile)
dbCur = dbCon.cursor()
# Get node names
print("Reading node names")
nodeNames = set()
for (name,) in dbCur.execute("SELECT name from nodes"):
	nodeNames.add(name)
# Skipping certain names
print("Checking for names to skip")
oldSz = len(nodeNames)
if os.path.exists(namesToSkipFile):
	with open(namesToSkipFile) as file:
		for line in file:
			nodeNames.remove(line.rstrip())
print(f"Skipping {oldSz - len(nodeNames)} nodes")
# Get disambiguation page labels
print("Reading disambiguation-page labels")
disambigLabels = set()
query = "SELECT labels.iri from labels INNER JOIN disambiguations ON labels.iri = disambiguations.iri"
for (label,) in dbpCur.execute(query):
	disambigLabels.add(label)
# Try associating nodes with IRIs, accounting for disambiguation labels
print("Trying to associate nodes with labels")
nodeToLabel = {}
nameVariantRegex = re.compile(r"(.*) \(([^)]+)\)")
nameToVariants = {}
iterNum = 0
for (label,) in dbpCur.execute("SELECT label from labels"):
	iterNum += 1
	if iterNum % 1e5 == 0:
		print(f"Processing line {iterNum}")
	#
	if label in disambigLabels:
		continue
	name = label.lower()
	if name in nodeNames:
		if name not in nameToVariants:
			nameToVariants[name] = [label]
		elif label not in nameToVariants[name]:
			nameToVariants[name].append(label)
	else:
		match = nameVariantRegex.fullmatch(name)
		if match != None:
			subName = match.group(1)
			if subName in nodeNames and match.group(2) != "disambiguation":
				if subName not in nameToVariants:
					nameToVariants[subName] = [label]
				elif name not in nameToVariants[subName]:
					nameToVariants[subName].append(label)
for (name, variants) in nameToVariants.items():
	if len(variants) == 1:
		nodeToLabel[name] = variants[0]
for name in nodeToLabel:
	del nameToVariants[name]
nodeToLabel["cellular organisms"] = "organism" # Special case for root node
print(f"Number of conflicts: {len(nameToVariants)}")
# Try resolving conflicts
def resolveWithPickedLabels():
	# Attempts conflict resolution using a file with lines of the form 'name1|label1',
		# where label1 may be absent, indicating that no label should be associated with the name
	print("Resolving conflicts using picked-labels")
	with open(pickedLabelsFile) as file:
		for line in file:
			(name, _, label) = line.rstrip().partition("|")
			if name not in nameToVariants:
				print(f"WARNING: No conflict found for name \"{name}\"", file=sys.stderr)
				continue
			if label == "":
				del nameToVariants[name]
			else:
				if label not in nameToVariants[name]:
					print(f"WARNING: Picked label \"{label}\" for name \"{name}\" not found", file=sys.stderr)
					continue
				nodeToLabel[name] = label
				del nameToVariants[name]
	print(f"Remaining number of conflicts: {len(nameToVariants)}")
def resolveWithCategoryList():
	# Attempts conflict resolution using category-text in labels of the form 'name1 (category1)'
	# Does a generic-category pass first (avoid stuff like Pan being classified as a horse instead of an ape)
	print("Resolving conflicts using category-list")
	generalCategories = {
		"species", "genus",
		"plant", "fungus", "animal",
		"annelid", "mollusc", "arthropod", "crustacean", "insect", "bug",
		"fish", "amphibian", "reptile", "bird", "mammal",
	}
	specificCategories = {
		"protist", "alveolate", "dinoflagellates",
		"orchid", "Poaceae", "fern", "moss", "alga",
		"bryozoan", "hydrozoan",
		"sponge", "cnidarian", "coral", "polychaete", "echinoderm",
		"bivalve", "gastropod", "chiton",
		"shrimp", "decapod", "crab", "barnacle", "copepod",
		"arachnid", "spider", "harvestman", "mite",
		"dragonfly", "mantis", "cicada", "grasshopper", "planthopper",
			"beetle", "fly", "butterfly", "moth", "wasp",
		"catfish",
		"frog",
		"lizard",
		"horse", "sheep", "cattle", "mouse",
	}
	namesToRemove = set()
	for (name, variants) in nameToVariants.items():
		found = False
		for label in variants:
			match = nameVariantRegex.match(label)
			if match != None and match.group(2) in generalCategories:
				nodeToLabel[name] = label
				namesToRemove.add(name)
				found = True
				break
		if not found:
			for label in variants:
				match = nameVariantRegex.match(label)
				if match != None and match.group(2) in specificCategories:
					nodeToLabel[name] = label
					namesToRemove.add(name)
					break
	for name in namesToRemove:
		del nameToVariants[name]
	print(f"Remaining number of conflicts: {len(nameToVariants)}")
def resolveWithTypeData():
	# Attempts conflict-resolution using dbpedia's instance-type data
	print("Resolving conflicts using instance-type data")
	taxonTypes = { # Obtained from the DBpedia ontology
		"http://dbpedia.org/ontology/Species",
		"http://dbpedia.org/ontology/Archaea",
		"http://dbpedia.org/ontology/Bacteria",
		"http://dbpedia.org/ontology/Eukaryote",
		"http://dbpedia.org/ontology/Plant",
		"http://dbpedia.org/ontology/ClubMoss",
		"http://dbpedia.org/ontology/Conifer",
		"http://dbpedia.org/ontology/CultivatedVariety",
		"http://dbpedia.org/ontology/Cycad",
		"http://dbpedia.org/ontology/Fern",
		"http://dbpedia.org/ontology/FloweringPlant",
		"http://dbpedia.org/ontology/Grape",
		"http://dbpedia.org/ontology/Ginkgo",
		"http://dbpedia.org/ontology/Gnetophytes",
		"http://dbpedia.org/ontology/GreenAlga",
		"http://dbpedia.org/ontology/Moss",
		"http://dbpedia.org/ontology/Fungus",
		"http://dbpedia.org/ontology/Animal",
		"http://dbpedia.org/ontology/Fish",
		"http://dbpedia.org/ontology/Crustacean",
		"http://dbpedia.org/ontology/Mollusca",
		"http://dbpedia.org/ontology/Insect",
		"http://dbpedia.org/ontology/Arachnid",
		"http://dbpedia.org/ontology/Amphibian",
		"http://dbpedia.org/ontology/Reptile",
		"http://dbpedia.org/ontology/Bird",
		"http://dbpedia.org/ontology/Mammal",
		"http://dbpedia.org/ontology/Cat",
		"http://dbpedia.org/ontology/Dog",
		"http://dbpedia.org/ontology/Horse",
	}
	iterNum = 0
	for (label, type) in dbpCur.execute("SELECT label, type from labels INNER JOIN types on labels.iri = types.iri"):
		iterNum += 1
		if iterNum % 1e5 == 0:
			print(f"Processing line {iterNum}")
		#
		if type in taxonTypes:
			name = label.lower()
			if name in nameToVariants:
				nodeToLabel[name] = label
				del nameToVariants[name]
			else:
				match = nameVariantRegex.fullmatch(name)
				if match != None:
					name = match.group(1)
					if name in nameToVariants:
						nodeToLabel[name] = label
						del nameToVariants[name]
	print(f"Remaining number of conflicts: {len(nameToVariants)}")
resolveWithPickedLabels()
# Associate nodes with IRIs
print("Getting node IRIs")
nodeToIri = {}
iterNum = 0
for (name, label) in nodeToLabel.items():
	row = dbpCur.execute("SELECT iri FROM labels where label = ? COLLATE NOCASE", (label,)).fetchone()
	if row == None:
		print(f"ERROR: Couldn't find label {label}", file=sys.stderr)
		sys.exit(1)
	else:
		nodeToIri[name] = row[0]
# Resolve redirects
print("Resolving redirects")
redirectingIriSet = set()
iterNum = 0
for (name, iri) in nodeToIri.items():
	iterNum += 1
	if iterNum % 1e4 == 0:
		print(f"At iteration {iterNum}")
	#
	row = dbpCur.execute("SELECT target FROM redirects where iri = ?", (iri,)).fetchone()
	if row != None:
		nodeToIri[name] = row[0]
		redirectingIriSet.add(name)
# Find descriptions, and add to db
print("Adding node description data")
dbCur.execute("CREATE TABLE descs (name TEXT PRIMARY KEY, desc TEXT, redirected INT, wiki_id INT, from_dbp INT)")
dbCur.execute("CREATE INDEX descs_id_idx ON descs(wiki_id)") # wiki_id intentionally left non-unique
iterNum = 0
for (name, iri) in nodeToIri.items():
	iterNum += 1
	if iterNum % 1e4 == 0:
		print(f"At iteration {iterNum}")
	#
	query = "SELECT abstract, id FROM abstracts INNER JOIN ids ON abstracts.iri = ids.iri WHERE ids.iri = ?"
	row = dbpCur.execute(query, (iri,)).fetchone()
	if row != None:
		dbCur.execute("INSERT INTO descs VALUES (?, ?, ?, ?, ?)",
			(name, row[0], 1 if name in redirectingIriSet else 0, row[1], 1))
# Close dbs
dbCon.commit()
dbCon.close()
dbpCon.commit()
dbpCon.close()
