/*
 * Defines a global store for UI settings, palette colors, etc
 */

import {defineStore} from 'pinia';
import {Action} from './lib';
import {LayoutOptions} from './layout';
import {getBreakpoint, Breakpoint, getScrollBarWidth, onTouchDevice} from './util';

// ========== For store state ==========

export type StoreState = {
	// Device info
	touchDevice: boolean,
	breakpoint: Breakpoint,
	scrollGap: number, // Size of scroll bar, in px
	// Tree display
	tree: 'trimmed' | 'images' | 'picked',
	lytOpts: LayoutOptions,
	ancestryBarBreadth: number, // px (fixed value needed for transitions)
	tutPaneSz: number, // px (fixed value needed for transitions)
	// Search related
	searchSuggLimit: number, // Max number of search suggestions
	searchJumpMode: boolean,
	// Tutorial related
	tutorialSkip: boolean,
	disabledActions: Set<Action>,
	// Coloring
	color: {
		text: string, // CSS color
		textDark: string,
		textAlt: string,
		bg: string,
		bgLight: string,
		bgDark: string,
		bgLight2: string,
		bgDark2: string,
		bgAlt: string,
		bgAltDark: string,
		alt: string,
		altDark: string,
		accent: string,
	},
	childQtyColors: [number, string][],
		// Specifies, for an increasing sequence of minimum-child-quantity values, CSS colors to use
		//eg: [[1, 'green'], [10, 'orange'], [100, 'red']]
	nonleafBgColors: string[],
		// Specifies CSS colors to use at various tree depths
		// With N strings, tiles at depth M use the color at index M % N
	nonleafHeaderColor: string, // CSS color
	ancestryBarBgColor: string,
	// More styling
	borderRadius: number, // CSS border-radius value, in px
	shadowNormal: string, // CSS box-shadow value
	shadowHovered: string,
	shadowFocused: string,
	// Timing
	clickHoldDuration: number, // Time after mousedown when a click-and-hold is recognised, in ms
	transitionDuration: number, // ms
	animationDelay: number, // Time between updates during transitions/resizes/etc, in ms
	autoActionDelay: number, // Time between auto-mode actions (incl transitions), in ms
	// Other
	disableShortcuts: boolean,
	autoHide: boolean, // If true, leaf-click failure results in hiding an ancestor and trying again
};

function getDefaultState(): StoreState {
	const breakpoint = getBreakpoint();
	const scrollGap = getScrollBarWidth();
	const tileSpacing = breakpoint == 'sm' ? 6 : 9;
	const color = { // Note: For scrollbar colors on chrome, edit ./index.css
		text: '#fafaf9',      // stone-50
		textDark: '#a8a29e',  // stone-400
		textAlt: '#1c1917',   // stone-900
		bg: '#292524',        // stone-800
		bgLight: '#44403c',   // stone-700
		bgDark: '#1c1917',    // stone-900
		bgLight2: '#57534e',  // stone-600
		bgDark2: '#0e0c0b',   // darker version of stone-900
		bgAlt: '#f5f5f4',     // stone-100
		bgAltDark: '#d6d3d1', // stone-300
		alt: '#a3e635',       // lime-400
		altDark: '#65a30d',   // lime-600
		accent: '#f59e0b',    // amber-500
	};

	return {
		// Device related
		touchDevice: onTouchDevice(),
		breakpoint: breakpoint,
		scrollGap,
		// Tree display
		tree: 'images',
		lytOpts: {
			tileSpacing, //px
			headerSz: 22, // px
			minTileSz: breakpoint == 'sm' ? 50 : 80, // px
			maxTileSz: 200, // px
			// Layout-algorithm related
			layoutType: 'sweep', // 'sqr' | 'rect' | 'sweep'
			rectMode: 'auto first-row', // 'horz' | 'vert' | 'linear' | 'auto' | 'auto first-row'
			rectSensitivity: 0.9, // Between 0 and 1
			sweepMode: 'left', // 'left' | 'top' | 'shorter' | 'auto'
			sweptNodesPrio: 'sqrt', // 'linear' | 'sqrt' | 'pow-2/3'
			sweepToParent: breakpoint == 'sm' ? 'prefer' : 'fallback', // 'none' | 'prefer' | 'fallback'
		},
		ancestryBarBreadth: (breakpoint == 'sm' ? 80 : 100) + tileSpacing*2, // px
		tutPaneSz: 180, // px
		// Search related
		searchSuggLimit: 10,
		searchJumpMode: false,
		// Tutorial related
		tutorialSkip: false,
		disabledActions: new Set() as Set<Action>,
		// Coloring
		color,
		childQtyColors: [[1, 'greenyellow'], [10, 'orange'], [100, 'red']],
		nonleafBgColors: [color.bgLight, color.bgLight2],
		nonleafHeaderColor: color.bgDark,
		ancestryBarBgColor: color.bgLight,
		// More styling
		borderRadius: 5, // px
		shadowNormal: '0 0 2px black',
		shadowHovered: '0 0 1px 2px ' + color.alt,
		shadowFocused: '0 0 1px 2px ' + color.accent,
		// Timing
		clickHoldDuration: 400, // ms
		transitionDuration: 300, // ms
		animationDelay: 100, // ms
		autoActionDelay: 500, // ms
		// Other
		disableShortcuts: false,
		autoHide: true,
	};
}

