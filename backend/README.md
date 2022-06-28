# Files
-   cgi-bin/data.py: CGI script for providing tree-of-life data to client
-   data: Contains scripts for generating the tree-of-life database

# During development
Having generated the database as data/data.db, running `python3 -m http.server --cgi 8000`,
in this directory, allows the client to access the CGI script, and hence the database,
via `localhost:8000/cgi-bin/data.py`.
