#!/bin/bash
set -e

cat imagesList/media_*_{1..58}.csv | tail -n +2 > imagesList.csv
sqlite3 imagesList.db <<END
CREATE TABLE images (
	content_id INT PRIMARY KEY, page_id INT, source_url TEXT, copy_url TEXT, license TEXT, copyright_owner TEXT);
.mode csv
.import 'imagesList.csv' images
END
