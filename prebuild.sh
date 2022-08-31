#!/bin/bash
set -e

sed -i -e "s|base: .*,|base: '/tilo/',|" vite.config.js
sed -i -e "s|SERVER_DATA_URL = .*|SERVER_DATA_URL = (new URL(window.location.href)).origin + '/tilo/data/'|" \
	-e "s|SERVER_IMG_PATH = .*|SERVER_IMG_PATH = '/img/tilo/'|" src/lib.ts
sed -i -e 's|DB_FILE = .*|DB_FILE = "/usr/local/www/db/tilo.db"|' backend/tilo.py
