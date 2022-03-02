#!/bin/bash
set -e

#reads through tol.json, gets names, and generates image for each name
cat tol.json | \
	gawk 'match ($0, /"name"\s*:\s*"(.*)"/, arr) {print arr[1]}' | \
	while read; do
		convert -size 400x400 xc:khaki +repage \
			-size 300x300  -fill black -background None  \
			-font Ubuntu-Mono -gravity center caption:"$REPLY" +repage \
			-gravity Center  -composite -strip  assets/"$REPLY".jpg
	done

