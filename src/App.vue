<script lang="ts">
import {defineComponent, PropType} from 'vue';
//
import Tile from './components/Tile.vue';
import AncestryBar from './components/AncestryBar.vue';
import TileInfoModal from './components/TileInfoModal.vue';
import SearchModal from './components/SearchModal.vue';
import HelpModal from './components/HelpModal.vue';
import SettingsPane from './components/SettingsPane.vue';
//
import SearchIcon from './components/icon/SearchIcon.vue';
import PlayIcon from './components/icon/PlayIcon.vue';
import HelpIcon from './components/icon/HelpIcon.vue';
import SettingsIcon from './components/icon/SettingsIcon.vue';
//
import {TolNode, TolNodeRaw, tolFromRaw, getTolMap} from './tol';
import {LayoutNode, initLayoutTree, initLayoutMap, tryLayout} from './layout';
import type {LayoutOptions} from './layout';
import {arraySum, randWeightedChoice} from './util';
// Import paths lack a .ts or .js extension because .ts makes vue-tsc complain, and .js makes vite complain

// Obtain tree-of-life data
import tolRaw from './tolData.json';
const tol: TolNode = tolFromRaw(tolRaw);
const tolMap = getTolMap(tol);

// Configurable settings
const defaultLytOpts: LayoutOptions = {
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
const defaultUiOpts = {
	// For leaf/non_leaf tile and detached-ancestor components
	borderRadius: 5, //px
	shadowNormal: '0 0 2px black',
	shadowHighlight: '0 0 1px 2px greenyellow',
	shadowFocused: '0 0 1px 2px orange',
	// For leaf and detached-ancestor components
	imgTilePadding: 4, //px
	imgTileFontSz: 15, //px
	imgTileColor: '#fafaf9',
	expandableImgTileColor: 'greenyellow', //yellow, greenyellow, turquoise,
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
	ancestryBarSz: defaultLytOpts.minTileSz * 2, //px (breadth of ancestry-bar area)
};

// Type representing auto-mode actions
type Action = 'move across' | 'move down' | 'move up' | 'expand' | 'collapse' | 'expand to view' | 'expand ancestry bar';
// Used in auto-mode to help avoid action cycles
function getReverseAction(action: Action): Action | null {
	switch (action){
		case 'move across':
			return null;
		case 'move down':
			return 'move up';
		case 'move up':
			return 'move down';
		case 'expand':
			return 'collapse';
		case 'collapse':
			return 'expand';
		case 'expand to view':
			return 'expand ancestry bar';
		case 'expand ancestry bar':
			return 'expand to view';
	}
}

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
			autoPrevAction: null as Action | null, // Used in auto-mode for reducing action cycles
			autoPrevActionFail: false, // Used in auto-mode to avoid re-trying a failed expand/collapse
			helpOpen: false,
			// Options
			lytOpts: {...defaultLytOpts},
			uiOpts: {...defaultUiOpts},
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
		tileAreaPos(){
			let pos = [this.tileAreaOffset, this.tileAreaOffset] as [number, number];
			if (this.detachedAncestors != null){
				if (this.wideArea){
					pos[0] += this.ancestryBarSz;
				} else {
					pos[1] += this.ancestryBarSz;
				}
			}
			return pos;
		},
		tileAreaDims(){
			let dims = [
				this.width - this.tileAreaOffset*2,
				this.height - this.tileAreaOffset*2
			] as [number, number];
			if (this.detachedAncestors != null){
				if (this.wideArea){
					dims[0] -= this.ancestryBarSz;
				} else {
					dims[1] -= this.ancestryBarSz;
				}
			}
			return dims;
		},
		ancestryBarDims(): [number, number] {
			if (this.wideArea){
				return [this.ancestryBarSz, this.height];
			} else {
				return [this.width, this.ancestryBarSz];
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
					this.tileAreaPos, this.tileAreaDims, this.lytOpts, true);
				// Prevent re-triggering until after a delay
				this.resizeThrottled = true;
				setTimeout(() => {this.resizeThrottled = false;}, this.resizeDelay);
			}
		},
		// For tile expand/collapse events
		onInnerLeafClicked(layoutNode: LayoutNode){
			let success = tryLayout(this.activeRoot, this.layoutMap,
				this.tileAreaPos, this.tileAreaDims, this.lytOpts, false, {type: 'expand', node: layoutNode});
			if (!success){
				layoutNode.expandFailFlag = !layoutNode.expandFailFlag; // Triggers failure animation
			}
			return success;
		},
		onInnerHeaderClicked(layoutNode: LayoutNode){
			let oldChildren = layoutNode.children;
			let success = tryLayout(this.activeRoot, this.layoutMap,
				this.tileAreaPos, this.tileAreaDims, this.lytOpts, false, {type: 'collapse', node: layoutNode});
			if (!success){
				layoutNode.collapseFailFlag = !layoutNode.collapseFailFlag; // Triggers failure animation
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
				this.tileAreaPos, this.tileAreaDims, this.lytOpts, true, {type: 'expand', node: layoutNode});
		},
		onInnerHeaderClickHeld(layoutNode: LayoutNode){
			if (layoutNode == this.activeRoot){
				console.log('Ignored expand-to-view on active-root node');
				return;
			}
			LayoutNode.hideUpward(layoutNode);
			this.activeRoot = layoutNode;
			tryLayout(this.activeRoot, this.layoutMap, this.tileAreaPos, this.tileAreaDims, this.lytOpts, true);
		},
		onDetachedAncestorClicked(layoutNode: LayoutNode){
			LayoutNode.showDownward(layoutNode);
			this.activeRoot = layoutNode;
			tryLayout(this.activeRoot, this.layoutMap, this.tileAreaPos, this.tileAreaDims, this.lytOpts, true);
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
			tryLayout(this.activeRoot, this.layoutMap, this.tileAreaPos, this.tileAreaDims, this.lytOpts, true);
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
			// If hidden, expand ancestor in ancestry-bar
			if (layoutNode.hidden){
				// Get self/ancestor in ancestry-bar
				while (!this.detachedAncestors!.includes(layoutNode)){
					ancestor = ancestor.parent!;
					layoutNode = this.layoutMap.get(ancestor.name)!;
				}
				this.onDetachedAncestorClicked(layoutNode!);
				setTimeout(() => this.expandToTolNode(tolNode), this.uiOpts.transitionDuration);
				return;
			}
			// Attempt tile-expand
			let success = this.onInnerLeafClicked(layoutNode);
			if (success){
				setTimeout(() => this.expandToTolNode(tolNode), this.uiOpts.transitionDuration);
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
			setTimeout(() => this.expandToTolNode(tolNode), this.uiOpts.transitionDuration);
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
				// Pick random leaf LayoutNode
				let layoutNode = this.activeRoot;
				while (layoutNode.children.length > 0){
					let childWeights = layoutNode.children.map(n => n.dCount);
					let idx = randWeightedChoice(childWeights);
					layoutNode = layoutNode.children[idx!];
				}
				this.setLastFocused(layoutNode);
				setTimeout(this.autoAction, this.autoWaitTime);
			} else {
				// Determine available actions
				let action: Action | null;
				let actionWeights: {[key: string]: number}; // Maps actions to choice weights
				let node = this.lastFocused;
				if (node.children.length == 0){
					actionWeights = {'move across': 1, 'move up': 2, 'expand': 4};
					// Zero weights for disallowed actions
					if (node == this.activeRoot || node.parent!.children.length == 1){
						actionWeights['move across'] = 0;
					}
					if (node == this.activeRoot){
						actionWeights['move up'] = 0;
					}
					if (node.tolNode.children.length == 0){
						actionWeights['expand'] = 0;
					}
				} else {
					actionWeights = {
						'move across': 1, 'move down': 2, 'move up': 1,
						'collapse': 1, 'expand to view': 0.5, 'expand ancestry bar': 0.5
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
					case 'move across':
						let siblings = node.parent!.children.filter(n => n != node);
						let siblingWeights = siblings.map(n => n.dCount + 1);
						this.setLastFocused(siblings[randWeightedChoice(siblingWeights)!]);
						break;
					case 'move down':
						let childWeights = node.children.map(n => n.dCount + 1);
						this.setLastFocused(node.children[randWeightedChoice(childWeights)!]);
						break;
					case 'move up':
						this.setLastFocused(node.parent!);
						break;
					case 'expand':
						this.autoPrevActionFail = !this.onInnerLeafClicked(node);
						break;
					case 'collapse':
						this.autoPrevActionFail = !this.onInnerHeaderClicked(node);
						break;
					case 'expand to view':
						this.onInnerHeaderClickHeld(node);
						break;
					case 'expand ancestry bar':
						this.onDetachedAncestorClicked(node.parent!);
						break;
				}
				setTimeout(this.autoAction, this.uiOpts.transitionDuration + this.autoWaitTime);
				this.autoPrevAction = action;
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
		tryLayout(this.activeRoot, this.layoutMap, this.tileAreaPos, this.tileAreaDims, this.lytOpts, true);
	},
	unmounted(){
		window.removeEventListener('resize', this.onResize);
		window.removeEventListener('keyup', this.onKeyUp);
	},
	components: {
		Tile, AncestryBar, TileInfoModal, SettingsPane, SearchModal, HelpModal,
		SearchIcon, PlayIcon, HelpIcon, SettingsIcon,
	},
});
</script>

