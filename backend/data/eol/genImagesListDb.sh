#!/bin/bash
set -e

# Combine CSV files into one, skipping header lines
cat imagesList/media_*_{1..58}.csv | tail -n +2 > imagesList.csv
# Create database, and import the CSV file
sqlite3 imagesList.db <<END
CREATE TABLE images (
	content_id INT PRIMARY KEY, page_id INT, source_url TEXT, copy_url TEXT, license TEXT, copyright_owner TEXT);
.mode csv
.import 'imagesList.csv' images
END
