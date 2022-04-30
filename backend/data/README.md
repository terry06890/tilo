File Generation Process
=======================
1   Obtain data in otol/ and eol/, as specified in their README files.
2   Run genOtolData.py, which creates data.db, and adds a 'nodes'
    table using data in otol/*.
3   Run genEolNameData.py, which adds a 'names' table to data.db, 
    using data in eol/vernacularNames.csv and the 'nodes' table.
4   Use downloadImgsForReview.py to download EOL images into imgsForReview/.
    It uses data in eol/imagesList.db, and the 'nodes' table.
5   Use reviewImgs.py to filter images in imgsForReview/ into EOL-id-unique
    images in imgsReviewed/ (uses 'names' to display common names).
6   Use genImgsForWeb.py to create cropped/resized images in img/, using
    images in imgsReviewed, and also to add an 'images' table to data.db.