<template>
<div :style="styles">
	<tile :layoutNode="layoutTree" :lytOpts="lytOpts" :uiOpts="uiOpts"
		@leaf-clicked="onInnerLeafClicked" @header-clicked="onInnerHeaderClicked"
		@leaf-click-held="onInnerLeafClickHeld" @header-click-held="onInnerHeaderClickHeld"
		@info-icon-clicked="onInnerInfoIconClicked"/>
	<ancestry-bar v-if="detachedAncestors != null"
		:pos="[0,0]" :dims="ancestryBarDims" :nodes="detachedAncestors"
		:lytOpts="lytOpts" :uiOpts="uiOpts"
		@detached-ancestor-clicked="onDetachedAncestorClicked" @info-icon-clicked="onInnerInfoIconClicked"/>
	<!-- Icons -->
	<search-icon @click="onSearchIconClick"
		class="absolute top-[6px] right-[54px] w-[18px] h-[18px] text-white/40 hover:text-white hover:cursor-pointer"/>
	<play-icon @click="onPlayIconClick"
		class="absolute top-[6px] right-[30px] w-[18px] h-[18px] text-white/40 hover:text-white hover:cursor-pointer"/>
	<help-icon @click="onHelpIconClick"
		class="absolute top-[6px] right-[6px] w-[18px] h-[18px] text-white/40 hover:text-white hover:cursor-pointer"/>
	<!-- Modals -->
	<transition name="fade">
		<tile-info-modal v-if="infoModalNode != null" :tolNode="infoModalNode" :uiOpts="uiOpts"
			@info-modal-close="onInfoModalClose"/>
	</transition>
	<transition name="fade">
		<search-modal v-if="searchOpen" :layoutTree="layoutTree" :tolMap="tolMap" :uiOpts="uiOpts"
			@search-close="onSearchClose" @search-node="onSearchNode" ref="searchModal"/>
	</transition>
	<transition name="fade">
		<help-modal v-if="helpOpen" :uiOpts="uiOpts" @help-modal-close="onHelpModalClose"/>
	</transition>
	<!-- Settings -->
	<transition name="slide-bottom-right">
		<settings-pane v-if="settingsOpen" :lytOpts="lytOpts" :uiOpts="uiOpts"
			@settings-close="onSettingsClose" @layout-option-change="onLayoutOptionChange"/>
		<!-- outer div prevents transition interference with inner rotate -->
		<div v-else class="absolute bottom-0 right-0 w-[100px] h-[100px] invisible">
			<div class="absolute bottom-[-50px] right-[-50px] w-[100px] h-[100px] visible -rotate-45
				bg-black text-white hover:cursor-pointer" @click="onSettingsIconClick">
				<settings-icon class="w-6 h-6 mx-auto mt-2"/>
			</div>
		</div>
	</transition>
	<!-- Overlay used to prevent interaction and capture clicks -->
	<div :style="{visibility: animationActive ? 'visible' : 'hidden'}"
		class="absolute left-0 top-0 w-full h-full" @click="onOverlayClick"></div>
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
