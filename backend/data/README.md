File Generation Process
=======================
1   Obtain data in otol/ and eol/, as specified in their README files.
2   Run genOtolData.py, which creates data.db, and adds a 'nodes'
    table using data in otol/*.
3   Run genEolNameData.py, which adds a 'names' table to data.db, 
    using data in eol/vernacularNames.csv and the 'nodes' table.
4   Run genSpellfixNameData.py, which adds a 'spellfix\_alt\_names'
    table to data.db, using data in the 'names' table.
5   Use downloadImgsForReview.py to download EOL images into imgsForReview/.
    It uses data in eol/imagesList.db, and the 'nodes' table.
6   Use reviewImgs.py to filter images in imgsForReview/ into EOL-id-unique
    images in imgsReviewed/ (uses 'names' to display common names).
7   Use genImgsForWeb.py to create cropped/resized images in img/, using
    images in imgsReviewed, and also to add an 'images' table to data.db.

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
