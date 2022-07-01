This directory holds files used to generate data.db, which contains tree-of-life data.

# Tables
## Tree Structure data
-   `nodes` <br>
    Format : `name TEXT PRIMARY KEY, id TEXT UNIQUE, tips INT` <br>
    Represents a tree-of-life node. `tips` represents the number of no-child descendants.
-   `edges` <br>
    Format: `parent TEXT, child TEXT, p_support INT, PRIMARY KEY (parent, child)` <br>
    `p_support` is 1 if the edge has 'phylogenetic support', and 0 otherwise
## Node name data
-   `eol_ids` <br>
    Format: `id INT PRIMARY KEY, name TEXT` <br>
    Associates an EOL ID with a node's name.
-   `names` <br>
    Format: `name TEXT, alt_name TEXT, pref_alt INT, src TEXT, PRIMARY KEY(name, alt_name)` <br>
    Associates a node with alternative names.
    `pref_alt` is 1 if the alt-name is the most 'preferred' one.
    `src` indicates the dataset the alt-name was obtained from (can be 'eol', 'enwiki', or 'picked').
## Node description data
-   `wiki_ids` <br>
    Format: `name TEXT PRIMARY KEY, id INT, redirected INT` <br>
    Associates a node with a wikipedia page ID.
    `redirected` is 1 if the node was associated with a different page that redirected to this one.
-   `descs` <br>
    Format: `wiki_id INT PRIMARY KEY, desc TEXT, from_dbp INT` <br>
    Associates a wikipedia page ID with a short-description.
    `from_dbp` is 1 if the description was obtained from DBpedia, and 0 otherwise.
## Node image data
-   `node_imgs` <br>
    Format: `name TEXT PRIMARY KEY, img_id INT, src TEXT` <br>
    Associates a node with an image.
-   `images` <br>
    Format: `id INT, src TEXT, url TEXT, license TEXT, artist TEXT, credit TEXT, PRIMARY KEY (id, src)` <br>
    Represents an image, identified by a source ('eol', 'enwiki', or 'picked'), and a source-specific ID.
-   `linked_imgs` <br>
    Format: `name TEXT PRIMARY KEY, otol_ids TEXT` <br>
    Associates a node with an image from another node.
    `otol_ids` can be an otol ID, or two comma-separated otol IDs or empty strings.
        The latter is used for compound nodes.
## Reduced tree data
-   `nodes_t`, `nodes_i`, `nodes_p` <br>
    These are like `nodes`, but describe the nodes for various reduced trees.
-   `edges_t`, `edges_i`, `edges_p` <br>
    Like `edges` but for reduced trees.

# Generating the Database

For the most part, these steps should be done in order.

As a warning, the whole process takes a lot of time and file space. The tree will probably
have about 2.5 billion nodes. Downloading the images will take several days, and occupy over
200 GB. And if you want good data, you'll need to do some manual review, which can take weeks.

## Environment
The scripts are written in python and bash.
Some of the python scripts require third-party packages:
-   jsonpickle: For encoding class objects as JSON.
-   requests: For downloading data.
-   PIL: For image processing.
-   tkinter: For providing a basic GUI to review images.
-   mwxml, mwparserfromhell: For parsing Wikipedia dumps.

## Generate tree structure data
1.  Obtain files in otol/, as specified in it's README.
2.  Run genOtolData.py, which creates data.db, and adds the `nodes` and `edges` tables,
    using data in otol/. It also uses these files, if they exist:
    -   pickedOtolNames.txt: Has lines of the form `name1|otolId1`. Some nodes in the
        tree may have the same name (eg: Pholidota can refer to pangolins or orchids).
        Normally, such nodes will get the names 'name1', 'name1 [2]', 'name1 [3], etc.
        This file can be used to manually specify which node should be named 'name1'.

## Generate node name data
1.  Obtain 'name data files' in eol/, as specified in it's README.
2.  Run genEolNameData.py, which adds the `names` and `eol_ids` tables, using data in
    eol/ and the `nodes` table. It also uses these files, if they exist:
    -   pickedEolIds.txt: Has lines of the form `nodeName1|eolId1` or `nodeName1|`.
        Specifies node names that should have a particular EOL ID, or no ID.
        Quite a few taxons have ambiguous names, and may need manual correction.
        For example, Viola may resolve to a taxon of butterflies or of plants.
    -   pickedEolAltsToSkip.txt: Has lines of the form `nodeName1|altName1`.
        Specifies that a node's alt-name set should exclude altName1.

