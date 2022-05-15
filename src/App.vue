<script lang="ts">
import {defineComponent, PropType} from 'vue';
// Components
import Tile from './components/Tile.vue';
import AncestryBar from './components/AncestryBar.vue';
import TileInfoModal from './components/TileInfoModal.vue';
import HelpModal from './components/HelpModal.vue';
import SearchModal from './components/SearchModal.vue';
import SettingsPane from './components/SettingsPane.vue';
// Icons
import HelpIcon from './components/icon/HelpIcon.vue';
import SearchIcon from './components/icon/SearchIcon.vue';
import PlayIcon from './components/icon/PlayIcon.vue';
import SettingsIcon from './components/icon/SettingsIcon.vue';
// Other
import type {TolMap} from './tol';
import {TolNode} from './tol';
import {LayoutNode, initLayoutTree, initLayoutMap, tryLayout} from './layout';
import type {LayoutOptions, LayoutTreeChg} from './layout';
import {arraySum, randWeightedChoice, getScrollBarWidth} from './util';
// Note: Import paths lack a .ts or .js extension because .ts makes vue-tsc complain, and .js makes vite complain

// Type representing auto-mode actions
type Action = 'move across' | 'move down' | 'move up' |
	'expand' | 'collapse' | 'expand to view' | 'expand ancestry bar';
// Used in auto-mode to help avoid action cycles
function getReverseAction(action: Action): Action | null {
	let reversePairs: Action[][] = [
		['move down', 'move up'],
		['expand', 'collapse'],
		['expand to view', 'expand ancestry bar'],
	];
	let pair = reversePairs.find(pair => pair.includes(action));
	if (pair != null){
		return pair[0] == action ? pair[1] : pair[0];
	} else {
		return null;
	}
}

// Initialise tree-of-life data
const ROOT_NAME = "cellular organisms";
const initialTolMap: TolMap = new Map();
initialTolMap.set(ROOT_NAME, new TolNode());

// Configurable options
const defaultLytOpts: LayoutOptions = {
	tileSpacing: 8, //px
	headerSz: 22, //px
	minTileSz: 50, //px
	maxTileSz: 200, //px
	// Layout-algorithm related
	layoutType: 'sweep', //'sqr' | 'rect' | 'sweep'
	rectMode: 'auto first-row', //'horz' | 'vert' | 'linear' | 'auto' | 'auto first-row'
	sweepMode: 'left', //'left' | 'top' | 'shorter' | 'auto'
	sweptNodesPrio: 'pow-2/3', //'linear' | 'sqrt' | 'pow-2/3'
	sweepToParent: true,
};
const defaultUiOpts = {
	// For tiles
	borderRadius: 5, //px
	shadowNormal: '0 0 2px black',
	shadowHighlight: '0 0 1px 2px greenyellow',
	shadowFocused: '0 0 1px 2px orange',
	infoIconSz: 18, //px
	infoIconMargin: 2, //px
	tipThresholds: [[1, 'greenyellow'], [100, 'orange'], [1000, 'red']],
	headerColor: '#fafaf9',
	// For leaf tiles
	leafTilePadding: 4, //px
	leafHeaderFontSz: 15, //px
	// For non-leaf tiles
	nonleafBgColors: ['#44403c', '#57534e'], //tiles at depth N use the Nth color, repeating from the start as needed
	nonleafHeaderFontSz: 15, //px
	nonleafHeaderColor: '#fafaf9',
	nonleafHeaderBgColor: '#1c1917',
	// For other components
	appBgColor: '#292524',
	tileAreaOffset: 5, //px (space between root tile and display boundary)
	scrollGap: getScrollBarWidth(), //px (gap for overflown-root and ancestry-bar scrollbars, used to prevent overlap)
	ancestryBarSz: defaultLytOpts.minTileSz * 2, //px (breadth of ancestry-bar area)
	ancestryBarBgColor: '#44403c',
	ancestryTileMargin: 5, //px (gap between detached-ancestor tiles)
	infoModalImgSz: 200,
	autoWaitTime: 500, //ms (time to wait between actions (with their transitions))
	// Timing related
	tileChgDuration: 300, //ms (for tile move/expand/collapse)
	clickHoldDuration: 400, //ms (duration after mousedown when a click-and-hold is recognised)
	// Other
	useReducedTree: false,
};

