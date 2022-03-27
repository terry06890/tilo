<script lang="ts">
import {defineComponent, PropType} from 'vue';
import Tile from './components/Tile.vue';
import ParentBar from './components/ParentBar.vue';
import TileInfoModal from './components/TileInfoModal.vue';
import SearchModal from './components/SearchModal.vue';
import HelpModal from './components/HelpModal.vue';
import Settings from './components/Settings.vue';
import {TolNode, LayoutNode, initLayoutTree, initLayoutMap, tryLayout, randWeightedChoice} from './lib';
import type {LayoutOptions} from './lib';
// Import paths lack a .ts or .js extension because .ts makes vue-tsc complain, and .js makes vite complain

// Obtain tree-of-life data
import tolRaw from './tol.json';
function preprocessTol(node: any): any {
	function helper(node: any, parent: any){
		//Add 'children' field if missing
		if (node.children == null){
			node.children = [];
		}
		//Add 'parent' field
		node.parent = parent;
		node.children.forEach((child: any) => helper(child, node));
	}
	helper(node, null);
	return node;
}
const tol: TolNode = preprocessTol(tolRaw);
function getTolMap(tol: TolNode): Map<string,TolNode> {
	function helper(node: TolNode, map: Map<string,TolNode>){
		map.set(node.name, node);
		node.children.forEach(child => helper(child, map));
	}
	let map = new Map();
	helper(tol, map);
	return map;
}
const tolMap = getTolMap(tol);

// Configurable settings
const defaultLayoutOptions: LayoutOptions = {
	tileSpacing: 8, //px
	headerSz: 20, //px
	minTileSz: 50, //px
	maxTileSz: 200, //px
	layoutType: 'sweep', //'sqr' | 'rect' | 'sweep'
	rectMode: 'auto first-row', //'horz' | 'vert' | 'linear' | 'auto' | 'auto first-row'
	sweepMode: 'left', //'left' | 'top' | 'shorter' | 'auto'
	sweptNodesPrio: 'pow-2/3', //'linear' | 'sqrt' | 'pow-2/3'
	sweepingToParent: true,
};
const defaultComponentOptions = {
	// For leaf/non_leaf tile and separated-parent components
	borderRadius: 5, //px
	shadowNormal: '0 0 2px black',
	shadowHighlight: '0 0 1px 2px greenyellow',
	shadowFocused: '0 0 1px 2px orange',
	// For leaf and separated-parent components
	imgTilePadding: 4, //px
	imgTileFontSz: 15, //px
	imgTileColor: '#fafaf9',
	expandableImgTileColor: 'greenyellow', //yellow, greenyellow, turquoise,
	infoIconSz: 18, //px
	infoIconPadding: 2, //px
	infoIconColor: 'rgba(250,250,250,0.3)',
	infoIconHoverColor: 'white',
	// For non-leaf tile-group components
	nonLeafBgColors: ['#44403c', '#57534e'], //tiles at depth N use the Nth color, repeating from the start as needed
	nonLeafHeaderFontSz: 15, //px
	nonLeafHeaderColor: '#fafaf9',
	nonLeafHeaderBgColor: '#1c1917',
	// For tile-info modal
	infoModalImgSz: 200,
	// Timing related
	transitionDuration: 300, //ms
	clickHoldDuration: 400, //ms (duration after mousedown when a click-and-hold is recognised)
};
const defaultOwnOptions = {
	tileAreaOffset: 5, //px (space between root tile and display boundary)
	parentBarSz: defaultLayoutOptions.minTileSz * 2, //px (breadth of separated-parents area)
};

