#!/usr/bin/python3

import sys, os, re
import sqlite3

import argparse
parser = argparse.ArgumentParser(description="""
Reads a database containing data from DBpedia, and tries to associate
DBpedia IRIs with nodes in the tree-of-life database, adding
short-descriptions for them.
""", formatter_class=argparse.RawDescriptionHelpFormatter)
parser.parse_args()

dbpediaDb = "dbpedia/descData.db"
namesToSkipFile = "pickedEnwikiNamesToSkip.txt"
pickedLabelsFile = "pickedDbpLabels.txt"
dbFile = "data.db"
rootNodeName = "cellular organisms"
rootLabel = "Organism" # Will be associated with root node
# Got about 400k descriptions when testing

print("Opening databases")
dbpCon = sqlite3.connect(dbpediaDb)
dbpCur = dbpCon.cursor()
dbCon = sqlite3.connect(dbFile)
dbCur = dbCon.cursor()

print("Getting node names")
nodeNames = set()
for (name,) in dbCur.execute("SELECT name from nodes"):
	nodeNames.add(name)

print("Checking for names to skip")
oldSz = len(nodeNames)
if os.path.exists(namesToSkipFile):
	with open(namesToSkipFile) as file:
		for line in file:
			nodeNames.remove(line.rstrip())
print(f"Skipping {oldSz - len(nodeNames)} nodes")

print("Reading disambiguation-page labels")
disambigLabels = set()
query = "SELECT labels.iri from labels INNER JOIN disambiguations ON labels.iri = disambiguations.iri"
for (label,) in dbpCur.execute(query):
	disambigLabels.add(label)

print("Trying to associate nodes with DBpedia labels")
nodeToLabel = {}
nameVariantRegex = re.compile(r"(.*) \(([^)]+)\)") # Used to recognise labels like 'Thor (shrimp)'
nameToVariants = {} # Maps node names to lists of matching labels
iterNum = 0
for (label,) in dbpCur.execute("SELECT label from labels"):
	iterNum += 1
	if iterNum % 1e5 == 0:
		print(f"At iteration {iterNum}")
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
# Associate labels without conflicts
for (name, variants) in nameToVariants.items():
	if len(variants) == 1:
		nodeToLabel[name] = variants[0]
for name in nodeToLabel:
	del nameToVariants[name]
# Special case for root node
nodeToLabel[rootNodeName] = rootLabel
if rootNodeName in nameToVariants:
	del nameToVariants["cellular organisms"]

print(f"Trying to resolve {len(nameToVariants)} conflicts")
def resolveWithPickedLabels():
	" Attempts to resolve conflicts using a picked-names file "
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
					print(f"INFO: Picked label \"{label}\" for name \"{name}\" outside choice set", file=sys.stderr)
				nodeToLabel[name] = label
				del nameToVariants[name]
def resolveWithCategoryList():
	"""
	Attempts to resolve conflicts by looking for labels like 'name1 (category1)',
	and choosing those with a category1 that seems 'biological'.
	Does two passes, using more generic categories first. This helps avoid stuff like
	Pan being classified as a horse instead of an ape.
	"""
	generalCategories = {
		"species", "genus",
		"plant", "fungus", "animal",
		"annelid", "mollusc", "arthropod", "crustacean", "insect", "bug",
		"fish", "amphibian", "reptile", "bird", "mammal",
	}
	specificCategories = {
		"protist", "alveolate", "dinoflagellates",
		"orchid", "poaceae", "fern", "moss", "alga",
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
			if match != None and match.group(2).lower() in generalCategories:
				nodeToLabel[name] = label
				namesToRemove.add(name)
				found = True
				break
		if not found:
			for label in variants:
				match = nameVariantRegex.match(label)
				if match != None and match.group(2).lower() in specificCategories:
					nodeToLabel[name] = label
					namesToRemove.add(name)
					break
	for name in namesToRemove:
		del nameToVariants[name]
def resolveWithTypeData():
	" Attempts to resolve conflicts using DBpedia's type data "
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
			print(f"At iteration {iterNum}")
		#
		if type in taxonTypes:
			name = label.lower()
			if name in nameToVariants:
				nodeToLabel[name] = label
				del nameToVariants[name]
			else:
				match = nameVariantRegex.fullmatch(name)
				if match != None:
					name = match.group(1).lower()
					if name in nameToVariants:
						nodeToLabel[name] = label
						del nameToVariants[name]
#resolveWithTypeData()
#resolveWithCategoryList()
resolveWithPickedLabels()
print(f"Remaining number of conflicts: {len(nameToVariants)}")

print("Getting node IRIs")
nodeToIri = {}
for (name, label) in nodeToLabel.items():
	(iri,) = dbpCur.execute("SELECT iri FROM labels where label = ?", (label,)).fetchone()
	nodeToIri[name] = iri

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

print("Adding description tables")
dbCur.execute("CREATE TABLE wiki_ids (name TEXT PRIMARY KEY, id INT, redirected INT)")
dbCur.execute("CREATE INDEX wiki_id_idx ON wiki_ids(id)")
dbCur.execute("CREATE TABLE descs (wiki_id INT PRIMARY KEY, desc TEXT, from_dbp INT)")
iterNum = 0
for (name, iri) in nodeToIri.items():
	iterNum += 1
	if iterNum % 1e4 == 0:
		print(f"At iteration {iterNum}")
	#
	query = "SELECT abstract, id FROM abstracts INNER JOIN ids ON abstracts.iri = ids.iri WHERE ids.iri = ?"
	row = dbpCur.execute(query, (iri,)).fetchone()
	if row != None:
		desc, wikiId = row
		dbCur.execute("INSERT INTO wiki_ids VALUES (?, ?, ?)", (name, wikiId, 1 if name in redirectingIriSet else 0))
		dbCur.execute("INSERT OR IGNORE INTO descs VALUES (?, ?, ?)", (wikiId, desc, 1))

print("Closing databases")
dbCon.commit()
dbCon.close()
dbpCon.commit()
dbpCon.close()
