#!/usr/bin/python3

import sys, re
import sqlite3

usageInfo =  f"usage: {sys.argv[0]}\n"
usageInfo += "Reads DBpedia data from dbpedia/dbpData.db, along with tree-of-life\n"
usageInfo += "node name data from a sqlite database, and looks for potential\n"
usageInfo += "conflicts in associating node names with DBpedia-node labels. For\n"
usageInfo += "example, a node named 'homo sapiens' might have conflicting labels\n"
usageInfo += "'Homo sapiens', 'homo sapiens (novel)', and 'homo sapiens (song)'.\n"
usageInfo += "\n"
usageInfo += "Writes conflict information to file. For each conflict, a line is printed,\n"
usageInfo += "holding comma-separated DBpedia labels. If the labels include no-parentheses elements,\n"
usageInfo += "additional tab-indented lines are printed, wholding short-abstracts for those labels.\n"
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

dbpDb = "dbpedia/dbpData.db"
dbFile = "data.db"
outFile = "conflicts.txt"

# Open dbs
dbCon = sqlite3.connect(dbFile)
dbCur = dbCon.cursor()
dbpCon = sqlite3.connect(dbpDb)
dbpCur = dbpCon.cursor()
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
# Find labels with conflicts
print("Finding conflicting labels")
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
					nameToVariants[subName] = [name] # Intentionally ignoring case here
				elif name not in nameToVariants[subName]:
					nameToVariants[subName].append(name)
namesToRemove = set()
for (name, variants) in nameToVariants.items():
	if len(variants) == 1:
		namesToRemove.add(name)
for name in namesToRemove:
	del nameToVariants[name]
print(f"Number of conflicts: {len(nameToVariants)}")
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
		print(f"Processing line {iterNum}")
	#
	if type in taxonTypes:
		name = label.lower()
		if name in nameToVariants:
			del nameToVariants[name]
		else:
			match = nameVariantRegex.fullmatch(name)
			if match != None:
				name = match.group(1)
				if name in nameToVariants:
					del nameToVariants[name]
print(f"Number of conflicts: {len(nameToVariants)}")
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
			namesToRemove.add(name)
			found = True
			break
	if not found:
		for label in variants:
			match = nameVariantRegex.match(label)
			if match != None and match.group(2) in specificCategories:
				namesToRemove.add(name)
				break
for name in namesToRemove:
	del nameToVariants[name]
print(f"Number of conflicts: {len(nameToVariants)}")
# Find descriptions for plain-named labels
print("Finding descriptions for plain-named labels")
labelToDesc = {}
iterNum = 0
query = "SELECT label, abstract from labels INNER JOIN abstracts ON labels.iri = abstracts.iri"
for (label, desc,) in dbpCur.execute(query):
	iterNum += 1
	if iterNum % 1e5 == 0:
		print(f"Processing line {iterNum}")
	#
	if label.lower() in nameToVariants:
		labelToDesc[label] = desc
print("Finding descriptions for redirect-resolved labels")
iterNum = 0
query = "SELECT label, abstract from labels" \
	" INNER JOIN redirects ON labels.iri = redirects.iri INNER JOIN abstracts ON redirects.target = abstracts.iri"
for (label, desc,) in dbpCur.execute(query):
	iterNum += 1
	if iterNum % 1e5 == 0:
		print(f"Processing line {iterNum}")
	#
	if label.lower() in nameToVariants:
		labelToDesc[label] = desc
#
print("Writing conflict data to file")
with open(outFile, "w") as file:
	for (name, variants) in nameToVariants.items():
		for n in variants:
			file.write(n + ", ")
		file.write("\n")
		for n in variants:
			if n in labelToDesc:
				file.write(f"\t{n}: {labelToDesc[n]}\n")
# Close dbs
dbCon.close()
dbpCon.close()
