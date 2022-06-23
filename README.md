# Grid of Life

An interactive visualisation of the biological tree of life.

Each tile represents a group of organisms with a common ancestor.
-   Clicking on a tile expands it into tiles representing direct descendants.
    If there are too many other tiles, there might not be room to expand.
-   Clicking on an expanded tile collapses it back into one tile.
-   Double-clicking on a tile expands it to fill the whole view.
    Other tiles will be moved to the side.

# Files
-   package.json:       Contains project information, including what packages need to be installed.
-   src:                Contains most of the client-side code.
-   index.html:         Holds code for the main page, into which code from src/ will be included.
-   backend:            Contains code for running the server, and generating tree-of-life data
-   public:             Contains files to be copied unchanged when building for production.
-   tailwind.config.js: For configuring Tailwind.
-   postcss.config.js:  For configuring Tailwind.
-   tsconfig.json:      For configuring Typescript.
-   vite.config.js:     For configuring Vite.
-   .gitignore:         Lists files to be ignored by Git.

# Overview
# Instructions
