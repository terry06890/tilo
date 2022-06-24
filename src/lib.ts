
/*
 * Project-wide types/classes
 */

// Used for tree-of-life representation
// Maps tree-of-life node names to node objects
export type TolMap = Map<string, TolNode>;
// Represents a tree-of-life node
export class TolNode {
	otolId: string | null;
	children: string[];
	parent: string | null;
	tips: number;
	pSupport: boolean;
	commonName: null | string;
	imgName: null | string | [string, string] | [null, string] | [string, null];
	constructor(children: string[] = [], parent = null, tips = 0, pSupport = false){
		this.otolId = null;
		this.children = children;
		this.parent = parent;
		this.tips = tips;
		this.pSupport = pSupport;
		this.commonName = null;
		this.imgName = null;
	}
}
// Used for server search-responses
export type SearchSugg = {name: string, canonicalName: string | null};
	// Represents a search-string suggestion
export type SearchSuggResponse = {suggs: SearchSugg[], hasMore: boolean};
	// Holds search suggestions and an indication of if there was more
// Used for server info-responses
export type DescInfo = {text: string, wikiId: number, fromRedirect: boolean, fromDbp: boolean};
export type ImgInfo = {id: number, src: string, url: string, license: string, artist: string, credit: string}
export type TileInfoResponse = {
	tolNode: null | TolNode,
	descData: null | DescInfo | [DescInfo, DescInfo],
	imgData: null | ImgInfo | [ImgInfo, ImgInfo],
};

// Used by auto-mode and tutorial
export type Action =
	'expand' | 'collapse' | 'expandToView' | 'unhideAncestor' |
	'tileInfo' | 'search' | 'autoMode' | 'settings' | 'help';
//
export type UiOptions = {
	// Shared styling
	borderRadius: number, // CSS border-radius value, in px
	shadowNormal: string, // CSS box-shadow value
	shadowHovered: string,
	shadowFocused: string,
	// Styling for App
	appBgColor: string, // CSS color
	titleBarBgColor: string, // CSS color
	mainTileMargin: number, // px
	// Styling for tiles
	textColor: string, // CSS color
	childQtyColors: [number, string][],
		// Specifies, for an increasing sequence of minimum-child-quantity values, CSS colors to use
		//eg: [[1, 'green'], [10, 'orange'], [100, 'red']]
	infoIconSz: number, // px
	infoIconMargin: number, // px
	leafPadding: number, // px
	leafHeaderFontSz: number, // px
	nonleafBgColors: string[],
		// Specifies CSS colors to use at various tree depths
		// With N strings, tiles at depth M use the color at index M % N
	nonleafHeaderFontSz: number, // px
	nonleafHeaderBgColor: string, // CSS color
	// Styling for other components
	infoModalImgSz: number, // px
	ancestryBarBgColor: string, // CSS color
	ancestryBarImgSz: number, // px
	ancestryTileGap: number, // Gap between ancestor tiles, in px
	tutPaneSz: number, // px
	tutPaneBgColor: string, // CSS color
	// Timing related
	clickHoldDuration: number, // Time after mousedown when a click-and-hold is recognised, in ms
	transitionDuration: number, // ms
	autoActionDelay: number, // Time between auto-mode actions, in ms
	// Other
	useReducedTree: boolean,
	searchSuggLimit: number, // Max number of search suggestions
	jumpToSearchedNode: boolean,
	tutorialSkip: boolean,
	disabledActions: Set<Action>,
	scrollGap: number, // Size of scroll bar, in px
};