// Gets 'composite keys' which have the form 'key1' or 'key1.key2' (usable to specify properties of store objects)
function getCompositeKeys(state: StoreState){
	const compKeys = [];
	for (const key of Object.getOwnPropertyNames(state) as (keyof StoreState)[]){
		if (typeof state[key] != 'object'){
			compKeys.push(key);
		} else {
			for (const subkey of Object.getOwnPropertyNames(state[key])){
				compKeys.push(`${key}.${subkey}`);
			}
		}
	}
	return compKeys;
}

const STORE_COMP_KEYS = getCompositeKeys(getDefaultState());

// ========== For getting/setting/loading store state ==========

function getStoreVal(state: StoreState, compKey: string): any {
	if (compKey in state){
		return state[compKey as keyof StoreState];
	}
	const [s1, s2] = compKey.split('.', 2);
	if (s1 in state){
		const key1 = s1 as keyof StoreState;
		if (typeof state[key1] == 'object' && s2 in (state[key1] as any)){
			return (state[key1] as any)[s2];
		}
	}
	return null;
}

function setStoreVal(state: StoreState, compKey: string, val: any): void {
	if (compKey in state){
		(state[compKey as keyof StoreState] as any) = val;
		return;
	}
	const [s1, s2] = compKey.split('.', 2);
	if (s1 in state){
		const key1 = s1 as keyof StoreState;
		if (typeof state[key1] == 'object' && s2 in (state[key1] as any)){
			(state[key1] as any)[s2] = val;
			return;
		}
	}
}

function loadFromLocalStorage(state: StoreState){
	for (const key of STORE_COMP_KEYS){
		const item = localStorage.getItem(key)
		if (item != null){
			setStoreVal(state, key, JSON.parse(item));
		}
	}
}

// ========== Main export ==========

export const useStore = defineStore('store', {
	state: () => {
		const state = getDefaultState();
		loadFromLocalStorage(state);
		return state;
	},

	actions: {
		reset(): void {
			Object.assign(this, getDefaultState());
		},

		resetOne(key: string){
			const val = getStoreVal(this, key);
			if (val != null){
				const val2 = getStoreVal(getDefaultState(), key);
				if (val != val2){
					setStoreVal(this, key, val2);
				}
			}
		},

		save(key: string){
			if (STORE_COMP_KEYS.includes(key)){
				localStorage.setItem(key, JSON.stringify(getStoreVal(this, key)));
			}
		},

		load(): void {
			loadFromLocalStorage(this);
		},

		clear(): void {
			for (const key of STORE_COMP_KEYS){
				localStorage.removeItem(key);
			}
		},

		softReset(): void { // Like reset(), but keeps saved values
			const defaultState = getDefaultState();
			for (const key of STORE_COMP_KEYS){
				const defaultVal = getStoreVal(defaultState, key);
				if (getStoreVal(this, key) != defaultVal && localStorage.getItem(key) == null){
					setStoreVal(this, key, defaultVal)
				}
			}
		},
	},
});
