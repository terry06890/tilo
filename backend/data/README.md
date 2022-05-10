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
3   Image Data
    1   Use downloadImgsForReview.py to download EOL images into imgsForReview/.
        It uses data in eol/imagesList.db, and the 'eol\_ids' table.
    2   Use reviewImgs.py to filter images in imgsForReview/ into EOL-id-unique
        images in imgsReviewed/ (uses 'names' and 'eol\_ids' to display extra info).
    3   Use genImgsForWeb.py to create cropped/resized images in img/, using
        images in imgsReviewed, and also to add an 'images' table to data.db.
4   Node Description Data
    1   Obtain data in enwiki/, as specified in it's README.
    2   Run genEnwikiData.py, which adds a 'descs' table to data.db,
        using data in enwiki/enwikiData.db, and the 'nodes' table.

data.db tables
==============
-   nodes <br>
    name TEXT PRIMARY KEY, children TEXT, parent TEXT, tips INT, p\_support INT
-   names <br>
    name TEXT, alt\_name TEXT, pref\_alt INT, PRIMARY KEY(name, alt\_name)
-   eol\_ids <br>
    id INT PRIMARY KEY, name TEXT
-   images <br>
    eol\_id INT PRIMARY KEY, source\_url TEXT, license TEXT, copyright\_owner TEXT
-   descs <br>
    name TEXT PRIMARY KEY, desc TEXT, redirected INT
