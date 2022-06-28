/*
 * Project-wide types/classes
 */

// Represents a tree-of-life node
export class TolNode {
	otolId: string | null;
	children: string[];
	parent: string | null;
	tips: number;
	pSupport: boolean;
	commonName: null | string;
	imgName: null | string |
		[string, string] | [null, string] | [string, null]; // Pairs represent compound-images
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
// Maps TolNode names to TolNode objects
export type TolMap = Map<string, TolNode>;

// For server requests
const SERVER_URL = 'http://localhost:8000/cgi-bin/data.py'
export async function getServerResponse(params: string){
	// Construct URL
	let url = new URL(SERVER_URL);
	url.search = params;
	// Query server
	let responseObj;
	try {
		let response = await fetch(url.toString());
		responseObj = await response.json();
	} catch (error){
		console.log(`Error with querying ${url}: ${error}`);
		return null;
	}
	return responseObj;
}
const SERVER_IMG_PATH = '/img/'
export function getImagePath(imgName: string): string {
	return SERVER_IMG_PATH + imgName.replaceAll('\'', '\\\'');
}
// For server search responses
export type SearchSugg = { // Represents a search-string suggestion
	name: string,
	canonicalName: string | null,
};
export type SearchSuggResponse = { // Holds search suggestions and an indication of if there was more
	suggs: SearchSugg[],
	hasMore: boolean,
};
// For server tile-info responses
export type DescInfo = {
	text: string,
	wikiId: number,
	fromRedirect: boolean,
	fromDbp: boolean,
};
export type ImgInfo = {
	id: number,
	src: string,
	url: string,
	license: string,
	artist: string,
	credit: string,
};
export type NodeInfo = {
	tolNode: TolNode,
	descInfo: null | DescInfo,
	imgInfo: null | ImgInfo,
};
export type InfoResponse = {
	nodeInfo: NodeInfo,
	subNodesInfo: [] | [NodeInfo, NodeInfo],
};

// Used by auto-mode and tutorial
export type Action =
	'expand' | 'collapse' | 'expandToView' | 'unhideAncestor' |
	'tileInfo' | 'search' | 'autoMode' | 'settings' | 'help';

// Project-wide configurable options (supersets the user-configurable settings)
export type UiOptions = {
	// Shared coloring/sizing
	textColor: string, // CSS color
	textColorAlt: string,
	bgColor: string,
	bgColorLight: string,
	bgColorDark: string,
	bgColorLight2: string,
	bgColorDark2: string,
	bgColorAlt: string,
	bgColorAltDark: string,
	altColor: string,
	altColorDark: string,
	borderRadius: number, // CSS border-radius value, in px
	shadowNormal: string, // CSS box-shadow value
	shadowHovered: string,
	shadowFocused: string,
	// Component coloring
	childQtyColors: [number, string][],
		// Specifies, for an increasing sequence of minimum-child-quantity values, CSS colors to use
		//eg: [[1, 'green'], [10, 'orange'], [100, 'red']]
	nonleafBgColors: string[],
		// Specifies CSS colors to use at various tree depths
		// With N strings, tiles at depth M use the color at index M % N
	nonleafHeaderColor: string, // CSS color
	ancestryBarBgColor: string,
	// Component sizing
	ancestryBarBreadth: number, // px (fixed value needed for transitions)
	tutPaneSz: number, // px (fixed value needed for transitions)
	scrollGap: number, // Size of scroll bar, in px
	// Timing related
	clickHoldDuration: number, // Time after mousedown when a click-and-hold is recognised, in ms
	transitionDuration: number, // ms
	animationDelay: number, // Time between updates during transitions/resizes/etc, in ms
	autoActionDelay: number, // Time between auto-mode actions (incl transitions), in ms
	// Other
	useReducedTree: boolean,
	searchSuggLimit: number, // Max number of search suggestions
	searchJumpMode: boolean,
	tutorialSkip: boolean,
	disabledActions: Set<Action>,
	useDblClick: boolean,
};
