<template>
<div class="absolute left-0 top-0 w-screen h-screen overflow-hidden flex flex-col"
	:style="{backgroundColor: uiOpts.bgColor}">
	<!-- Title bar -->
	<div class="flex shadow gap-2 p-2" :style="{backgroundColor: uiOpts.bgColorDark2}">
		<h1 class="my-auto ml-2 text-3xl" :style="{color: uiOpts.altColor}">Tilo</h1>
		<div class="mx-auto"/> <!-- Spacer -->
		<!-- Icons -->
		<icon-button v-if="!uiOpts.disabledActions.has('search')" :style="buttonStyles" @click="onSearchIconClick">
			<search-icon/>
		</icon-button>
		<icon-button v-if="!uiOpts.disabledActions.has('autoMode')" :style="buttonStyles" @click="onAutoIconClick">
			<play-icon/>
		</icon-button>
		<icon-button v-if="!uiOpts.disabledActions.has('settings')" :style="buttonStyles" @click="onSettingsIconClick">
			<settings-icon/>
		</icon-button>
		<icon-button v-if="!uiOpts.disabledActions.has('help')" :style="buttonStyles" @click="onHelpIconClick">
			<help-icon/>
		</icon-button>
	</div>
	<!-- Content area -->
	<div :style="tutPaneContainerStyles"> <!-- Used to slide-in/out the tutorial pane -->
		<transition name="fade" @after-enter="tutPaneInTransition = false" @after-leave="tutPaneInTransition = false">
			<tutorial-pane v-if="tutPaneOpen" :style="{height: uiOpts.tutPaneSz + 'px'}"
				:uiOpts="uiOpts" :triggerFlag="tutTriggerFlag" :skipWelcome="!tutWelcome"
				@close="onTutPaneClose" @skip="onTutorialSkip" @stage-chg="onTutStageChg"/>
		</transition>
	</div>
	<div :class="['flex', wideArea ? 'flex-row' : 'flex-col', 'grow', 'min-h-0']" ref="mainArea">
		<div :style="ancestryBarContainerStyles"> <!-- Used to slide-in/out the ancestry-bar -->
			<transition name="fade"
				@after-enter="ancestryBarInTransition = false" @after-leave="ancestryBarInTransition = false">
				<ancestry-bar v-if="detachedAncestors != null" class="w-full h-full"
					:nodes="detachedAncestors" :vert="wideArea" :tolMap="tolMap" :lytOpts="lytOpts" :uiOpts="uiOpts"
					@ancestor-click="onDetachedAncestorClick" @info-click="onInfoClick"/>
			</transition>
		</div>
		<div class="relative grow" :style="{margin: lytOpts.tileSpacing + 'px'}" ref="tileArea">
			<tile :layoutNode="layoutTree" :tolMap="tolMap" :lytOpts="lytOpts" :uiOpts="uiOpts"
				:overflownDim="overflownRoot ? tileAreaDims[1] : 0" :skipTransition="justInitialised"
				@leaf-click="onLeafClick" @nonleaf-click="onNonleafClick"
				@leaf-click-held="onLeafClickHeld" @nonleaf-click-held="onNonleafClickHeld"
				@info-click="onInfoClick"/>
		</div>
	</div>
	<!-- Modals -->
	<transition name="fade">
		<search-modal v-if="searchOpen" :tolMap="tolMap" :lytOpts="lytOpts" :uiOpts="uiOpts" ref="searchModal"
			@close="searchOpen = false" @search="onSearch" @info-click="onInfoClick" @setting-chg="onSettingChg" />
	</transition>
	<transition name="fade">
		<tile-info-modal v-if="infoModalNodeName != null"
			:nodeName="infoModalNodeName" :tolMap="tolMap" :lytOpts="lytOpts" :uiOpts="uiOpts"
			@close="infoModalNodeName = null"/>
	</transition>
	<transition name="fade">
		<help-modal v-if="helpOpen" :uiOpts="uiOpts" @close="helpOpen = false" @start-tutorial="onStartTutorial"/>
	</transition>
	<settings-modal v-if="settingsOpen" :lytOpts="lytOpts" :uiOpts="uiOpts" class="z-10"
		@close="settingsOpen = false" @reset="onResetSettings" @setting-chg="onSettingChg"/>
	<!-- Overlay used to prevent interaction and capture clicks -->
	<div :style="{visibility: modeRunning ? 'visible' : 'hidden'}"
		class="absolute left-0 top-0 w-full h-full" @click="modeRunning = false"></div>
</div>
</template>