export default defineComponent({
	data(){
		let layoutTree = initLayoutTree(initialTolMap, ROOT_NAME, 0);
		return {
			tolMap: initialTolMap,
			layoutTree: layoutTree,
			activeRoot: layoutTree, // Differs from layoutTree root when expand-to-view is used
			layoutMap: initLayoutMap(layoutTree), // Maps names to LayoutNode objects
			overflownRoot: false, // Set when displaying a root tile with many children, with overflow
			// Modals and settings related
			infoModalNodeName: null as string | null, // Name of node to display info for, or null
			helpOpen: false,
			searchOpen: false,
			settingsOpen: false,
			// For search and auto-mode
			modeRunning: false,
			lastFocused: null as LayoutNode | null,
			// For auto-mode
			autoPrevAction: null as Action | null, // Used to help prevent action cycles
			autoPrevActionFail: false, // Used to avoid re-trying a failed expand/collapse
			// Options
			lytOpts: {...defaultLytOpts},
			uiOpts: {...defaultUiOpts},
			// For window-resize handling
			width: document.documentElement.clientWidth,
			height: document.documentElement.clientHeight,
			pendingResizeHdlr: 0, // Set to a setTimeout() value
			// Other
			excessTolNodeThreshold: 1000, // Threshold where excess tolMap entries are removed (done on tile collapse)
		};
	},
	computed: {
		wideArea(): boolean {
			return this.width >= this.height;
		},
		// Nodes to show in ancestry-bar, with tol root first
		detachedAncestors(): LayoutNode[] | null {
			if (this.activeRoot == this.layoutTree){
				return null;
			}
			let ancestors = [];
			let node = this.activeRoot.parent;
			while (node != null){
				ancestors.push(node);
				node = node.parent;
			}
			return ancestors.reverse();
		},
		// Placement info for Tile and AncestryBar
		tileAreaPos(){
			let pos = [this.uiOpts.tileAreaOffset, this.uiOpts.tileAreaOffset] as [number, number];
			if (this.detachedAncestors != null){
				if (this.wideArea){
					pos[0] += this.uiOpts.ancestryBarSz;
				} else {
					pos[1] += this.uiOpts.ancestryBarSz;
				}
			}
			return pos;
		},
		tileAreaDims(){
			let dims = [
				this.width - this.uiOpts.tileAreaOffset*2,
				this.height - this.uiOpts.tileAreaOffset*2
			] as [number, number];
			if (this.detachedAncestors != null){
				if (this.wideArea){
					dims[0] -= this.uiOpts.ancestryBarSz;
				} else {
					dims[1] -= this.uiOpts.ancestryBarSz;
				}
			}
			return dims;
		},
		ancestryBarDims(): [number, number] {
			if (this.wideArea){
				return [this.uiOpts.ancestryBarSz, this.height];
			} else {
				return [this.width, this.uiOpts.ancestryBarSz];
			}
		},
	},
	methods: {
		// For tile expand/collapse events
		onLeafClick(layoutNode: LayoutNode){
			this.setLastFocused(null);
			// If clicking child of overflowing active-root
			if (this.overflownRoot){
				layoutNode.failFlag = !layoutNode.failFlag; // Triggers failure animation
				return Promise.resolve(false);
			}
			// Function for expanding tile
			let doExpansion = () => {
				let lytFnOpts = {
					allowCollapse: false,
					chg: {type: 'expand', node: layoutNode, tolMap: this.tolMap} as LayoutTreeChg,
					layoutMap: this.layoutMap
				};
				let success = tryLayout(
					this.activeRoot, this.tileAreaPos, this.tileAreaDims, this.lytOpts, lytFnOpts);
				// If expanding active-root with too many children to fit, allow overflow
				if (!success && layoutNode == this.activeRoot){
					success = tryLayout(this.activeRoot, this.tileAreaPos,
						[this.tileAreaDims[0] - this.uiOpts.scrollGap, this.tileAreaDims[1]],
						{...this.lytOpts, layoutType: 'flex-sqr'}, lytFnOpts);
					if (success){
						this.overflownRoot = true;
					}
				}
				// Check for failure
				if (!success){
					layoutNode.failFlag = !layoutNode.failFlag; // Triggers failure animation
				}
				return success;
			};
			// Check if data for node-to-expand exists, getting from server if needed
			let tolNode = this.tolMap.get(layoutNode.name)!;
			if (!this.tolMap.has(tolNode.children[0])){
				let urlPath = '/data/node?name=' + encodeURIComponent(layoutNode.name)
				urlPath += this.uiOpts.useReducedTree ? '&tree=reduced' : '';
				return fetch(urlPath)
					.then(response => response.json())
					.then(obj => {
						Object.getOwnPropertyNames(obj).forEach(key => {this.tolMap.set(key, obj[key])});
						doExpansion();
					})
					.catch(error => {
						console.log('ERROR loading tolnode data', error);
					});
			} else {
				return new Promise((resolve, reject) => resolve(doExpansion()));
			}
		},
		onNonleafClick(layoutNode: LayoutNode){
			this.setLastFocused(null);
			let success = tryLayout(this.activeRoot, this.tileAreaPos, this.tileAreaDims, this.lytOpts, {
				allowCollapse: false,
				chg: {type: 'collapse', node: layoutNode, tolMap: this.tolMap},
				layoutMap: this.layoutMap
			});
			if (!success){
				layoutNode.failFlag = !layoutNode.failFlag; // Triggers failure animation
			} else {
				// Update overflownRoot if root was collapsed
				if (this.overflownRoot){
					this.overflownRoot = false;
				}
				// Clear out excess nodes when a threshold is reached
				let numNodes = this.tolMap.size;
				let extraNodes = numNodes - this.layoutMap.size;
				if (extraNodes > this.excessTolNodeThreshold){
					for (let n of this.tolMap.keys()){
						if (!this.layoutMap.has(n)){
							this.tolMap.delete(n)
						}
					}
					console.log(`Cleaned up tolMap (removed ${numNodes - this.tolMap.size} out of ${numNodes})`);
				}
			}
			return success;
		},
		// For expand-to-view and ancestry-bar events
		onLeafClickHeld(layoutNode: LayoutNode){
			this.setLastFocused(null);
			if (layoutNode == this.activeRoot){
				this.onLeafClick(layoutNode);
				return;
			}
			// Function for expanding tile
			let doExpansion = () => {
				LayoutNode.hideUpward(layoutNode);
				this.activeRoot = layoutNode;
				this.overflownRoot = false;
				let lytFnOpts = {
					allowCollapse: false,
					chg: {type: 'expand', node: layoutNode, tolMap: this.tolMap} as LayoutTreeChg,
					layoutMap: this.layoutMap
				};
				let success = tryLayout(
					this.activeRoot, this.tileAreaPos, this.tileAreaDims, this.lytOpts, lytFnOpts);
				if (!success){
					success = tryLayout(this.activeRoot, this.tileAreaPos,
						[this.tileAreaDims[0] - this.uiOpts.scrollGap, this.tileAreaDims[1]],
						{...this.lytOpts, layoutType: 'flex-sqr'}, lytFnOpts);
					if (success){
						this.overflownRoot = true;
					}
				}
				// Check for failure
				if (!success){
					layoutNode.failFlag = !layoutNode.failFlag; // Triggers failure animation
				}
				return success;
			};
			// Check if data for node-to-expand exists, getting from server if needed
			let tolNode = this.tolMap.get(layoutNode.name)!;
			if (!this.tolMap.has(tolNode.children[0])){
				let urlPath = '/data/node?name=' + encodeURIComponent(layoutNode.name)
				urlPath += this.uiOpts.useReducedTree ? '&tree=reduced' : '';
				return fetch(urlPath)
					.then(response => response.json())
					.then(obj => {
						Object.getOwnPropertyNames(obj).forEach(key => {this.tolMap.set(key, obj[key])});
						doExpansion();
					})
					.catch(error => {
						console.log('ERROR loading tolnode data', error);
					});
			} else {
				return new Promise((resolve, reject) => resolve(doExpansion()));
			}
		},
		onNonleafClickHeld(layoutNode: LayoutNode){
			this.setLastFocused(null);
			if (layoutNode == this.activeRoot){
				console.log('Ignored expand-to-view on active-root node');
				return;
			}
			LayoutNode.hideUpward(layoutNode);
			this.activeRoot = layoutNode;
			tryLayout(this.activeRoot, this.tileAreaPos, this.tileAreaDims, this.lytOpts,
				{allowCollapse: true, layoutMap: this.layoutMap});
		},
		onDetachedAncestorClick(layoutNode: LayoutNode){
			this.setLastFocused(null);
			LayoutNode.showDownward(layoutNode);
			this.activeRoot = layoutNode;
			tryLayout(this.activeRoot, this.tileAreaPos, this.tileAreaDims, this.lytOpts,
				{allowCollapse: true, layoutMap: this.layoutMap});
			this.overflownRoot = false;
		},
		// For tile-info events
		onInfoIconClick(nodeName: string){
			if (!this.searchOpen){
				this.resetMode();
			}
			this.infoModalNodeName = nodeName;
		},
		// For help events
		onHelpIconClick(){
			this.resetMode();
			this.helpOpen = true;
		},
		// For search events
		onSearchIconClick(){
			this.resetMode();
			this.searchOpen = true;
		},
		onSearchNode(name: string){
			if (this.modeRunning){
				console.log("WARNING: Unexpected search event while search/auto mode is running")
				return;
			}
			this.searchOpen = false;
			this.modeRunning = true;
			this.expandToNode(name);
		},
		expandToNode(name: string){
			if (!this.modeRunning){
				return;
			}
			// Check if searched node is displayed
			let layoutNodeVal = this.layoutMap.get(name);
			if (layoutNodeVal != null && !layoutNodeVal.hidden){
				this.setLastFocused(layoutNodeVal);
				this.modeRunning = false;
				return;
			}
			// Get nearest in-layout-tree ancestor
			let ancestorName = name;
			while (this.layoutMap.get(ancestorName) == null){
				ancestorName = this.tolMap.get(ancestorName)!.parent!;
			}
			let layoutNode = this.layoutMap.get(ancestorName)!;
			// If hidden, expand self/ancestor in ancestry-bar
			if (layoutNode.hidden){
				while (!this.detachedAncestors!.includes(layoutNode)){
					layoutNode = layoutNode.parent!;
				}
				this.onDetachedAncestorClick(layoutNode!);
				setTimeout(() => this.expandToNode(name), this.uiOpts.tileChgDuration);
				return;
			}
			// Attempt tile-expand
			if (this.overflownRoot){
				this.onLeafClickHeld(layoutNode);
				setTimeout(() => this.expandToNode(name), this.uiOpts.tileChgDuration);
				return;
			}
			this.onLeafClick(layoutNode).then(success => {
				if (success){
					setTimeout(() => this.expandToNode(name), this.uiOpts.tileChgDuration);
					return;
				}
				// Attempt expand-to-view on ancestor just below activeRoot
				if (layoutNode == this.activeRoot){
					console.log('Screen too small to expand active root');
					this.modeRunning = false;
					return;
				}
				while (true){
					if (layoutNode.parent! == this.activeRoot){
						break;
					}
					layoutNode = layoutNode.parent!;
				}
				this.onNonleafClickHeld(layoutNode);
				setTimeout(() => this.expandToNode(name), this.uiOpts.tileChgDuration);
			});
		},
		// For auto-mode events
		onPlayIconClick(){
			this.resetMode();
			this.modeRunning = true;
			this.autoAction();
		},
		autoAction(){
			if (!this.modeRunning){
				this.setLastFocused(null);
				return;
			}
			if (this.lastFocused == null){
				// Pick random leaf LayoutNode
				let layoutNode = this.activeRoot;
				while (layoutNode.children.length > 0){
					let childWeights = layoutNode.children.map(n => n.dCount);
					let idx = randWeightedChoice(childWeights);
					layoutNode = layoutNode.children[idx!];
				}
				this.setLastFocused(layoutNode);
				setTimeout(this.autoAction, this.uiOpts.autoWaitTime);
			} else {
				// Determine available actions
				let action: Action | null;
				let actionWeights: {[key: string]: number}; // Maps actions to choice weights
				let node: LayoutNode = this.lastFocused;
				if (node.children.length == 0){
					actionWeights = {'move across': 1, 'move up': 2, 'expand': 3};
					// Zero weights for disallowed actions
					if (node == this.activeRoot || node.parent!.children.length == 1){
						actionWeights['move across'] = 0;
					}
					if (node == this.activeRoot){
						actionWeights['move up'] = 0;
					}
					if (this.tolMap.get(node.name)!.children.length == 0 || this.overflownRoot){
						actionWeights['expand'] = 0;
					}
				} else {
					actionWeights = {
						'move across': 1, 'move down': 2, 'move up': 1,
						'collapse': 1, 'expand to view': 1, 'expand ancestry bar': 1
					};
					// Zero weights for disallowed actions
					if (node == this.activeRoot || node.parent!.children.length == 1){
						actionWeights['move across'] = 0;
					}
					if (node == this.activeRoot){
						actionWeights['move up'] = 0;
					}
					if (!node.children.every(n => n.children.length == 0)){
						actionWeights['collapse'] = 0; // Only collapse if all children are leaves
					}
					if (node.parent != this.activeRoot){
						actionWeights['expand to view'] = 0; // Only expand-to-view if direct child of activeRoot
					}
					if (this.activeRoot.parent == null || node != this.activeRoot){
						actionWeights['expand ancestry bar'] = 0; // Only expand ancestry-bar if able and activeRoot
					}
				}
				if (this.autoPrevAction != null){ // Avoid undoing previous action
					let revAction = getReverseAction(this.autoPrevAction);
					if (revAction != null && revAction in actionWeights){
						actionWeights[revAction as keyof typeof actionWeights] = 0;
					}
					if (this.autoPrevActionFail){
						actionWeights[this.autoPrevAction as keyof typeof actionWeights] = 0;
					}
				}
				// Choose action
				let actionList = Object.getOwnPropertyNames(actionWeights);
				let weightList = actionList.map(action => actionWeights[action]);
				if (arraySum(weightList) == 0){
					action = null;
				} else {
					action = actionList[randWeightedChoice(weightList)!] as Action;
				}
				// Perform action
				this.autoPrevActionFail = false;
				switch (action){
					case 'move across': // Bias towards siblings with higher dCount
						let siblings = node.parent!.children.filter(n => n != node);
						let siblingWeights = siblings.map(n => n.dCount + 1);
						this.setLastFocused(siblings[randWeightedChoice(siblingWeights)!]);
						break;
					case 'move down': // Bias towards children with higher dCount
						let childWeights = node.children.map(n => n.dCount + 1);
						this.setLastFocused(node.children[randWeightedChoice(childWeights)!]);
						break;
					case 'move up':
						this.setLastFocused(node.parent!);
						break;
					case 'expand':
						this.onLeafClick(node)
							.then(success => this.autoPrevActionFail = !success)
							.catch(error => this.autoPrevActionFail = true);
						break;
					case 'collapse':
						this.autoPrevActionFail = !this.onNonleafClick(node);
						break;
					case 'expand to view':
						this.onNonleafClickHeld(node);
						break;
					case 'expand ancestry bar':
						this.onDetachedAncestorClick(node.parent!);
						break;
				}
				setTimeout(this.autoAction, this.uiOpts.tileChgDuration + this.uiOpts.autoWaitTime);
				this.autoPrevAction = action;
			}
		},
		// For settings events
		onSettingsIconClick(){
			this.resetMode();
			this.settingsOpen = true;
		},
		onLayoutOptionChange(){
			tryLayout(this.activeRoot, this.tileAreaPos, this.tileAreaDims, this.lytOpts,
				{allowCollapse: true, layoutMap: this.layoutMap});
		},
		onTreeChange(){
			// Collapse tree to root
			if (this.activeRoot != this.layoutTree){
				this.onDetachedAncestorClick(this.layoutTree);
			}
			this.onNonleafClick(this.layoutTree);
			// Re-initialise tree
			this.initTreeFromServer();
		},
		// For other events
		onResize(){
			if (this.pendingResizeHdlr == 0){
				this.pendingResizeHdlr = setTimeout(() => {
					this.width = document.documentElement.clientWidth;
					this.height = document.documentElement.clientHeight;
					this.uiOpts.scrollGap = getScrollBarWidth();
					tryLayout(this.activeRoot, this.tileAreaPos, this.tileAreaDims, this.lytOpts,
						{allowCollapse: true, layoutMap: this.layoutMap});
					this.overflownRoot = false;
					this.pendingResizeHdlr = 0;
				}, 100);
			}
		},
		onKeyUp(evt: KeyboardEvent){
			if (evt.key == 'Escape'){
				this.resetMode();
			} else if (evt.key == 'F' && evt.ctrlKey){ // On ctrl-shift-f
				if (!this.searchOpen){
					this.onSearchIconClick();
				} else {
					(this.$refs.searchModal as InstanceType<typeof SearchModal>).focusInput();
				}
			}
		},
		// Helper methods
		initTreeFromServer(){
			let urlPath = '/data/node?name=' + encodeURIComponent(ROOT_NAME);
			urlPath += this.uiOpts.useReducedTree ? '&tree=reduced' : '';
			fetch(urlPath)
				.then(response => response.json())
				.then(obj => {
					this.tolMap.clear();
					Object.getOwnPropertyNames(obj).forEach(key => {this.tolMap.set(key, obj[key])});
					this.layoutTree = initLayoutTree(this.tolMap, this.layoutTree.name, 0);
					this.activeRoot = this.layoutTree;
					this.layoutMap = initLayoutMap(this.layoutTree);
					tryLayout(this.activeRoot, this.tileAreaPos, this.tileAreaDims, this.lytOpts,
						{allowCollapse: true, layoutMap: this.layoutMap});
				})
				.catch(error => {
					console.log('ERROR loading initial tolnode data', error);
				});
		},
		resetMode(){
			this.infoModalNodeName = null;
			this.searchOpen = false;
			this.helpOpen = false;
			this.settingsOpen = false;
			this.modeRunning = false;
			this.setLastFocused(null);
		},
		setLastFocused(node: LayoutNode | null){
			if (this.lastFocused != null){
				this.lastFocused.hasFocus = false;
			}
			this.lastFocused = node;
			if (node != null){
				node.hasFocus = true;
			}
		},
	},
	created(){
		window.addEventListener('resize', this.onResize);
		window.addEventListener('keyup', this.onKeyUp);
		tryLayout(this.activeRoot, this.tileAreaPos, this.tileAreaDims, this.lytOpts,
			{allowCollapse: true, layoutMap: this.layoutMap});
		this.initTreeFromServer();
	},
	unmounted(){
		window.removeEventListener('resize', this.onResize);
		window.removeEventListener('keyup', this.onKeyUp);
	},
	components: {
		Tile, AncestryBar,
		HelpIcon, SearchIcon, PlayIcon, SettingsIcon,
		TileInfoModal, HelpModal, SearchModal, SettingsPane,
	},
});
</script>

