This directory holds files used to generate the tree-of-life database data.db.

# Database Tables
## Tree Structure
-   `nodes` <br>
    Format: `name TEXT PRIMARY KEY, id TEXT UNIQUE, tips INT` <br>
    Represents a tree-of-life node. `tips` holds the number of no-child descendants
-   `edges` <br>
    Format: `parent TEXT, child TEXT, p_support INT, PRIMARY KEY (parent, child)` <br>
    `p_support` is 1 if the edge has 'phylogenetic support', and 0 otherwise
## Node Mappings
-   `eol_ids` <br>
    Format: `name TEXT PRIMARY KEY, id INT` <br>
    Associates nodes with EOL IDs
-   `wiki_ids` <br>
    Format: `name TEXT PRIMARY KEY, id INT` <br>
    Associates nodes with wikipedia page IDs
## Node Vernacular Names
-   `names` <br>
    Format: `name TEXT, alt_name TEXT, pref_alt INT, src TEXT, PRIMARY KEY(name, alt_name)` <br>
    Associates a node with alternative names.
    `pref_alt` is 1 if the alt-name is the most 'preferred' one.
    `src` indicates the dataset the alt-name was obtained from (can be 'eol', 'enwiki', or 'picked').
## Node Descriptions
-   `descs` <br>
    Format: `wiki_id INT PRIMARY KEY, desc TEXT, from_dbp INT` <br>
    Associates a wikipedia page ID with a short-description.
    `from_dbp` is 1 if the description was obtained from DBpedia, and 0 otherwise.
## Node Images
-   `node_imgs` <br>
    Format: `name TEXT PRIMARY KEY, img_id INT, src TEXT` <br>
    Associates a node with an image.
-   `images` <br>
    Format: `id INT, src TEXT, url TEXT, license TEXT, artist TEXT, credit TEXT, PRIMARY KEY (id, src)` <br>
    Represents an image, identified by a source ('eol', 'enwiki', or 'picked'), and a source-specific ID.
-   `linked_imgs` <br>
    Format: `name TEXT PRIMARY KEY, otol_ids TEXT` <br>
    Associates a node with an image from another node.
    `otol_ids` can be an otol ID, or (for compound nodes) two comma-separated strings that may be otol IDs or empty.
## Reduced Trees
-   `nodes_t`, `nodes_i`, `nodes_p` <br>
    These are like `nodes`, but describe nodes of reduced trees.
-   `edges_t`, `edges_i`, `edges_p` <br>
    Like `edges` but for reduced trees.
## Other
-   `node_iucn` <br>
    Format: `name TEXT PRIMARY KEY, iucn TEXT` <br>
    Associates nodes with IUCN conservation status strings (eg: 'endangered')
-   `node_pop` <br>
    Format: `name TEXT PRIMARY KEY, pop INT` <br>
    Associates nodes with popularity values (higher means more popular)

# Generating the Database

As a warning, the whole process takes a lot of time and file space. The
tree will probably have about 2.6 million nodes. Downloading the images
takes several days, and occupies over 200 GB.

## Generate Tree Structure Data
1.  Obtain 'tree data files' in otol/, as specified in it's README.
2.  Run `gen_otol_data.py`, which creates data.db, and adds the `nodes` and `edges` tables,
    using data in otol/. It also uses these files, if they exist:
    -   `picked_otol_names.txt`: Has lines of the form `name1|otolId1`.
        Can be used to override numeric suffixes added to same-name nodes.

## Generate Dataset Mappings
1.  Obtain 'taxonomy data files' in otol/, 'mapping files' in eol/,
    files in wikidata/, and 'dump-index files' in enwiki/, as specified
    in their READMEs.
2.  Run `gen_mapping_data.py`, which adds the `eol_ids` and `wiki_ids` tables,
    as well as `node_iucn`. It uses the files obtained above, the `nodes` table,
    and 'picked mappings' files, if they exist.
    -   `picked_eol_ids.txt` contains lines like `3785967|405349`, specifying
        an otol ID and an eol ID to map it to. The eol ID can be empty,
        in which case the otol ID won't be mapped.
    -   `picked_wiki_ids.txt` and `picked_wiki_ids_rough.txt` contain lines like
        `5341349|Human`, specifying an otol ID and an enwiki title,
        which may contain spaces. The title can be empty.