<script lang="ts">
import {defineComponent, PropType} from 'vue';
// Components
import Tile from './components/Tile.vue';
import TileInfoModal from './components/TileInfoModal.vue';
import SearchModal from './components/SearchModal.vue';
import SettingsModal from './components/SettingsModal.vue';
import HelpModal from './components/HelpModal.vue';
import AncestryBar from './components/AncestryBar.vue';
import TutorialPane from './components/TutorialPane.vue';
import IconButton from './components/IconButton.vue';
// Icons
import SearchIcon from './components/icon/SearchIcon.vue';
import PlayIcon from './components/icon/PlayIcon.vue';
import SettingsIcon from './components/icon/SettingsIcon.vue';
import HelpIcon from './components/icon/HelpIcon.vue';
// Other
	// Note: Import paths lack a .ts or .js extension because .ts makes vue-tsc complain, and .js makes vite complain
import {TolNode, TolMap, Action, UiOptions} from './lib';
import {LayoutNode, LayoutOptions, LayoutTreeChg} from './layout';
import {initLayoutTree, initLayoutMap, tryLayout} from './layout';
import {arraySum, randWeightedChoice, getScrollBarWidth, getBreakpoint} from './util';

// Type representing auto-mode actions
type AutoAction = 'move across' | 'move down' | 'move up' | Action;
// Function used in auto-mode to help avoid action cycles
function getReverseAction(action: AutoAction): AutoAction | null {
	const reversePairs: AutoAction[][] = [
		['move down', 'move up'],
		['expand', 'collapse'],
		['expandToView', 'unhideAncestor'],
	];
	let pair = reversePairs.find(pair => pair.includes(action));
	if (pair != null){
		return pair[0] == action ? pair[1] : pair[0];
	} else {
		return null;
	}
}
// For options
function getDefaultLytOpts(): LayoutOptions {
	let screenSz = getBreakpoint();
	return {
		tileSpacing: screenSz == 'sm' ? 6 : 10, //px
		headerSz: 22, // px
		minTileSz: 50, // px
		maxTileSz: 200, // px
		// Layout-algorithm related
		layoutType: 'sweep', // 'sqr' | 'rect' | 'sweep'
		rectMode: 'auto first-row', // 'horz' | 'vert' | 'linear' | 'auto' | 'auto first-row'
		rectSensitivity: 0.9, // Between 0 and 1
		sweepMode: 'left', // 'left' | 'top' | 'shorter' | 'auto'
		sweptNodesPrio: 'sqrt', // 'linear' | 'sqrt' | 'pow-2/3'
		sweepToParent: 'prefer', // 'none' | 'prefer' | 'fallback'
	};
}
function getDefaultUiOpts(lytOpts: LayoutOptions): UiOptions {
	let screenSz = getBreakpoint();
	// Reused option values
	let textColor = '#fafaf9', textColorAlt = '#1c1917';
	let bgColor = '#292524',
		bgColorLight = '#44403c', bgColorDark = '#1c1917',
		bgColorLight2 = '#57534e', bgColorDark2 = '#0e0c0b',
		bgColorAlt = '#fafaf9', bgColorAltDark = '#a8a29e';
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
		ancestryBarBreadth: lytOpts.maxTileSz / 2 + lytOpts.tileSpacing*2 + scrollGap, // px
		tutPaneSz: 200, // px
		scrollGap,
		// Timing related
		clickHoldDuration: 400, // ms
		transitionDuration: 300, // ms
		animationDelay: 100, // ms
		autoActionDelay: 500, // ms
		// Other
		useReducedTree: false,
		searchSuggLimit: 10,
		searchJumpMode: false,
		tutorialSkip: false,
		disabledActions: new Set() as Set<Action>,
	};
}
const lytOptPrefix = 'LYT '; // Used when saving to localStorage
const uiOptPrefix = 'UI ';

