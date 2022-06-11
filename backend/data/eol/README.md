Downloaded Files
================
-   imagesList.tgz <br>
    Obtained from https://opendata.eol.org/dataset/images-list on 24/04/2022.
    Listed as being last updated on 05/02/2020.
-   vernacularNames.csv <br>
    Obtained from https://opendata.eol.org/dataset/vernacular-names on 24/04/2022.
    Listed as being last updated on 27/10/2020.

Generated Files
===============
-   imagesList/ <br>
    Obtained by extracting imagesList.tgz.
-   imagesList.db <br>
    Represents data from eol/imagesList/*, and is created by genImagesListDb.sh. <br>
    Tables: <br>
    -   images:
        content_id INT PRIMARY KEY, page_id INT, source_url TEXT, copy_url TEXT, license TEXT, copyright_owner TEXT
