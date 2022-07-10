# Files
-   data:      Contains scripts for generating the tree-of-life database
-   tilo.py:   WSGI script that serves tree-of-life data
-   server.py: Basic dev server that serves a WSGI script

# During development
Having generated the database as data/data.db, running `server.py`,
in this directory, allows the client to access data from `tilo.py`,
via `localhost:8000`.
