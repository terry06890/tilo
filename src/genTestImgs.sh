#!/bin/bash
set -e

#generate tol.json from tol.txt
cat tolData.txt | ./txtTreeToJSON.py > tolData.json

#reads through tolData.json, gets names, and generates image for each name
cat tolData.json | \
	gawk 'match ($0, /"name"\s*:\s*"([^"]*)"/, arr) {print arr[1]}' | \
	while read; do
		convert -size 200x200 xc:khaki +repage \
			-size 150x150  -fill black -background None  \
			-font Ubuntu-Mono -gravity center caption:"$REPLY" +repage \
			-gravity Center  -composite -strip ../public/img/"$REPLY".png
	done

