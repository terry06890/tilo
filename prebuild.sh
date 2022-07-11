#!/bin/bash
set -e

sed -i -e "s|base: .*,|base: '/tilo/',|" vite.config.js
sed -i -e "s|SERVER_DATA_URL = .*|SERVER_DATA_URL = 'https://terryt.dev/tilo/data'|" \
	-e "s|SERVER_IMG_PATH = .*|SERVER_IMG_PATH = '/img/tilo/'|" src/lib.ts
sed -i -e 's|dbFile = .*|dbFile = "/usr/local/www/db/tilo.db"|' backend/tilo.py
