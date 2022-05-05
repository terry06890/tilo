File Generation Process
=======================

1   Tree Structure Data
    1   Obtain data in otol/, as specified in it's README.
    2   Run genOtolData.py, which creates data.db, and adds a 'nodes'
        table using data in otol/*.
2   Name Data for Search
    1   Obtain data in eol/, as specified in it's README.
    2   Run genEolNameData.py, which adds 'names' and 'eol\_ids' tables to data.db, 
        using data in eol/vernacularNames.csv and the 'nodes' table.
    3   Run genSpellfixNameData.py, which adds a 'spellfix\_alt\_names'
        table to data.db, using data in the 'names' table.
3   Image Data
    1   Use downloadImgsForReview.py to download EOL images into imgsForReview/.
        It uses data in eol/imagesList.db, and the 'eol_ids' table.
    2   Use reviewImgs.py to filter images in imgsForReview/ into EOL-id-unique
        images in imgsReviewed/ (uses 'names' and 'eol_ids' to display extra info).
    3   Use genImgsForWeb.py to create cropped/resized images in img/, using
        images in imgsReviewed, and also to add an 'images' table to data.db.
4   Node Description Data
    1   Obtain data in enwiki/, as specified in it's README.
    2   Run genEnwikiData.py, which adds a 'descs' table to data.db,
        using data in enwiki/enwikiData.db, and the 'nodes' table.

data.db tables
==============
nodes: name TEXT PRIMARY KEY, children TEXT, parent TEXT, tips INT, p\_support INT
names: name TEXT, alt\_name TEXT, pref\_alt INT, PRIMARY KEY(name, alt\_name)
eol\_ids: id INT PRIMARY KEY, name TEXT
spellfix\_alt\_names
images: eol\_id INT PRIMARY KEY, source\_url TEXT, license TEXT, copyright\_owner TEXT
descs: name TEXT PRIMARY KEY, desc TEXT, redirected INT

spellfix.so
===========

This file provides the spellfix1 extension for Sqlite, and
is used for responding to fuzzy-search requests.

It was obtained by:
1   Downloading the sqlite source tree from
    the github mirror at <https://github.com/sqlite/sqlite>,
    into a directory sqlite/
2   After making sure autoconf 2.61+ and libtool are installed,
    running `mkdir bld; cd bld; ../sqlite/configure;`
3   Running `make`
4   Running `cp ../sqlite/ext/misc/spellfix.c .`
5   Running `gcc -fPIC -shared spellfix.c -o spellfix.so`
