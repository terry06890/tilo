#!/usr/bin/python3

import sys
import sqlite3

usageInfo =  f"usage: {sys.argv[0]}\n"
usageInfo += "Reads alt-names from a 'names' table in a database, and adds a spellfix \n"
usageInfo += "table 'spellfix_alt_names' usable for fuzzy-searching those names.\n"
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

dbFile = "data.db"

# Connect to db, and load spellfix extension
dbCon = sqlite3.connect(dbFile)
dbCon.enable_load_extension(True)
dbCon.load_extension('./spellfix')
# Create spellfix table, and insert alt-names
spellfixCur = dbCon.cursor()
spellfixCur.execute("CREATE VIRTUAL TABLE spellfix_alt_names USING spellfix1")
namesCur = dbCon.cursor()
iterationNum = 0
for row in namesCur.execute("SELECT DISTINCT alt_name FROM names"):
	iterationNum += 1
	if iterationNum % 10000 == 0:
		print("Loop {}: {}".format(iterationNum, row[0]))
	# Insert alt-name
	spellfixCur.execute("INSERT INTO spellfix_alt_names(word) VALUES (?)", (row[0],))
# Close db
dbCon.commit()
dbCon.close()