## Generate Node Name Data
1.  Obtain 'name data files' in eol/, and 'description database files' in enwiki/,
    as specified in their READMEs.
2.  Run `gen_name_data.py`, which adds the `names` table, using data in eol/ and enwiki/,
    along with the `nodes`, `eol_ids`, and `wiki_ids` tables. <br>
    It also uses `picked_names.txt`, if it exists. This file can hold lines like
    `embryophyta|land plant|1`, specifying a node name, an alt-name to add for it,
    and a 1 or 0 indicating whether it is a 'preferred' alt-name. The last field
    can be empty, which indicates that the alt-name should be removed, or, if the
    alt-name is the same as the node name, that no alt-name should be preferred.

## Generate Node Description Data
1.  Obtain files in dbpedia/, as specified in it's README.
2.  Run `gen_desc_data.py`, which adds the `descs` table, using data in dbpedia/ and
    enwiki/, and the `nodes` table.

## Generate Node Images Data
### Get images from EOL
1.  Obtain 'image metadata files' in eol/, as specified in it's README.
2.  In eol/, run `download_imgs.py`, which downloads images (possibly multiple per node),
    into eol/imgs_for_review, using data in eol/, as well as the `eol_ids` table.
    By default, more images than needed are downloaded for review. To skip this, set
    the script's MAX_IMGS_PER_ID to 1.
3.  In eol/, run `review_imgs.py`, which interactively displays the downloaded images for
    each node, providing the choice of which (if any) to use, moving them to eol/imgs/.
    Uses `names` and `eol_ids` to display extra info. If MAX_IMGS_PER_ID was set to 1 in
    the previous step, you can skip review by renaming the image folder.
### Get Images from Wikipedia
1.  In enwiki/, run `gen_img_data.py`, which looks for wikipedia image names for each node,
    using the `wiki_ids` table, and stores them in a database.
2.  In enwiki/, run `download_img_license_info.py`, which downloads licensing information for
    those images, using wikipedia's online API.
3.  In enwiki/, run `download_imgs.py`, which downloads 'permissively-licensed'
    images into enwiki/imgs/.
### Merge the Image Sets
1.  Run `review_imgs_to_gen.py`, which displays images from eol/imgs/ and enwiki/imgs/,
    and enables choosing, for each node, which image should be used, if any,
    and outputs choice information into `img_list.txt`. Uses the `nodes`,
    `eol_ids`, and `wiki_ids` tables (as well as `names` to display extra info).
    To skip manual review, set REVIEW to 'none' in the script (the script will select any
    image, preferring ones from Wikipedia).
2.  Run `gen_imgs.py`, which creates cropped/resized images in img/, from files listed in
    `img_list.txt` and located in eol/ and enwiki/, and creates the `node_imgs` and
    `images` tables. If `picked_imgs/` is present, images within it are also used. <br>
    The outputs might need to be manually created/adjusted:
    -   An input image might have no output produced, possibly due to
        data incompatibilities, memory limits, etc. A few input image files
        might actually be html files, containing a 'file not found' page.
    -   An input x.gif might produce x-1.jpg, x-2.jpg, etc, instead of x.jpg.
    -   An input image might produce output with unexpected dimensions.
        This seems to happen when the image is very large, and triggers a
        decompression bomb warning.
### Add more Image Associations
1.  Run `gen_linked_imgs.py`, which tries to associate nodes without images to
    images of it's children. Adds the `linked_imgs` table, and uses the
    `nodes`, `edges`, and `node_imgs` tables.

## Generate Reduced Trees
1.  Run `gen_reduced_trees.py`, which generates multiple reduced versions of the tree,
    adding the `nodes_*` and `edges_*` tables, using `nodes`, `edges`, `wiki_ids`,
    `node_imgs`, `linked_imgs`, and `names`. Reads from `picked_nodes.txt`, which lists
    names of nodes that must be included (1 per line).

## Generate Node Popularity Data
1.  Obtain 'page view files' in enwiki/, as specified in it's README.
2.  Run `gen_pop_data.py`, which adds the `node_pop` table, using data in enwiki/,
    and the `wiki_ids` table.
