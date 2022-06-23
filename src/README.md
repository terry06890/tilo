# Files
-   main.ts: Included by ../index.html. Creates the main Vue component.
-   App.vue: The main Vue component.
-   components:
    -   Tile.vue:          Displays a tree-of-life node, and can include child nodes.
    -   AncestryBar.vue:   Displays ancestors of the top-level Tile.
    -   TutorialPane.vue:  Displays tutorial content.
    -   TileInfoModal.vue: Modal displaying info about a Tile's node.
    -   SearchModal.vue:   Modal with a search bar.
    -   SettingsModal:     Modal displaying configurable settings.
    -   HelpModal.vue:     Modal displaying help info.
    -   RButton.vue:       Basic button component.
    -   icon:              Contains components that display SVG icons.
-   layout.ts: Contains code for laying out Tiles.
-   lib.ts:    Contains classes/types and utility functions.
-   index.css: Included by main.ts. Provides Tailwind's CSS classes.
-   env.d.ts:  From Vite's template files.