// Holds a tree structure representing a subtree of 'tol' to be rendered
// Collects events about tile expansion/collapse and window-resize, and initiates relayout of tiles
export default defineComponent({
	data(){
		let layoutTree = initLayoutTree(tol, 0);
		return {
			layoutTree: layoutTree,
			activeRoot: layoutTree,
			layoutMap: initLayoutMap(layoutTree), // Maps names to LayoutNode objects
			tolMap: tolMap, // Maps names to TolNode objects
			//
			infoModalNode: null as TolNode | null, // Hides/unhides info modal, and provides the node to display
			searchOpen: false,
			settingsOpen: false,
			lastFocused: null as LayoutNode | null,
			animationActive: false,
			autoWaitTime: 500, //ms (in auto mode, time to wait after an action ends)
			helpOpen: false,
			// Options
			layoutOptions: {...defaultLayoutOptions},
			componentOptions: {...defaultComponentOptions},
			...defaultOwnOptions,
			// For window-resize handling
			width: document.documentElement.clientWidth,
			height: document.documentElement.clientHeight,
			resizeThrottled: false,
			resizeDelay: 50, //ms (increasing to 100 seems to cause resize-skipping when opening browser mobile-view)
		};
	},
	computed: {
		wideArea(): boolean{
			return this.width >= this.height;
		},
		sepdParents(): LayoutNode[] | null {
			if (this.activeRoot == this.layoutTree){
				return null;
			}
			let parents = [];
			let node = this.activeRoot.parent;
			while (node != null){
				parents.push(node);
				node = node.parent;
			}
			return parents.reverse();
		},
		tileAreaPos(){
			let pos = [this.tileAreaOffset, this.tileAreaOffset] as [number, number];
			if (this.sepdParents != null){
				if (this.wideArea){
					pos[0] += this.parentBarSz;
				} else {
					pos[1] += this.parentBarSz;
				}
			}
			return pos;
		},
		tileAreaDims(){
			let dims = [
				this.width - this.tileAreaOffset*2,
				this.height - this.tileAreaOffset*2
			] as [number, number];
			if (this.sepdParents != null){
				if (this.wideArea){
					dims[0] -= this.parentBarSz;
				} else {
					dims[1] -= this.parentBarSz;
				}
			}
			return dims;
		},
		parentBarDims(): [number, number] {
			if (this.wideArea){
				return [this.parentBarSz, this.height];
			} else {
				return [this.width, this.parentBarSz];
			}
		},
		styles(): Record<string,string> {
			return {
				position: 'absolute',
				left: '0',
				top: '0',
				width: '100vw', // Making this dynamic causes white flashes when resizing
				height: '100vh',
				backgroundColor: '#292524',
				overflow: 'hidden',
			};
		},
	},
	methods: {
		onResize(){
			if (!this.resizeThrottled){
				this.width = document.documentElement.clientWidth;
				this.height = document.documentElement.clientHeight;
				tryLayout(this.activeRoot, this.layoutMap,
					this.tileAreaPos, this.tileAreaDims, this.layoutOptions, true);
				// Prevent re-triggering until after a delay
				this.resizeThrottled = true;
				setTimeout(() => {this.resizeThrottled = false;}, this.resizeDelay);
			}
		},
		// For tile expand/collapse events
		onInnerLeafClicked({layoutNode, failCallback}: {layoutNode: LayoutNode, failCallback?: () => void}){
			let success = tryLayout(this.activeRoot, this.layoutMap,
				this.tileAreaPos, this.tileAreaDims, this.layoutOptions, false, {type: 'expand', node: layoutNode});
			if (!success && failCallback != null){
				failCallback();
			}
			return success;
		},
		onInnerHeaderClicked({layoutNode, failCallback}: {layoutNode: LayoutNode, failCallback?: () => void}){
			let oldChildren = layoutNode.children;
			let success = tryLayout(this.activeRoot, this.layoutMap,
				this.tileAreaPos, this.tileAreaDims, this.layoutOptions, false, {type: 'collapse', node: layoutNode});
			if (!success && failCallback != null){
				failCallback();
			}
			return success;
		},
		// For expand-to-view events
		onInnerLeafClickHeld(layoutNode: LayoutNode){
			if (layoutNode == this.activeRoot){
				console.log('Ignored expand-to-view on root node');
				return;
			}
			LayoutNode.hideUpward(layoutNode);
			this.activeRoot = layoutNode;
			tryLayout(this.activeRoot, this.layoutMap,
				this.tileAreaPos, this.tileAreaDims, this.layoutOptions, true, {type: 'expand', node: layoutNode});
		},
		onInnerHeaderClickHeld(layoutNode: LayoutNode){
			if (layoutNode == this.activeRoot){
				console.log('Ignored expand-to-view on active-root node');
				return;
			}
			LayoutNode.hideUpward(layoutNode);
			this.activeRoot = layoutNode;
			tryLayout(this.activeRoot, this.layoutMap, this.tileAreaPos, this.tileAreaDims, this.layoutOptions, true);
		},
		onSepdParentClicked(layoutNode: LayoutNode){
			LayoutNode.showDownward(layoutNode);
			this.activeRoot = layoutNode;
			tryLayout(this.activeRoot, this.layoutMap, this.tileAreaPos, this.tileAreaDims, this.layoutOptions, true);
		},
		// For info modal events
		onInnerInfoIconClicked(node: LayoutNode){
			this.closeModesAndSettings();
			this.infoModalNode = node.tolNode;
		},
		onInfoModalClose(){
			this.infoModalNode = null;
		},
		//
		onSettingsIconClick(){
			this.closeModesAndSettings();
			this.settingsOpen = true;
		},
		onSettingsClose(){
			this.settingsOpen = false;
		},
		onLayoutOptionChange(){
			tryLayout(this.activeRoot, this.layoutMap, this.tileAreaPos, this.tileAreaDims, this.layoutOptions, true);
		},
		//
		onSearchIconClick(){
			this.closeModesAndSettings();
			this.searchOpen = true;
		},
		onSearchClose(){
			this.searchOpen = false;
		},
		onSearchNode(tolNode: TolNode){
			this.searchOpen = false;
			this.animationActive = true;
			this.expandToTolNode(tolNode);
		},
		//
		closeModesAndSettings(){
			this.infoModalNode = null;
			this.searchOpen = false;
			this.helpOpen = false;
			this.settingsOpen = false;
			this.animationActive = false;
			this.setLastFocused(null);
		},
		onKeyUp(evt: KeyboardEvent){
			if (evt.key == 'Escape'){
				this.closeModesAndSettings();
			} else if (evt.key == 'F' && evt.ctrlKey){
				if (!this.searchOpen){
					this.onSearchIconClick();
				} else {
					(this.$refs.searchModal as InstanceType<typeof SearchModal>).focusInput();
				}
			}
		},
		expandToTolNode(tolNode: TolNode){
			if (!this.animationActive){
				return;
			}
			// Check if searched node is shown
			let layoutNode = this.layoutMap.get(tolNode.name);
			if (layoutNode != null && !layoutNode.hidden){
				this.setLastFocused(layoutNode);
				this.animationActive = false;
				return;
			}
			// Get nearest in-layout-tree ancestor
			let ancestor = tolNode;
			while (this.layoutMap.get(ancestor.name) == null){
				ancestor = ancestor.parent!;
			}
			layoutNode = this.layoutMap.get(ancestor.name)!;
			// If hidden, expand ancestor in parent-bar
			if (layoutNode.hidden){
				// Get self/ancestor in parent-bar
				while (!this.sepdParents!.includes(layoutNode)){
					ancestor = ancestor.parent!;
					layoutNode = this.layoutMap.get(ancestor.name)!;
				}
				this.onSepdParentClicked(layoutNode!);
				setTimeout(() => this.expandToTolNode(tolNode), this.componentOptions.transitionDuration);
				return;
			}
			// Attempt tile-expand
			let success = this.onInnerLeafClicked({layoutNode});
			if (success){
				setTimeout(() => this.expandToTolNode(tolNode), this.componentOptions.transitionDuration);
				return;
			}
			// Attempt expand-to-view on ancestor just below activeRoot
			if (ancestor.name == this.activeRoot.tolNode.name){
				console.log('Unable to complete search (not enough room to expand active root)');
					// Happens if screen is very small or node has very many children
				this.animationActive = false;
				return;
			}
			while (true){
				if (ancestor.parent!.name == this.activeRoot.tolNode.name){
					break;
				}
				ancestor = ancestor.parent!;
			}
			layoutNode = this.layoutMap.get(ancestor.name)!;
			this.onInnerHeaderClickHeld(layoutNode);
			setTimeout(() => this.expandToTolNode(tolNode), this.componentOptions.transitionDuration);
		},
		onOverlayClick(){
			this.animationActive = false;
		},
		onPlayIconClick(){
			this.closeModesAndSettings();
			this.animationActive = true;
			this.autoAction();
		},
		autoAction(){
			if (!this.animationActive){
				this.setLastFocused(null);
				return;
			}
			if (this.lastFocused == null){
				// Get random leaf LayoutNode
				let layoutNode = this.activeRoot;
				while (layoutNode.children.length > 0){
					let idx = Math.floor(Math.random() * layoutNode.children.length);
					layoutNode = layoutNode.children[idx];
				}
				this.setLastFocused(layoutNode);
				setTimeout(this.autoAction, this.autoWaitTime);
			} else {
				// Perform action
				let node = this.lastFocused;
				if (node.children.length == 0){
					const Action = {MoveAcross:0, MoveUpward:1, Expand:2};
					let actionWeights = [1, 2, 4];
					// Zero weights for disallowed actions
					if (node == this.activeRoot || node.parent!.children.length == 1){
						actionWeights[Action.MoveAcross] = 0;
					}
					if (node == this.activeRoot){
						actionWeights[Action.MoveUpward] = 0;
					}
					if (node.tolNode.children.length == 0){
						actionWeights[Action.Expand] = 0;
					}
					let action = randWeightedChoice(actionWeights);
					switch (action){
						case Action.MoveAcross:
							let siblings = node.parent!.children.filter(n => n != node);
							this.setLastFocused(siblings[Math.floor(Math.random() * siblings.length)]);
							break;
						case Action.MoveUpward:
							this.setLastFocused(node.parent!);
							break;
						case Action.Expand:
							this.onInnerLeafClicked({layoutNode: node});
							break;
					}
				} else {
					const Action = {MoveAcross:0, MoveDown:1, MoveUp:2, Collapse:3, ExpandToView:4, ExpandParentBar:5};
					let actionWeights = [1, 2, 1, 1, 1, 1];
					// Zero weights for disallowed actions
					if (node == this.activeRoot || node.parent!.children.length == 1){
						actionWeights[Action.MoveAcross] = 0;
					}
					if (node == this.activeRoot){
						actionWeights[Action.MoveUp] = 0;
					}
					if (!node.children.every(n => n.children.length == 0)){
						actionWeights[Action.Collapse] = 0; // Only collapse if all children are leaves
					}
					if (node.parent != this.activeRoot){
						actionWeights[Action.ExpandToView] = 0; // Only expand-to-view if direct child of activeRoot
					}
					if (this.activeRoot.parent == null || node != this.activeRoot){
						actionWeights[Action.ExpandParentBar] = 0; // Only expand parent-bar if able and activeRoot
					}
					let action = randWeightedChoice(actionWeights);
					switch (action){
						case Action.MoveAcross:
							let siblings = node.parent!.children.filter(n => n != node);
							this.setLastFocused(siblings[Math.floor(Math.random() * siblings.length)]);
							break;
						case Action.MoveDown:
							let idx = Math.floor(Math.random() * node.children.length);
							this.setLastFocused(node.children[idx]);
							break;
						case Action.MoveUp:
							this.setLastFocused(node.parent!);
							break;
						case Action.Collapse:
							this.onInnerHeaderClicked({layoutNode: node});
							break;
						case Action.ExpandToView:
							this.onInnerHeaderClickHeld(node);
							break;
						case Action.ExpandParentBar:
							this.onSepdParentClicked(node.parent!);
							break;
					}
				}
				setTimeout(this.autoAction, this.componentOptions.transitionDuration + this.autoWaitTime);
			}
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
		onHelpIconClick(){
			this.closeModesAndSettings();
			this.helpOpen = true;
		},
		onHelpModalClose(){
			this.helpOpen = false;
		},
	},
	created(){
		window.addEventListener('resize', this.onResize);
		window.addEventListener('keyup', this.onKeyUp);
		tryLayout(this.activeRoot, this.layoutMap, this.tileAreaPos, this.tileAreaDims, this.layoutOptions, true);
	},
	unmounted(){
		window.removeEventListener('resize', this.onResize);
		window.removeEventListener('keyup', this.onKeyUp);
	},
	components: {Tile, ParentBar, TileInfoModal, Settings, SearchModal, HelpModal, },
});
</script>

<template>
<div :style="styles">
	<tile :layoutNode="layoutTree"
		:headerSz="layoutOptions.headerSz" :tileSpacing="layoutOptions.tileSpacing" :options="componentOptions"
		@leaf-clicked="onInnerLeafClicked" @header-clicked="onInnerHeaderClicked"
		@leaf-click-held="onInnerLeafClickHeld" @header-click-held="onInnerHeaderClickHeld"
		@info-icon-clicked="onInnerInfoIconClicked"/>
	<parent-bar v-if="sepdParents != null"
		:pos="[0,0]" :dims="parentBarDims" :nodes="sepdParents" :options="componentOptions"
		@sepd-parent-clicked="onSepdParentClicked" @info-icon-clicked="onInnerInfoIconClicked"/>
	<!-- Settings -->
	<transition name="slide-bottom-right">
		<settings v-if="settingsOpen" :layoutOptions="layoutOptions" :componentOptions="componentOptions"
			@settings-close="onSettingsClose" @layout-option-change="onLayoutOptionChange"/>
		<!-- outer div prevents transition interference with inner rotate -->
		<div v-else class="absolute bottom-0 right-0 w-[100px] h-[100px] invisible">
			<div class="absolute bottom-[-50px] right-[-50px] w-[100px] h-[100px] visible -rotate-45
				bg-black text-white hover:cursor-pointer" @click="onSettingsIconClick">
				<svg class="w-6 h-6 mx-auto mt-2"><use href="#svg-settings"/></svg>
			</div>
		</div>
	</transition>
	<!-- Icons -->
	<svg class="absolute top-[6px] right-[54px] w-[18px] h-[18px] text-white/40 hover:text-white hover:cursor-pointer"
		@click="onSearchIconClick">
		<use href="#svg-search"/>
	</svg>
	<svg class="absolute top-[6px] right-[30px] w-[18px] h-[18px] text-white/40 hover:text-white hover:cursor-pointer"
		@click="onPlayIconClick">
		<use href="#svg-play"/>
	</svg>
	<svg class="absolute top-[6px] right-[6px] w-[18px] h-[18px] text-white/40 hover:text-white hover:cursor-pointer"
		@click="onHelpIconClick">
		<use href="#svg-help"/>
	</svg>
	<!-- Modals -->
	<transition name="fade">
		<tile-info-modal v-if="infoModalNode != null" :tolNode="infoModalNode" :options="componentOptions"
			@info-modal-close="onInfoModalClose"/>
	</transition>
	<transition name="fade">
		<search-modal v-if="searchOpen" :layoutTree="layoutTree" :tolMap="tolMap" :options="componentOptions"
			@search-close="onSearchClose" @search-node="onSearchNode" ref="searchModal"/>
	</transition>
	<transition name="fade">
		<help-modal v-if="helpOpen" :options="componentOptions" @help-modal-close="onHelpModalClose"/>
	</transition>
	<!-- Overlay used to prevent interaction and capture clicks -->
	<div :style="{visibility: animationActive ? 'visible' : 'hidden'}"
		class="absolute left-0 top-0 w-full h-full" @click="onOverlayClick"></div>
	<!-- SVGs -->
	<svg style="display:none">
		<defs>
			<svg id="svg-info"
				xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
				stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
				<circle cx="12" cy="12" r="10"/>
				<line x1="12" y1="16" x2="12" y2="12"/>
				<line x1="12" y1="8" x2="12.01" y2="8"/>
			</svg>
			<svg id="svg-settings"
				xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
				stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
				<circle cx="12" cy="12" r="3"/>
				<path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0
					0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2
					2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0
					0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65
					1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1
					2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2
					0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65
					1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0
					1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0
					2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2
					2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
			</svg>
			<svg id="svg-search"
				xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
				stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
				<circle cx="11" cy="11" r="8"/>
				<line x1="21" y1="21" x2="16.65" y2="16.65"/>
			</svg>
			<svg id="svg-play"
				xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
				stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
				<circle cx="12" cy="12" r="10"/>
				<polygon points="10 8 16 12 10 16 10 8"/>
			</svg>
			<svg id="svg-help"
				xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
				stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
				<circle cx="12" cy="12" r="10"/>
				<path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
				<line x1="12" y1="17" x2="12.01" y2="17"/>
			</svg>
			<svg id="svg-close"
				xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
				stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
				<line x1="18" y1="6" x2="6" y2="18"/>
				<line x1="6" y1="6" x2="18" y2="18"/>
			</svg>
		</defs>
	</svg>
</div>
</template>

<style>
.animate-expand-shrink {
	animation-name: expand-shrink;
	animation-duration: 300ms;
	animation-iteration-count: 1;
	animation-timing-function: ease-in-out;
}
@keyframes expand-shrink {
	from {
		transform: scale(1, 1);
	}
	50% {
		transform: scale(1.1, 1.1);
	}
	to {
		transform: scale(1, 1);
	}
}
.animate-shrink-expand {
	animation-name: shrink-expand;
	animation-duration: 300ms;
	animation-iteration-count: 1;
	animation-timing-function: ease-in-out;
}
@keyframes shrink-expand {
	from {
		transform: translate3d(0,0,0) scale(1, 1);
	}
	50% {
		transform: translate3d(0,0,0) scale(0.9, 0.9);
	}
	to {
		transform: translate3d(0,0,0) scale(1, 1);
	}
}
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
