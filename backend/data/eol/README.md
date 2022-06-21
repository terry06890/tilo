This directory holds files obtained from/using the [Encyclopedia of Life](https://eol.org/).

# Name Data Files
-   vernacularNames.csv <br>
    Obtained from <https://opendata.eol.org/dataset/vernacular-names> on 24/04/2022 (last updated on 27/10/2020).
    Contains alternative-name data from EOL.

# Image Metadata Files
-   imagesList.tgz <br>
    Obtained from <https://opendata.eol.org/dataset/images-list> on 24/04/2022 (last updated on 05/02/2020).
    Contains metadata for images from EOL.
-   imagesList/ <br>
    Extracted from imagesList.tgz.
-   imagesList.db <br>
    Contains data from imagesList/.
    Created by running genImagesListDb.sh, which simply imports csv files into a database. <br>
    Tables: <br>
    -   `images`:
        `content_id INT PRIMARY KEY, page_id INT, source_url TEXT, copy_url TEXT, license TEXT, copyright_owner TEXT`

# Image Generation Files
-   downloadImgs.py <br>
    Used to download image files into imgsForReview/.
-   reviewImgs.py <br>
    Used to review images in imgsForReview/, moving acceptable ones into imgs/.
