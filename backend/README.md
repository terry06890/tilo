# Files
-   **tolData**:   Holds scripts for generating the tree-of-life database
-   **tilo.py**:   WSGI script that serves data from the tree-of-life database. <br>
    Note: Using WSGI instead of CGI to avoid starting a new process for each request.
-   **server.py**: Basic dev server that serves the WSGI script and image files