export default defineComponent({
	data(){
		// Initial tree-of-life data
		let initialTolMap: TolMap = new Map();
		initialTolMap.set("", new TolNode());
		let layoutTree = initLayoutTree(initialTolMap, "", 0);
		layoutTree.hidden = true;
		// Get/load option values
		let lytOpts = this.getLytOpts();
		let uiOpts = this.getUiOpts();
		//
		return {
			// Tree/layout data
			tolMap: initialTolMap,
			layoutTree: layoutTree,
			activeRoot: layoutTree, // Root of the displayed subtree
			layoutMap: initLayoutMap(layoutTree), // Maps names to LayoutNodes
			overflownRoot: false, // Set when displaying a root tile with many children, with overflow
			// For modals
			infoModalNodeName: null as string | null, // Name of node to display info for, or null
			searchOpen: false,
			settingsOpen: false,
			helpOpen: false,
			// For search and auto-mode
			modeRunning: false,
			lastFocused: null as LayoutNode | null, // Used to un-focus 
			// For auto-mode
			autoPrevAction: null as AutoAction | null, // Used to help prevent action cycles
			autoPrevActionFail: false, // Used to avoid re-trying a failed expand/collapse
			// For tutorial pane
			tutPaneOpen: !uiOpts.tutorialSkip,
			tutWelcome: !uiOpts.tutorialSkip,
			tutTriggerAction: null as Action | null, // Used to advance tutorial upon user-actions
			tutTriggerFlag: false,
			// Options
			lytOpts: lytOpts,
			uiOpts: uiOpts,
			// For layout and resize-handling
			mainAreaDims: [0, 0] as [number, number],
			tileAreaDims: [0, 0] as [number, number],
			lastResizeHdlrTime: 0, // Used to throttle resize handling
			pendingResizeHdlr: 0, // Set via setTimeout() for a non-initial resize event
			// For transitions
			ancestryBarInTransition: false,
			tutPaneInTransition: false,
			// Other
			justInitialised: false, // Used to skip transition for tile initially loaded from server
			changedSweepToParent: false, // Set during search animation for efficiency
			excessTolNodeThreshold: 1000, // Threshold where excess tolMap entries get removed
		};
	},
	computed: {
		wideArea(): boolean {
			return this.mainAreaDims[0] > this.mainAreaDims[1];
		},
		// Nodes to show in ancestry-bar (ordered from root downwards)
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
		// Styles
		buttonStyles(): Record<string,string> {
			return {
				color: this.uiOpts.textColor,
				backgroundColor: this.uiOpts.altColorDark,
			};
		},
		tutPaneContainerStyles(): Record<string,string> {
			return {
				minHeight: (this.tutPaneOpen ? this.uiOpts.tutPaneSz : 0) + 'px',
				maxHeight: (this.tutPaneOpen ? this.uiOpts.tutPaneSz : 0) + 'px',
				transitionDuration: this.uiOpts.transitionDuration + 'ms',
				transitionProperty: 'max-height, min-height',
				overflow: 'hidden',
			};
		},
		ancestryBarContainerStyles(): Record<string,string> {
			let ancestryBarBreadth = this.detachedAncestors == null ? 0 : this.uiOpts.ancestryBarBreadth;
			let styles = {
				minWidth: 'auto',
				maxWidth: 'none',
				minHeight: 'auto',
				maxHeight: 'none',
				transitionDuration: this.uiOpts.transitionDuration + 'ms',
				transitionProperty: '',
				overflow: 'hidden',
			};
			if (this.wideArea){
				styles.minWidth = ancestryBarBreadth + 'px';
				styles.maxWidth = ancestryBarBreadth + 'px';
				styles.transitionProperty = 'min-width, max-width';
			} else {
				styles.minHeight = ancestryBarBreadth + 'px';
				styles.maxHeight = ancestryBarBreadth + 'px';
				styles.transitionProperty = 'min-height, max-height';
			}
			return styles;
		},
	},
	methods: {
		// For tile expand/collapse events
		async onLeafClick(layoutNode: LayoutNode): Promise<boolean> {
			if (this.uiOpts.disabledActions.has('expand')){
				return false;
			}
			this.handleActionForTutorial('expand');
			this.setLastFocused(null);
			// If clicking child of overflowing active-root
			if (this.overflownRoot){
				layoutNode.failFlag = !layoutNode.failFlag; // Triggers failure animation
				return false;
			}
			// Function for expanding tile
			let doExpansion = () => {
				let lytFnOpts = {
					allowCollapse: false,
					chg: {type: 'expand', node: layoutNode, tolMap: this.tolMap} as LayoutTreeChg,
					layoutMap: this.layoutMap
				};
				let success = tryLayout(this.activeRoot, this.tileAreaDims, this.lytOpts, lytFnOpts);
				// If expanding active-root with too many children to fit, allow overflow
				if (!success && layoutNode == this.activeRoot){
					success = tryLayout(this.activeRoot, this.tileAreaDims,
						{...this.lytOpts, layoutType: 'sqr-overflow'}, lytFnOpts);
					if (success){
						this.overflownRoot = true;
					}
				}
				//
				if (!success){
					layoutNode.failFlag = !layoutNode.failFlag; // Triggers failure animation
				}
				return success;
			};
			// Check if data for node-to-expand exists, getting from server if needed
			let tolNode = this.tolMap.get(layoutNode.name)!;
			if (!this.tolMap.has(tolNode.children[0])){
				let responseObj: {[x: string]: TolNode};
				try {
					let urlPath = '/data/node?name=' + encodeURIComponent(layoutNode.name)
					urlPath += this.uiOpts.useReducedTree ? '&tree=reduced' : '';
					let response = await fetch(urlPath);
					responseObj = await response.json();
				} catch (error){
					console.log('Error with retreiving tol-node data: ' + error);
					return false;
				}
				Object.getOwnPropertyNames(responseObj).forEach(n => {this.tolMap.set(n, responseObj[n])});
				return doExpansion();
			} else {
				return doExpansion();
			}
		},
		async onNonleafClick(layoutNode: LayoutNode, {skipClean = false} = {}): Promise<boolean> {
			if (this.uiOpts.disabledActions.has('collapse')){
				return false;
			}
			this.handleActionForTutorial('collapse');
			this.setLastFocused(null);
			//
			let success = tryLayout(this.activeRoot, this.tileAreaDims, this.lytOpts, {
				allowCollapse: false,
				chg: {type: 'collapse', node: layoutNode, tolMap: this.tolMap},
				layoutMap: this.layoutMap
			});
			if (!success){
				layoutNode.failFlag = !layoutNode.failFlag; // Triggers failure animation
			} else {
				// Update overflownRoot to indicate root was collapsed
				if (this.overflownRoot){
					this.overflownRoot = false;
				}
				// Possibly clear out excess nodes when a threshold is reached
				if (!skipClean){
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
			}
			return success;
		},
		// For expand-to-view and ancestry-bar events
		async onLeafClickHeld(layoutNode: LayoutNode): Promise<boolean> {
			if (this.uiOpts.disabledActions.has('expandToView')){
				return false;
			}
			this.handleActionForTutorial('expandToView');
			this.setLastFocused(null);
			// Special case for active root
			if (layoutNode == this.activeRoot){
				this.onLeafClick(layoutNode);
				return true;
			}
			// Function for expanding tile
			let doExpansion = async () => {
				// Hide ancestors
				LayoutNode.hideUpward(layoutNode, this.layoutMap);
				if (this.detachedAncestors == null){ // Account for ancestry-bar transition
					this.ancestryBarInTransition = true;
					this.relayoutDuringAncestryBarTransition();
				}
				this.activeRoot = layoutNode;
				// Relayout
				await this.updateAreaDims();
				this.overflownRoot = false;
				let lytFnOpts = {
					allowCollapse: false,
					chg: {type: 'expand', node: layoutNode, tolMap: this.tolMap} as LayoutTreeChg,
					layoutMap: this.layoutMap
				};
				let success = tryLayout(this.activeRoot, this.tileAreaDims, this.lytOpts, lytFnOpts);
				// If expanding active-root with too many children to fit, allow overflow
				if (!success){
					success = tryLayout(this.activeRoot, this.tileAreaDims,
						{...this.lytOpts, layoutType: 'sqr-overflow'}, lytFnOpts);
					if (success){
						this.overflownRoot = true;
					}
				}
				//
				if (!success){
					layoutNode.failFlag = !layoutNode.failFlag; // Triggers failure animation
				}
				return success;
			};
			// Check if data for node-to-expand exists, getting from server if needed
			let tolNode = this.tolMap.get(layoutNode.name)!;
			if (!this.tolMap.has(tolNode.children[0])){
				let responseObj: {[x: string]: TolNode};
				try {
					let urlPath = '/data/node?name=' + encodeURIComponent(layoutNode.name)
					urlPath += this.uiOpts.useReducedTree ? '&tree=reduced' : '';
					let response = await fetch(urlPath);
					responseObj = await response.json();
				} catch (error){
					console.log('Error with retreiving tol-node data: ' + error);
					return false;
				}
				Object.getOwnPropertyNames(responseObj).forEach(n => {this.tolMap.set(n, responseObj[n])});
				return doExpansion();
			} else {
				return doExpansion();
			}
		},
		async onNonleafClickHeld(layoutNode: LayoutNode): Promise<boolean> {
			if (this.uiOpts.disabledActions.has('expandToView')){
				return false;
			}
			this.handleActionForTutorial('expandToView');
			this.setLastFocused(null);
			// Special case for active root
			if (layoutNode == this.activeRoot){
				console.log('Ignored expand-to-view on active-root node');
				return false;
			}
			// Hide ancestors
			LayoutNode.hideUpward(layoutNode, this.layoutMap);
			if (this.detachedAncestors == null){ // Account for ancestry-bar transition
				this.ancestryBarInTransition = true;
				this.relayoutDuringAncestryBarTransition();
			}
			this.activeRoot = layoutNode;
			// Relayout
			await this.updateAreaDims();
			return this.relayoutWithCollapse();
		},
		async onDetachedAncestorClick(layoutNode: LayoutNode, {collapseAndNoRelayout = false} = {}): Promise<boolean> {
			if (this.uiOpts.disabledActions.has('unhideAncestor')){
				return false;
			}
			this.handleActionForTutorial('unhideAncestor');
			this.setLastFocused(null);
			// Unhide ancestors
			this.activeRoot = layoutNode;
			this.overflownRoot = false;
			if (layoutNode.parent == null){ // Account for ancestry-bar transition
				this.ancestryBarInTransition = true;
				this.relayoutDuringAncestryBarTransition();
			}
			//
			let success: boolean;
			if (collapseAndNoRelayout){
				if (this.uiOpts.disabledActions.has('collapse')){
					console.log('INFO: Ignored unhide-ancestor due to disabled collapse');
					return false;
				}
				success = await this.onNonleafClick(layoutNode, {skipClean: true});
			} else {
				await this.updateAreaDims();
				success = this.relayoutWithCollapse();
			}
			LayoutNode.showDownward(layoutNode);
			return success;
		},
		// For tile-info events
		onInfoClick(nodeName: string): void {
			this.handleActionForTutorial('tileInfo');
			if (!this.searchOpen){ // Close an active non-search mode
				this.resetMode();
			}
			this.infoModalNodeName = nodeName;
		},
		// For search events
		onSearchIconClick(): void {
			this.handleActionForTutorial('search');
			if (!this.searchOpen){
				this.resetMode();
				this.searchOpen = true;
			}
		},
		onSearch(name: string): void {
			if (this.modeRunning){
				console.log('WARNING: Unexpected search event while search/auto mode is running')
				return;
			}
			let disabledActions = this.uiOpts.disabledActions;
			if (disabledActions.has('expand') || disabledActions.has('expandToView') ||
				disabledActions.has('unhideAncestor')){
				console.log('INFO: Ignored search action due to disabled expand/expandToView');
				return;
			}
			//
			this.searchOpen = false;
			this.modeRunning = true;
			if (this.lytOpts.sweepToParent == 'fallback'){ // Temporary change for efficiency
				this.lytOpts.sweepToParent = 'prefer';
				this.changedSweepToParent = true;
			}
			this.expandToNode(name);
		},
		async expandToNode(name: string){
			if (!this.modeRunning){
				return;
			}
			// Check if node is displayed
			let targetNode = this.layoutMap.get(name);
			if (targetNode != null && !targetNode.hidden){
				this.setLastFocused(targetNode);
				this.modeRunning = false;
				this.afterSearch();
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
				let nodeInAncestryBar = layoutNode;
				while (!this.detachedAncestors!.includes(nodeInAncestryBar)){
					nodeInAncestryBar = nodeInAncestryBar.parent!;
				}
				if (!this.uiOpts.searchJumpMode){
					await this.onDetachedAncestorClick(nodeInAncestryBar!);
					setTimeout(() => this.expandToNode(name), this.uiOpts.transitionDuration);
				} else{
					await this.onDetachedAncestorClick(nodeInAncestryBar, {collapseAndNoRelayout: true});
					this.expandToNode(name);
				}
				return;
			}
			// Attempt tile-expand
			if (this.uiOpts.searchJumpMode){
				// Extend layout tree
				let tolNode = this.tolMap.get(name)!;
				let nodesToAdd = [name] as string[];
				while (tolNode.parent != layoutNode.name){
					nodesToAdd.push(tolNode.parent!);
					tolNode = this.tolMap.get(tolNode.parent!)!;
				}
				nodesToAdd.reverse();
				layoutNode.addDescendantChain(nodesToAdd, this.tolMap, this.layoutMap);
				// Expand-to-view on target-node's parent
				targetNode = this.layoutMap.get(name);
				await this.onLeafClickHeld(targetNode!.parent!);
				setTimeout(() => this.setLastFocused(targetNode!), this.uiOpts.transitionDuration);
				this.modeRunning = false;
				return;
			}
			if (this.overflownRoot){
				await this.onLeafClickHeld(layoutNode);
				setTimeout(() => this.expandToNode(name), this.uiOpts.transitionDuration);
				return;
			}
			let success = await this.onLeafClick(layoutNode);
			if (success){
				setTimeout(() => this.expandToNode(name), this.uiOpts.transitionDuration);
				return;
			}
			// Attempt expand-to-view on an ancestor halfway to the active root
			if (layoutNode == this.activeRoot){
				console.log('Screen too small to expand active root');
				this.modeRunning = false;
				return;
			}
			let ancestorChain = [layoutNode];
			while (layoutNode.parent! != this.activeRoot){
				layoutNode = layoutNode.parent!;
				ancestorChain.push(layoutNode);
			}
			layoutNode = ancestorChain[Math.floor((ancestorChain.length - 1) / 2)]
			await this.onNonleafClickHeld(layoutNode);
			setTimeout(() => this.expandToNode(name), this.uiOpts.transitionDuration);
		},
		afterSearch(): void {
			if (this.changedSweepToParent){
				this.lytOpts.sweepToParent = 'fallback';
				this.changedSweepToParent = false;
			}
		},
		// For auto-mode events
		onAutoIconClick(): void {
			let disabledActions = this.uiOpts.disabledActions;
			if (disabledActions.has('expand') || disabledActions.has('collapse') ||
				disabledActions.has('expandToView') || disabledActions.has('unhideAncestor')){
				console.log('INFO: Ignored auto-mode action due to disabled expand/collapse/etc');
				return;
			}
			//
			this.handleActionForTutorial('autoMode');
			this.resetMode();
			this.modeRunning = true;
			this.autoAction();
		},
		async autoAction(){
			if (!this.modeRunning){
				this.setLastFocused(null);
				return;
			}
			if (this.lastFocused == null){
				// Pick random leaf LayoutNode
				let layoutNode = this.activeRoot;
				while (layoutNode.children.length > 0){
					let childWeights = layoutNode.children.map(n => n.tips);
					let idx = randWeightedChoice(childWeights);
					layoutNode = layoutNode.children[idx!];
				}
				this.setLastFocused(layoutNode);
				setTimeout(this.autoAction, this.uiOpts.autoActionDelay);
			} else {
				// Determine available actions
				let action: AutoAction | null;
				let actionWeights: {[key: string]: number}; // Maps actions to choice weights
				let node: LayoutNode = this.lastFocused;
				if (node.children.length == 0){
					actionWeights = {'move across': 1, 'move up': 2, 'expand': 3};
				} else {
					actionWeights = {
						'move across': 1, 'move down': 2, 'move up': 1,
						'collapse': 1, 'expandToView': 1, 'unhideAncestor': 1
					};
				}
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
				if (!node.children.every(n => n.children.length == 0)){
					actionWeights['collapse'] = 0; // Only collapse if all children are leaves
				}
				if (node.parent != this.activeRoot){
					actionWeights['expandToView'] = 0; // Only expand-to-view if direct child of activeRoot
				}
				if (this.activeRoot.parent == null || node != this.activeRoot){
					actionWeights['unhideAncestor'] = 0; // Only expand ancestry-bar if able and activeRoot
				}
				// Avoid undoing previous action
				if (this.autoPrevAction != null){
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
					action = actionList[randWeightedChoice(weightList)!] as AutoAction;
				}
				// Perform action
				this.autoPrevAction = action;
				let success = true;
				try {
					switch (action){
						case 'move across': // Bias towards siblings with higher tips
							let siblings = node.parent!.children.filter(n => n != node);
							let siblingWeights = siblings.map(n => n.tips + 1);
							this.setLastFocused(siblings[randWeightedChoice(siblingWeights)!]);
							break;
						case 'move down': // Bias towards children with higher tips
							let childWeights = node.children.map(n => n.tips + 1);
							this.setLastFocused(node.children[randWeightedChoice(childWeights)!]);
							break;
						case 'move up':
							this.setLastFocused(node.parent!);
							break;
						case 'expand':
							success = await this.onLeafClick(node);
							break;
						case 'collapse':
							success = await this.onNonleafClick(node);
							break;
						case 'expandToView':
							success = await this.onNonleafClickHeld(node);
							break;
						case 'unhideAncestor':
							success = await this.onDetachedAncestorClick(node.parent!);
							break;
					}
				} catch (error) {
					this.autoPrevActionFail = true;
					return;
				}
				this.autoPrevActionFail = !success;
				setTimeout(this.autoAction, this.uiOpts.transitionDuration + this.uiOpts.autoActionDelay);
			}
		},
		// For settings events
		onSettingsIconClick(): void {
			this.handleActionForTutorial('settings');
			this.resetMode();
			this.settingsOpen = true;
		},
		async onSettingChg(setting: string){
			// Save in localStorage
			if (setting in this.lytOpts){
				localStorage.setItem(lytOptPrefix + setting, String(this.lytOpts[setting as keyof LayoutOptions]));
				this.relayoutWithCollapse();
			} else if (setting in this.uiOpts){
				localStorage.setItem(uiOptPrefix + setting, String(this.uiOpts[setting as keyof UiOptions]));
				if (setting == 'useReducedTree'){
					this.onTreeChange();
				}
			} else {
				throw new Error('Unexpected setting');
			}
			console.log(`Saved setting ${setting}`);
		},
		async onTreeChange(){
			if (this.activeRoot != this.layoutTree){
				// Collapse tree to root
				await this.onDetachedAncestorClick(this.layoutTree);
			}
			await this.onNonleafClick(this.layoutTree);
			await this.initTreeFromServer();
		},
		onResetSettings(): void {
			localStorage.clear();
			// Restore default options
			let defaultLytOpts = getDefaultLytOpts();
			let defaultUiOpts = getDefaultUiOpts(defaultLytOpts);
			if (this.uiOpts.useReducedTree != defaultUiOpts.useReducedTree){
				this.onTreeChange();
			}
			Object.assign(this.lytOpts, defaultLytOpts);
			Object.assign(this.uiOpts, defaultUiOpts);
			console.log('Settings reset');
			//
			this.relayoutWithCollapse();
		},
		// For help events
		onHelpIconClick(): void {
			this.handleActionForTutorial('help');
			this.resetMode();
			this.helpOpen = true;
		},
		// For tutorial-pane events
		onTutPaneClose(): void {
			this.tutPaneOpen = false;
			this.tutWelcome = false;
			this.uiOpts.disabledActions.clear();
			// Account for tutorial-pane transition
			this.tutPaneInTransition = true;
			this.relayoutDuringTutPaneTransition();
		},
		onTutStageChg(triggerAction: Action | null): void {
			this.tutWelcome = false;
			this.tutTriggerAction = triggerAction;
		},
		onTutorialSkip(): void {
			// Remember to skip in future sessions
			localStorage.setItem(uiOptPrefix + 'tutorialSkip', String(true));
		},
		onStartTutorial(): void {
			if (!this.tutPaneOpen){
				this.tutPaneOpen = true;
				// Account for tutorial-pane transition
				this.tutPaneInTransition = true;
				this.relayoutDuringTutPaneTransition();
			}
		},
		handleActionForTutorial(action: Action): void {
			if (!this.tutPaneOpen){
				return;
			}
			// Close welcome message on first action
			if (this.tutWelcome){
				this.onTutPaneClose();
			}
			// Tell TutorialPane if trigger-action was done
			if (this.tutTriggerAction == action){
				this.tutTriggerFlag = !this.tutTriggerFlag;
			}
		},
		// For other events
		async onResize(){
			// Handle event, delaying/ignoring if this was recently done
			if (this.pendingResizeHdlr == 0){
				let handleResize = async () => {
					// Update layout/ui options with defaults, excluding user-modified ones
					let lytOpts = getDefaultLytOpts();
					let uiOpts = getDefaultUiOpts(lytOpts);
					let changedTree = false;
					for (let prop of Object.getOwnPropertyNames(lytOpts) as (keyof LayoutOptions)[]){
						let item = localStorage.getItem(lytOptPrefix + prop);
						if (item == null && this.lytOpts[prop] != lytOpts[prop]){
							this.lytOpts[prop] = lytOpts[prop];
						}
					}
					for (let prop of Object.getOwnPropertyNames(uiOpts) as (keyof UiOptions)[]){
						let item = localStorage.getItem(uiOptPrefix + prop);
						//Not: Using JSON.stringify here to roughly deep-compare values
						if (item == null && JSON.stringify(this.uiOpts[prop]) != JSON.stringify(uiOpts[prop])){
							this.uiOpts[prop] = uiOpts[prop];
							if (prop == 'useReducedTree'){
								changedTree = true;
							}
						}
					}
					// Relayout
					this.overflownRoot = false;
					if (!changedTree){
						await this.updateAreaDims();
						this.relayoutWithCollapse();
					} else {
						this.onTreeChange();
					}
				};
				//
				let currentTime = new Date().getTime();
				if (currentTime - this.lastResizeHdlrTime > this.uiOpts.animationDelay){
					this.lastResizeHdlrTime = currentTime;
					await handleResize();
					this.lastResizeHdlrTime = new Date().getTime();
				} else {
					let remainingDelay = this.uiOpts.animationDelay - (currentTime - this.lastResizeHdlrTime);
					this.pendingResizeHdlr = setTimeout(async () => {
						this.pendingResizeHdlr = 0;
						await handleResize();
						this.lastResizeHdlrTime = new Date().getTime();
					}, remainingDelay);
				}
			}
		},
		onKeyUp(evt: KeyboardEvent): void {
			if (evt.key == 'Escape'){
				this.resetMode();
			} else if (evt.key == 'f' && evt.ctrlKey){
				// If no non-search modal is open, open/focus search bar
				if (this.infoModalNodeName == null && !this.helpOpen && !this.settingsOpen){
					evt.preventDefault();
					if (!this.searchOpen){
						this.onSearchIconClick();
					} else {
						(this.$refs.searchModal as InstanceType<typeof SearchModal>).focusInput();
					}
				}
			} else if (evt.key == 'F' && evt.ctrlKey){
				// If search bar is open, switch search mode
				if (this.searchOpen){
					this.uiOpts.searchJumpMode = !this.uiOpts.searchJumpMode;
					this.onSettingChg('searchJumpMode');
				}
			}
		},
		// For initialisation
		async initTreeFromServer(){
			// Query server
			let responseObj: {[x: string]: TolNode};
			try {
				let urlPath = '/data/node';
				urlPath += this.uiOpts.useReducedTree ? '?tree=reduced' : '';
				let response = await fetch(urlPath);
				responseObj = await response.json();
			} catch (error) {
				console.log('Error with retrieving tree data: ' + error);
				return;
			}
			// Get root node name
			let rootName = null;
			let nodeNames = Object.getOwnPropertyNames(responseObj);
			for (let n of nodeNames){
				if (responseObj[n].parent == null){
					rootName = n;
					break;
				}
			}
			if (rootName == null){
				console.log('ERROR: Server response has no root node');
				return;
			}
			// Initialise tree
			this.tolMap.clear();
			nodeNames.forEach(n => {this.tolMap.set(n, responseObj[n])});
			this.layoutTree = initLayoutTree(this.tolMap, rootName, 0);
			this.activeRoot = this.layoutTree;
			this.layoutMap = initLayoutMap(this.layoutTree);
			// Relayout
			await this.updateAreaDims();
			this.relayoutWithCollapse(false);
			// Skip initial transition
			this.justInitialised = true;
			setTimeout(() => {this.justInitialised = false}, this.uiOpts.transitionDuration);
		},
		getLytOpts(): LayoutOptions {
			let opts = getDefaultLytOpts();
			for (let prop of Object.getOwnPropertyNames(opts) as (keyof LayoutOptions)[]){
				let item = localStorage.getItem(lytOptPrefix + prop);
				if (item != null){
					switch (typeof(opts[prop])){
						case 'boolean': (opts[prop] as unknown as boolean) = Boolean(item); break;
						case 'number': (opts[prop] as unknown as number) = Number(item); break;
						case 'string': (opts[prop] as unknown as string) = item; break;
						default: console.log(`WARNING: Found saved layout setting "${prop}" with unexpected type`);
					}
				}
			}
			return opts;
		},
		getUiOpts(): UiOptions {
			let opts = getDefaultUiOpts(getDefaultLytOpts());
			for (let prop of Object.getOwnPropertyNames(opts) as (keyof UiOptions)[]){
				let item = localStorage.getItem(uiOptPrefix + prop);
				if (item != null){
					switch (typeof(opts[prop])){
						case 'boolean': (opts[prop] as unknown as boolean) = (item == 'true'); break;
						case 'number': (opts[prop] as unknown as number) = Number(item); break;
						case 'string': (opts[prop] as unknown as string) = item; break;
						default: console.log(`WARNING: Found saved UI setting "${prop}" with unexpected type`);
					}
				}
			}
			return opts;
		},
		// For transitions
		relayoutDuringAncestryBarTransition(): void {
			let timerId = setInterval(async () => {
				await this.updateAreaDims();
				this.relayoutWithCollapse();
				if (!this.ancestryBarInTransition){
					clearTimeout(timerId);
				}
			}, this.uiOpts.animationDelay);
			setTimeout(() => {
				if (this.ancestryBarInTransition){
					this.ancestryBarInTransition = false;
					clearTimeout(timerId);
					console.log('Reached timeout waiting for ancestry-bar transition-end event');
				}
			}, this.uiOpts.transitionDuration + 300);
		},
		relayoutDuringTutPaneTransition(): void {
			let timerId = setInterval(async () => {
				await this.updateAreaDims();
				this.relayoutWithCollapse();
				if (!this.tutPaneInTransition){
					clearTimeout(timerId);
				}
			}, this.uiOpts.animationDelay);
			setTimeout(() => {
				if (this.tutPaneInTransition){
					this.tutPaneInTransition = false;
					clearTimeout(timerId);
					console.log('Reached timeout waiting for tutorial-pane transition-end event');
				}
			}, this.uiOpts.transitionDuration + 300);
		},
		// For relayout
		relayoutWithCollapse(secondPass = true): boolean {
			let success;
			if (this.overflownRoot){
				success = tryLayout(this.activeRoot, this.tileAreaDims,
					{...this.lytOpts, layoutType: 'sqr-overflow'}, {allowCollapse: false, layoutMap: this.layoutMap});
			} else {
				success = tryLayout(this.activeRoot, this.tileAreaDims, this.lytOpts,
					{allowCollapse: true, layoutMap: this.layoutMap});
				if (secondPass){
					// Relayout again, which can help allocate remaining tiles 'evenly'
					success = tryLayout(this.activeRoot, this.tileAreaDims, this.lytOpts,
						{allowCollapse: false, layoutMap: this.layoutMap});
				}
			}
			return success;
		},
		async updateAreaDims(){
			let mainAreaEl = this.$refs.mainArea as HTMLElement;
			this.mainAreaDims = [mainAreaEl.offsetWidth, mainAreaEl.offsetHeight];
			await this.$nextTick(); // Wait until ancestor-bar is laid-out
			let tileAreaEl = this.$refs.tileArea as HTMLElement;
			this.tileAreaDims = [tileAreaEl.offsetWidth, tileAreaEl.offsetHeight];
		},
		// Other
		resetMode(): void {
			this.infoModalNodeName = null;
			this.searchOpen = false;
			this.afterSearch();
			this.settingsOpen = false;
			this.helpOpen = false;
			this.modeRunning = false;
			this.setLastFocused(null);
		},
		setLastFocused(node: LayoutNode | null): void {
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
		window.addEventListener('keydown', this.onKeyUp);
		this.initTreeFromServer();
	},
	unmounted(){
		window.removeEventListener('resize', this.onResize);
		window.removeEventListener('keydown', this.onKeyUp);
	},
	components: {
		Tile, TutorialPane, AncestryBar,
		IconButton, SearchIcon, PlayIcon, SettingsIcon, HelpIcon,
		TileInfoModal, SearchModal, SettingsModal, HelpModal,
	},
});
</script>

<style>
.fade-enter-from, .fade-leave-to {
	opacity: 0;
}
.fade-enter-active, .fade-leave-active {
	transition-property: opacity;
	transition-duration: 300ms;
	transition-timing-function: ease-out;
}
</style>
