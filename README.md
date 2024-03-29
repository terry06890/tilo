# Tilo

A visual explorer for the biological Tree of Life.
[Available online](https://terryt.dev/tilo/).

## Project Overview

The UI is largely coded in Typescript, using the [Vue](https://vuejs.org)
framework, with [Vite](https://vitejs.dev) as the build tool. Much of
the styling is done using [Tailwind](https://tailwindcss.com). Packages
are managed using [npm](https://www.npmjs.com) and [Node.js](https://nodejs.org).

On the server side, tree data is served and generated using Python, with
packages managed using [Pip](https://pypi.org/project/pip). Tree data is
stored using [Sqlite](https://www.sqlite.org).

## Files

### Project Level
-   **package.json**:       Contains npm project information, such as package dependencies.
-   **package-lock.json**:  Auto-generated by npm. Used for replicable installations.
-   **LICENCE.txt**:        This project's license (MIT).
### Client &amp; Server
-   **src**:                Contains most of the client-side code.
-   **index.html**:         Holds code for the main page, into which code from 'src' will be included.
-   **public**:             Contains files to be copied unchanged in the production-build of the UI.
-   **backend**:            Contains code for the server, and for generating tree-of-life data.
### Configuration
-   **vite.config.js**:     For configuring Vite.
-   **tailwind.config.js**: For configuring Tailwind.
-   **postcss.config.js**:  For configuring Tailwind.
-   **tsconfig.json**:      For configuring Typescript.
### Other
-   **.gitignore**:         Lists files to be ignored if using [Git](https://git-scm.com/downloads).
-   **DEPLOY.md**:          Instructions for deployment on an Apache server on Ubuntu.
-   **prebuild.sh**:        Bash script for automating some steps of deployment.

## Setup Instructions

Note: Running your own version of the client and server should be straightforward,
but generating the database takes a long time. More details are
in `backend/tol_data/README.md`.

### Client Side
1.  If you don't have npm or Node.js installed, you can download a Node installer from
    <https://nodejs.org/en/download>, which includes npm. This project was coded using version 16.
1.  In this directory, run the command `npm install`, which install packages listed in
    package.json, creating a `node_modules` directory to hold them.

### Server Side
1.  If you don't have Python 3 installed, see <https://www.python.org/downloads>.
    The package manager Pip is included.
1.  The database used by the server is generated using scripts in `backend/tol_data/`.
    See it's README for instructions. Package dependencies are listed in `backend/requirements.txt`.
    They can be installed using `pip install -r requirements.txt`.

    If you want to keep the installed package separate from your system's packages,
    it's common practice to use [venv](https://docs.python.org/3/tutorial/venv.html).

### Running Tilo
1.  In `backend/`, run `./server.py`, which starts a basic HTTP server that provides
    tree-of-life data on port 8000.
1.  In this directory, or somewhere in `src/`, run `npm run dev`. This starts a dev server that
    provides Tilo's user interface on port 3000.
1.  Open a web browser, and navigate to <http://localhost:3000>.

## Deploying the Website
This is significantly dependent on the server platform. `DEPLOY.md` contains
instructions for deployment on an Apache server on an Ubuntu system.

## Licence

Tilo is licensed under the [MIT Licence](https://github.com/terry06890/tilo/blob/main/LICENCE.txt).
