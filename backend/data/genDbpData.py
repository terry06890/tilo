#!/usr/bin/python3

import sys, re
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
for row in dbCur.execute("SELECT name from nodes"):
	nodeNames.add(row[0])
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
		print("Processing line {}".format(iterNum))
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
					nameToVariants[subName] = [name] # Intentionally ignoring case here
				elif name not in nameToVariants[subName]:
					nameToVariants[subName].append(name)
for (name, variants) in nameToVariants.items():
	if len(variants) == 1:
		nodeToLabel[name] = variants[0]
for name in nodeToLabel:
	del nameToVariants[name]
nodeToLabel["cellular organisms"] = "organism" # Special case for root node
print("Number of conflicts: {}".format(len(nameToVariants)))
# Try conflict resolution via picked-labels
print("Resolving conflicts using picked-labels")
with open(pickedLabelsFile) as file:
	for line in file:
		pickedLabel = line.rstrip()
		name = pickedLabel.lower()
		if name in nameToVariants:
			nodeToLabel[name] = pickedLabel
			del nameToVariants[name]
		else:
			match = nameVariantRegex.match(pickedLabel)
			if match == None:
				print("WARNING: Picked label {} not found (1)".format(pickedLabel), file=sys.stderr)
			else:
				name = match.group(1)
				if name not in nameToVariants:
					print("WARNING: Picked label {} not found (2)".format(pickedLabel), file=sys.stderr)
				else:
					nodeToLabel[name] = pickedLabel
					del nameToVariants[name]
print("Number of conflicts: {}".format(len(nameToVariants)))
# Try conflict resolution via category-list
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
print("Number of conflicts: {}".format(len(nameToVariants)))
# Try conflict resolution via taxon-type information
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
		print("Processing line {}".format(iterNum))
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
print("Number of conflicts: {}".format(len(nameToVariants)))
# Associate nodes with IRIs
print("Getting nodes IRIs")
nodeToIri = {}
iterNum = 0
for (name, label) in nodeToLabel.items():
	row = dbpCur.execute("SELECT iri FROM labels where label = ? COLLATE NOCASE", (label,)).fetchone()
	if row == None:
		print("ERROR: Couldn't find label {}".format(label), file=sys.stderr)
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
		print("At iteration {}".format(iterNum))
	#
	row = dbpCur.execute("SELECT target FROM redirects where iri = ?", (iri,)).fetchone()
	if row != None:
		nodeToIri[name] = row[0]
		redirectingIriSet.add(name)
# Find descriptions, and add to db
print("Adding node description data")
dbCur.execute("CREATE TABLE descs (name TEXT PRIMARY KEY, desc TEXT, redirected INT, wiki_id INT, from_dbp INT)")
iterNum = 0
for (name, iri) in nodeToIri.items():
	iterNum += 1
	if iterNum % 1e4 == 0:
		print("At iteration {}".format(iterNum))
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
