This directory is used for adding additional, manually-picked images,
to the server's dataset, overriding any from eol and enwiki. If used,
it is expected to contain image files, and a metadata.txt file that
holds metadata.

Possible Files
==============
-   Image files
-   metadata.txt <br>
    Contains lines with the format filename|url|license|artist|credit.
    The filename should be a tree-of-life node name, with an image
    extension.  Other fields correspond to those in the 'images' table.
