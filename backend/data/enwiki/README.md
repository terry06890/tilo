Downloaded Files
================
-   enwiki\_content/enwiki-20220420-pages-articles-*.xml.gz:
    Obtained via https://dumps.wikimedia.org/backup-index.html (site suggests downloading from a mirror).
    Contains text content and metadata for pages in English Wikipedia (current revision only, excludes talk pages).
    Some file content and format information was available from
    https://meta.wikimedia.org/wiki/Data_dumps/What%27s_available_for_download.
-   enwiki-20220420-page.sql.gz:
    Obtained like above. Contains page-table information including page id, namespace, title, etc.
    Format information was found at https://www.mediawiki.org/wiki/Manual:Page_table.
-   enwiki-20220420-redirect.sql.gz:
    Obtained like above. Contains page-redirection info.
    Format information was found at https://meta.wikimedia.org/wiki/Data_dumps/What%27s_available_for_download.

Generated Files
===============
-   enwiki\_content/enwiki-*.xml and enwiki-*.sql:
    Uncompressed versions of downloaded files.
-   enwikiData.db:
    An sqlite database representing data from the enwiki dump files.
    Generation: 
    1   Install python, and packages mwsql, mwxml, and mwparsefromhell. Example:
        1   On Ubuntu, install python3, python3-pip, and python3-venv via `apt-get update; apt-get ...`.
        2   Create a virtual environment in which to install packages via `python3 -m venv .venv`.
        3   Activate the virtual environment via `source .venv/bin/activate`.
        4   Install mwsql, mwxml, and mwparsefromhell via `pip install mwsql mwxml mwparsefromhell`.
    2   Run genPageData.py (still under the virtual environment), which creates the database,
        reads from the page dump, and creates a 'pages' table.
    3   Run genRedirectData.py, which creates a 'redirects' table, using information in the redirects dump,
        and page ids from the 'pages' table.
    4   Run genDescData.py, which reads the page-content xml dumps, and the 'pages' and 'redirects' tables,
        and associates page ids with (potentially redirect-resolved) pages, and attempts to parse some
        wikitext within those pages to obtain the first descriptive paragraph, with markup removed.
-   .venv:
    Provides a python virtual environment for packages needed to generate data.
