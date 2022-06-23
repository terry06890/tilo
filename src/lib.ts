
/*
 * Types/classes
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

/*
 * General utility functions
 */

export type Breakpoint = 'sm' | 'md' | 'lg'; // These represent screen sizes
export function getBreakpoint(): Breakpoint {
	let w = window.innerWidth;
	if (w < 768){
		return 'sm';
	} else if (w < 1024){
		return 'md';
	} else {
		return 'lg';
	}
}

// Returns [0 ... len]
export function range(len: number): number[] {
	return [...Array(len).keys()];
}
// Returns sum of array values
export function arraySum(array: number[]): number {
	return array.reduce((x,y) => x+y);
}
// Returns an array of increasing evenly-spaced numbers from 'start' to 'end' with size 'size'
export function linspace(start: number, end: number, size: number): number[] {
	let step = (end - start) / (size - 1);
	let ar = [];
	for (let i = 0; i < size; i++){
		ar.push(start + step * i);
	}
	return ar;
}
// Returns array copy with vals clipped to within [min,max], redistributing to compensate
// Returns null on failure
export function limitVals(arr: number[], min: number, max: number): number[] | null {
	let vals = [...arr];
	let clipped = new Array(vals.length).fill(false);
	let owedChg = 0; // Stores total change made after clipping values
	while (true){
		// Clip values
		for (let i = 0; i < vals.length; i++){
			if (clipped[i]){
				continue;
			}
			if (vals[i] < min){
				owedChg += vals[i] - min;
				vals[i] = min;
				clipped[i] = true;
			} else if (vals[i] > max){
				owedChg += vals[i] - max;
				vals[i] = max;
				clipped[i] = true;
			}
		}
		if (Math.abs(owedChg) < Number.EPSILON){
			return vals;
		}
		// Compensate for changes made
		let indicesToUpdate = (owedChg > 0) ?
			range(vals.length).filter(idx => vals[idx] < max) :
			range(vals.length).filter(idx => vals[idx] > min);
		if (indicesToUpdate.length == 0){
			return null;
		}
		for (let i of indicesToUpdate){
			vals[i] += owedChg / indicesToUpdate.length;
		}
		owedChg = 0;
	}
}
// Usable to iterate through possible int arrays with ascending values in the range 0 to maxLen-1, starting with [0]
	// eg: With maxLen 3, updates [0] to [0,1], then to [0,2], then [0,1,2]
// Returns false when there is no next array
export function updateAscSeq(seq: number[], maxLen: number): boolean {
	// Try increasing last element, then preceding elements, then extending the array
	let i = seq.length - 1;
	while (true){
		if (i > 0 && seq[i] < (maxLen - 1) - (seq.length - 1 - i)){
			seq[i]++;
			return true;
		} else if (i > 0){
			i--;
		} else {
			if (seq.length < maxLen){
				seq.push(0);
				seq.splice(0, seq.length, ...range(seq.length));
				return true;
			} else {
				return false;
			}
		}
	}
}
// Given a non-empty array of non-negative weights, returns an array index chosen with weighted pseudorandomness
// Returns null if array contains all zeros
export function randWeightedChoice(weights: number[]): number | null {
	let thresholds = Array(weights.length);
	let sum = 0;
	for (let i = 0; i < weights.length; i++){
		sum += weights[i];
		thresholds[i] = sum;
	}
	let rand = Math.random();
	for (let i = 0; i < weights.length; i++){
		if (rand <= thresholds[i] / sum){
			return i;
		}
	}
	return null;
}
// Returns a string with words first-letter capitalised
export function capitalizeWords(str: string){
	str = str.replace(/\b\w/g, x => x.toUpperCase()); // '\b' matches word boundary, '\w' is like [a-zA-Z0-9_]
	str = str.replace(/(\w)'S/, '$1\'s'); // Avoid cases like "traveler's tree" -> "Traveler'S Tree"
	return str;
}
// Dynamically obtains scroll bar width
// From stackoverflow.com/questions/13382516/getting-scroll-bar-width-using-javascript
export function getScrollBarWidth(){
	// Create hidden outer div
	let outer = document.createElement('div');
	outer.style.visibility = 'hidden';
	outer.style.overflow = 'scroll';
	document.body.appendChild(outer);
	// Create inner div
	let inner = document.createElement('div');
	outer.appendChild(inner);
	// Get width difference
	let scrollBarWidth = outer.offsetWidth - inner.offsetWidth;
	// Remove temporary divs
	outer.parentNode!.removeChild(outer);
	//
	return scrollBarWidth;
}