## Generate node description data
### Get data from DBpedia
1.  Obtain files in dbpedia/, as specified in it's README.
2.  Run genDbpData.py, which adds the `wiki_ids` and `descs` tables, using data in
    dbpedia/ and the `nodes` table. It also uses these files, if they exist:
    -   pickedEnwikiNamesToSkip.txt: Each line holds the name of a node for which
        no description should be obtained. Many node names have a same-name
        wikipedia page that describes something different (eg: Osiris).
    -   pickedDbpLabels.txt: Has lines of the form `nodeName1|label1`.
        Specifies node names that should have a particular associated page label.
### Get data from Wikipedia
1.  Obtain 'description database files' in enwiki/, as specified in it's README.
2.  Run genEnwikiDescData.py, which adds to the `wiki_ids` and `descs` tables,
    using data in enwiki/ and the `nodes` table.
    It also uses these files, if they exist:
    -   pickedEnwikiNamesToSkip.txt: Same as with genDbpData.py.
    -   pickedEnwikiLabels.txt: Similar to pickedDbpLabels.txt.

## Generate node image data
### Get images from EOL
1.  Obtain 'image metadata files' in eol/, as specified in it's README.
2.  In eol/, run downloadImgs.py, which downloads images (possibly multiple per node),
    into eol/imgsForReview, using data in eol/, as well as the `eol_ids` table.
3.  In eol/, run reviewImgs.py, which interactively displays the downloaded images for
    each node, providing the choice of which to use, moving them to eol/imgs/.
    Uses `names` and `eol_ids` to display extra info.
### Get images from Wikipedia
1.  In enwiki/, run genImgData.py, which looks for wikipedia image names for each node,
    using the `wiki_ids` table, and stores them in a database.
2.  In enwiki/, run downloadImgLicenseInfo.py, which downloads licensing information for
    those images, using wikipedia's online API.
3.  In enwiki/, run downloadImgs.py, which downloads 'permissively-licensed'
    images into enwiki/imgs/.
### Merge the image sets
1.  Run reviewImgsToGen.py, which displays images from eol/imgs/ and enwiki/imgs/,
    and enables choosing, for each node, which image should be used, if any,
    and outputs choice information into imgList.txt. Uses the `nodes`,
    `eol_ids`, and `wiki_ids` tables (as well as `names` to display extra info).
2.  Run genImgs.py, which creates cropped/resized images in img/, from files listed in
    imgList.txt and located in eol/ and enwiki/, and creates the `node_imgs` and
    `images` tables. If pickedImgs/ is present, images within it are also used. <br>
    The outputs might need to be manually created/adjusted:
    -   An input image might have no output produced, possibly due to
        data incompatibilities, memory limits, etc. A few input image files
        might actually be html files, containing a 'file not found' page.
    -   An input x.gif might produce x-1.jpg, x-2.jpg, etc, instead of x.jpg.
    -   An input image might produce output with unexpected dimensions.
        This seems to happen when the image is very large, and triggers a
        decompression bomb warning.
    The result might have as many as 150k images, with about 2/3 of them
    being from wikipedia.
### Add more image associations
1.  Run genLinkedImgs.py, which tries to associate nodes without images to
    images of it's children. Adds the `linked_imgs` table, and uses the
    `nodes`, `edges`, and `node_imgs` tables.

## Do some post-processing
1.  Run genEnwikiNameData.py, which adds more entries to the `names` table,
    using data in enwiki/, and the `names` and `wiki_ids` tables.
2.  Optionally run addPickedNames.py, which allows adding manually-selected name data to
    the `names` table, as specified in pickedNames.txt.
    -   pickedNames.txt: Has lines of the form `nodeName1|altName1|prefAlt1`.
        These correspond to entries in the `names` table. `prefAlt` should be 1 or 0.
        A line like `name1|name1|1` causes a node to have no preferred alt-name.
3.  Run genReducedTrees.py, which generates multiple reduced versions of the tree,
    adding the `nodes_*` and `edges_*` tables, using `nodes` and `names`. Reads from
    pickedNodes.txt, which lists names of nodes that must be included (1 per line).
    The original tree isn't used for web-queries, as some nodes would have over 
    10k children, which can take a while to render (took over a minute in testing).
