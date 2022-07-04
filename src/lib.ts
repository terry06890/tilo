/*
 * Project-wide types/classes
 */

import {TolNode} from './tol';
import {LayoutOptions} from './layout';
import {getBreakpoint, Breakpoint, getScrollBarWidth, onTouchDevice} from './util';

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
	subNodesInfo: [] | [NodeInfo | null, NodeInfo | null],
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
	// Device-info-like
	touchDevice: boolean,
	breakpoint: Breakpoint,
	// Other
	tree: 'trimmed' | 'images' | 'picked',
	searchSuggLimit: number, // Max number of search suggestions
	searchJumpMode: boolean,
	tutorialSkip: boolean,
	disabledActions: Set<Action>,
	disableShortcuts: boolean,
};
// Option defaults
export function getDefaultLytOpts(): LayoutOptions {
	let screenSz = getBreakpoint();
	return {
		tileSpacing: screenSz == 'sm' ? 6 : 9, //px
		headerSz: screenSz == 'sm' ? 18 : 22, // px
		minTileSz: 50, // px
		maxTileSz: 200, // px
		// Layout-algorithm related
		layoutType: 'sweep', // 'sqr' | 'rect' | 'sweep'
		rectMode: 'auto first-row', // 'horz' | 'vert' | 'linear' | 'auto' | 'auto first-row'
		rectSensitivity: 0.9, // Between 0 and 1
		sweepMode: 'left', // 'left' | 'top' | 'shorter' | 'auto'
		sweptNodesPrio: 'sqrt', // 'linear' | 'sqrt' | 'pow-2/3'
		sweepToParent: 'fallback', // 'none' | 'prefer' | 'fallback'
	};
}
export function getDefaultUiOpts(lytOpts: LayoutOptions): UiOptions {
	let screenSz = getBreakpoint();
	// Reused option values
	let textColor = '#fafaf9', textColorAlt = '#1c1917';
	let bgColor = '#292524',
		bgColorLight = '#44403c', bgColorDark = '#1c1917',
		bgColorLight2 = '#57534e', bgColorDark2 = '#0e0c0b',
		bgColorAlt = '#f5f5f4', bgColorAltDark = '#a8a29e';
	let altColor = '#a3e623', altColorDark = '#65a30d';
	let accentColor = '#f59e0b';
	let scrollGap = getScrollBarWidth();
	//
	return {
		// Shared coloring/sizing
		textColor, textColorAlt,
		bgColor, bgColorLight, bgColorDark, bgColorLight2, bgColorDark2, bgColorAlt, bgColorAltDark,
		altColor, altColorDark,
		borderRadius: 5, // px
		shadowNormal: '0 0 2px black',
		shadowHovered: '0 0 1px 2px ' + altColor,
		shadowFocused: '0 0 1px 2px ' + accentColor,
		// Component coloring
		childQtyColors: [[1, 'greenyellow'], [10, 'orange'], [100, 'red']],
		nonleafBgColors: [bgColorLight, bgColorLight2],
		nonleafHeaderColor: bgColorDark,
		ancestryBarBgColor: bgColorLight,
		// Component sizing
		ancestryBarBreadth: (screenSz == 'sm' ? 80 : 100) + lytOpts.tileSpacing*2, // px
		tutPaneSz: 180, // px
		scrollGap,
		// Timing related
		clickHoldDuration: 400, // ms
		transitionDuration: 300, // ms
		animationDelay: 100, // ms
		autoActionDelay: 500, // ms
		// Device-info-like
		touchDevice: onTouchDevice(),
		breakpoint: getBreakpoint(),
		// Other
		tree: 'images',
		searchSuggLimit: 10,
		searchJumpMode: false,
		tutorialSkip: false,
		disabledActions: new Set() as Set<Action>,
		disableShortcuts: false,
	};
}
// Used in Settings.vue, and when saving to localStorage
export type OptionType = 'LYT' | 'UI';
