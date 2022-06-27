# Tilo
Provides an interactive visualisation of the biological Tree of Life.

## Files
-   package.json:       Contains project information, including package dependencies.
-   src:                Contains most of the client-side code.
-   index.html:         Holds code for the main page, into which code from 'src' will be included.
-   backend:            Contains code for the server, and generating tree-of-life data
-   vite.config.js:     For configuring Vite.
-   tailwind.config.js: For configuring Tailwind.
-   postcss.config.js:  For configuring Tailwind.
-   tsconfig.json:      For configuring Typescript.
-   .gitignore:         Lists files to be ignored by Git.
-   public:             Contains files to be copied unchanged when building for production.

## Overview
(TODO)

## Setup Instructions
(TODO)

##

During development, a client request to the server on the same machine
would be blocked due to the Same Origin Policy. This is avoided by
adding an 'Access-Control-Allow-Origin: *' header to server responses.
This should be disabled during production.