<template>
<div class="absolute left-0 top-0 w-screen h-screen overflow-hidden" :style="{backgroundColor: uiOpts.appBgColor}">
	<!-- Note: Making the above enclosing div's width/height dynamic seems to cause white flashes when resizing -->
	<tile :layoutNode="layoutTree" :tolMap="tolMap" :lytOpts="lytOpts" :uiOpts="uiOpts"
		:overflownDim="overflownRoot ? tileAreaDims[1] : 0"
		@leaf-click="onLeafClick" @nonleaf-click="onNonleafClick"
		@leaf-click-held="onLeafClickHeld" @nonleaf-click-held="onNonleafClickHeld"
		@info-icon-click="onInfoIconClick"/>
	<ancestry-bar v-if="detachedAncestors != null"
		:pos="[0,0]" :dims="ancestryBarDims" :nodes="detachedAncestors"
		:tolMap="tolMap" :lytOpts="lytOpts" :uiOpts="uiOpts"
		@detached-ancestor-click="onDetachedAncestorClick" @info-icon-click="onInfoIconClick"/>
	<!-- Icons -->
	<help-icon @click="onHelpIconClick"
		class="absolute bottom-[6px] left-[6px] w-[18px] h-[18px]
			text-white/40 hover:text-white hover:cursor-pointer"/>
	<search-icon @click="onSearchIconClick"
		class="absolute bottom-[6px] left-[30px] w-[18px] h-[18px]
			text-white/40 hover:text-white hover:cursor-pointer"/>
	<play-icon @click="onPlayIconClick"
		class="absolute bottom-[6px] left-[54px] w-[18px] h-[18px]
			text-white/40 hover:text-white hover:cursor-pointer"/>
	<!-- Modals -->
	<transition name="fade">
		<search-modal v-if="searchOpen" :tolMap="tolMap" :uiOpts="uiOpts" ref="searchModal"
			@search-close="searchOpen = false" @search-node="onSearchNode" @info-icon-click="onInfoIconClick"/>
	</transition>
	<transition name="fade">
		<tile-info-modal v-if="infoModalNodeName != null" :nodeName="infoModalNodeName" :tolMap="tolMap" :uiOpts="uiOpts"
			@info-modal-close="infoModalNodeName = null"/>
	</transition>
	<transition name="fade">
		<help-modal v-if="helpOpen" :uiOpts="uiOpts" @help-modal-close="helpOpen = false"/>
	</transition>
	<!-- Settings -->
	<transition name="slide-bottom-right">
		<settings-pane v-if="settingsOpen" :lytOpts="lytOpts" :uiOpts="uiOpts"
			@settings-close="settingsOpen = false"
			@layout-option-change="onLayoutOptionChange" @tree-change="onTreeChange"/>
		<div v-else class="absolute bottom-0 right-0 w-[100px] h-[100px] invisible">
			<!-- Note: Above enclosing div prevents transition interference with inner rotate -->
			<div class="absolute bottom-[-50px] right-[-50px] w-[100px] h-[100px] visible -rotate-45
				bg-black text-white hover:cursor-pointer" @click="onSettingsIconClick">
				<settings-icon class="w-6 h-6 mx-auto mt-2"/>
			</div>
		</div>
	</transition>
	<!-- Overlay used to prevent interaction and capture clicks -->
	<div :style="{visibility: modeRunning ? 'visible' : 'hidden'}"
		class="absolute left-0 top-0 w-full h-full" @click="modeRunning = false"></div>
</div>
</template>

<style>
.fade-enter-from, .fade-leave-to {
	opacity: 0;
}
.fade-enter-active, .fade-leave-active {
	transition-property: opacity;
	transition-duration: 300ms;
	transition-timing-function: ease-out;
}
.slide-bottom-right-enter-from, .slide-bottom-right-leave-to {
	transform: translate(100%, 100%);
	opacity: 0;
}
.slide-bottom-right-enter-active, .slide-bottom-right-leave-active {
	transition-property: transform, opacity;
	transition-duration: 300ms;
	transition-timing-function: ease-in-out;
}
</style>
