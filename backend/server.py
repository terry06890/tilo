#!/usr/bin/python3

import sys
from wsgiref.simple_server import make_server
from tilo import application

usageInfo = f"""
Usage: {sys.argv[0]}

Runs a basic dev server that serves a WSGI script
"""
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

with make_server('', 8000, application) as httpd:
    print("Serving HTTP on port 8000...")
    httpd.serve_forever()
