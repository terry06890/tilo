#!/usr/bin/python3

import sys, os
from wsgiref import simple_server, util
import mimetypes
from tilo import application

import argparse
parser = argparse.ArgumentParser(description="""
Runs a basic dev server that serves a WSGI script and image files
""")
parser.parse_args()

# WSGI handler that uses 'application', but also serves image files
def wrappingApp(environ, start_response):
	urlPath = environ["PATH_INFO"]
	if urlPath.startswith("/data/"):
		# Run WSGI script
		return application(environ, start_response)
	elif urlPath.startswith("/tolData/img/"):
		# Serve image file
		imgPath = os.path.join(os.getcwd(), urlPath[1:])
		if os.path.exists(imgPath):
			imgType = mimetypes.guess_type(imgPath)[0]
			start_response("200 OK", [("Content-type", imgType)])
			return util.FileWrapper(open(imgPath, "rb"))
		else:
			start_response("404 Not Found", [("Content-type", "text/plain")])
			return [b"No image found"]
	else:
		start_response("404 Not Found", [("Content-type", "text/plain")])
		return [b"Unrecognised path"]
# Start server
with simple_server.make_server('', 8000, wrappingApp) as httpd:
    print("Serving HTTP on port 8000...")
    httpd.serve_forever()
