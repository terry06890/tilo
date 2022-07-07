<template>
<div class="absolute left-0 top-0 w-screen h-screen overflow-hidden flex flex-col"
	:style="{backgroundColor: uiOpts.bgColor}">
	<!-- Title bar -->
	<div class="flex shadow gap-2 p-2" :style="{backgroundColor: uiOpts.bgColorDark2, color: uiOpts.altColor}">
		<h1 class="my-auto ml-2 text-4xl">Tilo</h1>
		<div class="mx-auto"/> <!-- Spacer -->
		<!-- Icons -->
		<icon-button :disabled="isDisabled('help')" :size="45" :style="buttonStyles" @click="onHelpIconClick">
			<help-icon/>
		</icon-button>
		<icon-button :disabled="isDisabled('settings')" :size="45" :style="buttonStyles" @click="onSettingsIconClick">
			<settings-icon/>
		</icon-button>
		<icon-button :disabled="isDisabled('autoMode')" :size="45" :style="buttonStyles" @click="onAutoIconClick">
			<play-icon v-if="modeRunning != 'autoMode'"/>
			<pause-icon v-else/>
		</icon-button>
		<icon-button :disabled="isDisabled('search')" :size="45" :style="buttonStyles" @click="onSearchIconClick">
			<search-icon/>
		</icon-button>
	</div>
	<!-- Content area -->
	<div class="grow min-h-0 flex flex-col" ref="contentArea">
		<div :style="tutPaneContainerStyles" class="z-10"> <!-- Used to slide-in/out the tutorial pane -->
			<transition name="fade">
				<tutorial-pane v-if="tutPaneOpen" :style="tutPaneStyles"
					:actionsDone="actionsDone" :triggerFlag="tutTriggerFlag" :skipWelcome="!tutWelcome"
					:uiOpts="uiOpts" @close="onTutPaneClose" @skip="onTutorialSkip" @stage-chg="onTutStageChg"/>
			</transition>
		</div>
		<div :class="['flex', wideMainArea ? 'flex-row' : 'flex-col', 'grow', 'min-h-0']"> <!-- 'Main area' -->
			<div :style="ancestryBarContainerStyles"> <!-- Used to slide-in/out the ancestry-bar -->
				<transition name="fade">
					<ancestry-bar v-if="detachedAncestors != null" class="w-full h-full"
						:nodes="detachedAncestors" :vert="wideMainArea" :breadth="uiOpts.ancestryBarBreadth"
						:tolMap="tolMap" :lytOpts="lytOpts" :uiOpts="uiOpts"
						@ancestor-click="onDetachedAncestorClick" @info-click="onInfoClick"/>
				</transition>
			</div>
			<div class="relative grow" :style="{margin: lytOpts.tileSpacing + 'px'}"> <!-- 'Tile area' -->
				<tile :layoutNode="layoutTree" :tolMap="tolMap" :lytOpts="lytOpts" :uiOpts="uiOpts"
					:overflownDim="overflownRoot ? tileAreaDims[1] : 0" :skipTransition="justInitialised"
					@leaf-click="onLeafClick" @nonleaf-click="onNonleafClick"
					@leaf-click-held="onLeafClickHeld" @nonleaf-click-held="onNonleafClickHeld"
					@info-click="onInfoClick"/>
			</div>
		</div>
	</div>
	<!-- Modals -->
	<transition name="fade">
		<search-modal v-if="searchOpen" :tolMap="tolMap" :lytMap="layoutMap" :lytOpts="lytOpts" :uiOpts="uiOpts"
			@close="onSearchClose" @search="onSearch" @info-click="onInfoClick" @setting-chg="onSettingChg"
			@net-wait="primeLoadInd('Loading data')" @net-get="endLoadInd" class="z-10" ref="searchModal"/>
	</transition>
	<transition name="fade">
		<tile-info-modal v-if="infoModalNodeName != null && infoModalData != null"
			:nodeName="infoModalNodeName" :infoResponse="infoModalData" :tolMap="tolMap" :lytOpts="lytOpts"
			:uiOpts="uiOpts" class="z-10" @close="infoModalNodeName = null"/>
	</transition>
	<transition name="fade">
		<help-modal v-if="helpOpen" :tutOpen="tutPaneOpen" :uiOpts="uiOpts" class="z-10"
			@close="helpOpen = false" @start-tutorial="onStartTutorial"/>
	</transition>
	<settings-modal v-if="settingsOpen" :lytOpts="lytOpts" :uiOpts="uiOpts" class="z-10"
		@close="settingsOpen = false" @reset="onResetSettings" @setting-chg="onSettingChg"/>
	<transition name="fade">
		<loading-modal v-if="loadingMsg != null" :msg="loadingMsg" :uiOpts="uiOpts" class="z-10"/>
	</transition>
	<!-- Overlay used to capture clicks during auto mode, etc -->
	<div :style="{visibility: modeRunning != null ? 'visible' : 'hidden'}"
		class="absolute left-0 top-0 w-full h-full z-20" @click="modeRunning = null"></div>
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
import LoadingModal from './components/LoadingModal.vue';
import IconButton from './components/IconButton.vue';
// Icons
import SearchIcon from './components/icon/SearchIcon.vue';
import PlayIcon from './components/icon/PlayIcon.vue';
import PauseIcon from './components/icon/PauseIcon.vue';
import SettingsIcon from './components/icon/SettingsIcon.vue';
import HelpIcon from './components/icon/HelpIcon.vue';
// Other
	// Note: Import paths lack a .ts or .js because .ts makes vue-tsc complain, and .js makes vite complain
import {TolNode, TolMap} from './tol';
import {LayoutNode, LayoutOptions, LayoutTreeChg,
	initLayoutTree, initLayoutMap, tryLayout} from './layout';
import {queryServer, InfoResponse, Action,
	UiOptions, getDefaultLytOpts, getDefaultUiOpts, OptionType} from './lib';
import {arraySum, randWeightedChoice, timeout} from './util';

// Type representing auto-mode actions
type AutoAction = 'move across' | 'move down' | 'move up' | Action;
// Function used in auto-mode to reduce action cycles
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

export default defineComponent({
	data(){
		// Create initial tree-of-life data
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
			infoModalData: null as InfoResponse | null,
			searchOpen: false,
			settingsOpen: false,
			helpOpen: false,
			loadingMsg: null as null | string, // Message to display in loading-indicator
			// For search and auto-mode
			modeRunning: null as null | 'search' | 'autoMode',
			lastFocused: null as LayoutNode | null, // Used to un-focus 
			// For auto-mode
			autoPrevAction: null as AutoAction | null, // Used to help prevent action cycles
			autoPrevActionFail: false, // Used to avoid re-trying a failed expand/collapse
			// For tutorial pane
			tutPaneOpen: !uiOpts.tutorialSkip,
			tutWelcome: !uiOpts.tutorialSkip,
			tutTriggerAction: null as Action | null, // Used to advance tutorial upon user-actions
			tutTriggerFlag: false,
			actionsDone: new Set() as Set<Action>, // Used to avoid disabling actions the user has already seen
			// Options
			lytOpts: lytOpts,
			uiOpts: uiOpts,
			// For layout and resize-handling
			mainAreaDims: [0, 0] as [number, number],
			tileAreaDims: [0, 0] as [number, number],
			lastResizeHdlrTime: 0, // Used to throttle resize handling
			afterResizeHdlr: 0, // Set via setTimeout() to execute after a run of resize events
			// Other
			justInitialised: false, // Used to skip transition for the tile initially loaded from server
			pendingLoadingRevealHdlr: 0, // Used to delay showing the loading-indicator modal
			changedSweepToParent: false, // Set during search animation for efficiency
			excessTolNodeThreshold: 1000, // Threshold where excess tolMap entries get removed
		};
	},
	computed: {
		wideMainArea(): boolean {
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
			if (this.uiOpts.breakpoint == 'sm'){
				return {
					minHeight: (this.tutPaneOpen ? this.uiOpts.tutPaneSz : 0) + 'px',
					maxHeight: (this.tutPaneOpen ? this.uiOpts.tutPaneSz : 0) + 'px',
					transitionProperty: 'max-height, min-height',
					transitionDuration: this.uiOpts.transitionDuration + 'ms',
					overflow: 'hidden',
				};
			} else {
				return {
					position: 'absolute',
					bottom: '0.5cm',
					right: '0.5cm',
					visibility: this.tutPaneOpen ? 'visible' : 'hidden',
					transitionProperty: 'visibility',
					transitionDuration: this.uiOpts.transitionDuration + 'ms',
				};
			}
		},
		tutPaneStyles(): Record<string,string>  {
			if (this.uiOpts.breakpoint == 'sm'){
				return {
					height: this.uiOpts.tutPaneSz + 'px',
				}
			} else {
				return {
					height: this.uiOpts.tutPaneSz + 'px',
					minWidth: '10cm',
					maxWidth: '10cm',
					borderRadius: this.uiOpts.borderRadius + 'px',
					boxShadow: '0 0 3px black',
				};
			}
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
			if (this.wideMainArea){
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
		async onLeafClick(layoutNode: LayoutNode, subAction = false): Promise<boolean> {
			if (!subAction){
				if (this.isDisabled('expand')){
					return false;
				}
				this.handleActionForTutorial('expand');
				this.setLastFocused(null);
			}
			// If clicking child of overflowing active-root
			if (this.overflownRoot){
				if (!this.uiOpts.autoHide){
					if (!subAction){
						layoutNode.failFlag = !layoutNode.failFlag; // Triggers failure animation
					}
					return false;
				} else {
					return await this.onLeafClickHeld(layoutNode);
				}
			}
			// Function for expanding tile
			let doExpansion = async () => {
				let lytFnOpts = {
					allowCollapse: false,
					chg: {type: 'expand', node: layoutNode, tolMap: this.tolMap} as LayoutTreeChg,
					layoutMap: this.layoutMap
				};
				let success = tryLayout(this.activeRoot, this.tileAreaDims, this.lytOpts, lytFnOpts);
				// Handle auto-hide
				if (!success && this.uiOpts.autoHide){
					while (!success && layoutNode != this.activeRoot){
						let node = layoutNode;
						while (node.parent != this.activeRoot){
							node = node.parent!;
						}
						await this.onNonleafClickHeld(node, true);
						this.updateAreaDims();
						success = tryLayout(this.activeRoot, this.tileAreaDims, this.lytOpts, lytFnOpts);
					}
				}
				// If expanding active-root with too many children to fit, allow overflow
				if (!success && layoutNode == this.activeRoot){
					success = tryLayout(this.activeRoot, this.tileAreaDims,
						{...this.lytOpts, layoutType: 'sqr-overflow'}, lytFnOpts);
					if (success){
						this.overflownRoot = true;
					}
				}
				//
				if (!subAction && !success){
					layoutNode.failFlag = !layoutNode.failFlag; // Triggers failure animation
				}
				return success;
			};
			// Check if data for node-to-expand exists, getting from server if needed
			let tolNode = this.tolMap.get(layoutNode.name)!;
			if (!this.tolMap.has(tolNode.children[0])){
				let urlParams = new URLSearchParams({type: 'node', name: layoutNode.name, tree: this.uiOpts.tree});
				let responseObj: {[x: string]: TolNode} = await this.loadFromServer(urlParams);
				if (responseObj == null){
					return false;
				}
				Object.getOwnPropertyNames(responseObj).forEach(n => {this.tolMap.set(n, responseObj[n])});
				return doExpansion();
			} else {
				return doExpansion();
			}
		},
		async onNonleafClick(layoutNode: LayoutNode, subAction = false): Promise<boolean> {
			if (!subAction){
				if (this.isDisabled('collapse')){
					return false;
				}
				this.handleActionForTutorial('collapse');
				this.setLastFocused(null);
			}
			// Relayout
			let success = tryLayout(this.activeRoot, this.tileAreaDims, this.lytOpts, {
				allowCollapse: false,
				chg: {type: 'collapse', node: layoutNode, tolMap: this.tolMap},
				layoutMap: this.layoutMap
			});
			// Update overflownRoot if root was collapsed
			if (success && this.overflownRoot){
				this.overflownRoot = false;
			}
			if (!subAction){
				if (!success){
					layoutNode.failFlag = !layoutNode.failFlag; // Triggers failure animation
				} else {
					// Possibly clear out excess nodes when a threshold is reached
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
		async onLeafClickHeld(layoutNode: LayoutNode, subAction = false): Promise<boolean> {
			// Special case for active root
			if (layoutNode == this.activeRoot){
				console.log('Ignored expand-to-view on active-root node');
				return false;
			}
			//
			if (!subAction){
				if (this.isDisabled('expandToView')){
					return false;
				}
				this.handleActionForTutorial('expandToView');
				this.setLastFocused(null);
			}
			// Function for expanding tile
			let doExpansion = async () => {
				// Hide ancestors
				LayoutNode.hideUpward(layoutNode, this.layoutMap);
				this.activeRoot = layoutNode;
				// Relayout
				this.updateAreaDims();
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
				if (!success && !subAction){
					layoutNode.failFlag = !layoutNode.failFlag; // Triggers failure animation
				}
				return success;
			};
			// Check if data for node-to-expand exists, getting from server if needed
			let tolNode = this.tolMap.get(layoutNode.name)!;
			if (!this.tolMap.has(tolNode.children[0])){
				let urlParams = new URLSearchParams({type: 'node', name: layoutNode.name, tree: this.uiOpts.tree});
				let responseObj: {[x: string]: TolNode} = await this.loadFromServer(urlParams);
				if (responseObj == null){
					return false;
				}
				Object.getOwnPropertyNames(responseObj).forEach(n => {this.tolMap.set(n, responseObj[n])});
				return doExpansion();
			} else {
				return doExpansion();
			}
		},
		async onNonleafClickHeld(layoutNode: LayoutNode, subAction = false): Promise<boolean> {
			// Special case for active root
			if (layoutNode == this.activeRoot){
				console.log('Ignored expand-to-view on active-root node');
				return false;
			}
			//
			if (!subAction){
				if (this.isDisabled('expandToView')){
					return false;
				}
				this.handleActionForTutorial('expandToView');
				this.setLastFocused(null);
			}
			// Hide ancestors
			LayoutNode.hideUpward(layoutNode, this.layoutMap);
			this.activeRoot = layoutNode;
			// Relayout
			this.updateAreaDims();
			return this.relayoutWithCollapse();
		},
		async onDetachedAncestorClick(layoutNode: LayoutNode, subAction = false, collapse = false): Promise<boolean> {
			if (!subAction){
				if (this.isDisabled('unhideAncestor')){
					return false;
				}
				this.handleActionForTutorial('unhideAncestor');
				this.setLastFocused(null);
			}
			// Unhide ancestors
			this.activeRoot = layoutNode;
			this.overflownRoot = false;
			//
			let success: boolean;
			this.updateAreaDims();
			if (!collapse){
				// Relayout, attempting to have the ancestor expanded
				this.relayoutWithCollapse(false);
				if (layoutNode.children.length > 0){
					success = this.relayoutWithCollapse(false); // Second pass for regularity
				} else {
					success = await this.onLeafClick(layoutNode, true);
				}
			} else {
				success = await this.onNonleafClick(layoutNode, true); // For reducing tile-flashing on-screen
			}
			LayoutNode.showDownward(layoutNode);
			return success;
		},
		// For tile-info events
		async onInfoClick(nodeName: string){
			if (!this.searchOpen){ // Close an active non-search mode
				this.resetMode();
			}
			// Query server for tol-node info
			let urlParams = new URLSearchParams({type: 'info', name: nodeName, tree: this.uiOpts.tree});
			let responseObj: InfoResponse = await this.loadFromServer(urlParams);
			if (responseObj == null){
				return;
			}
			// Set fields from response
			this.infoModalNodeName = nodeName;
			this.infoModalData = responseObj;
		},
		// For search events
		onSearchIconClick(): void {
			if (this.isDisabled('search')){
				return;
			}
			if (!this.searchOpen){
				this.resetMode();
				this.searchOpen = true;
			}
		},
		onSearch(name: string): void {
			if (this.modeRunning != null){
				console.log('WARNING: Unexpected search event while search/auto mode is running')
				return;
			}
			this.searchOpen = false;
			this.modeRunning = 'search';
			this.expandToNode(name);
		},
		async expandToNode(name: string){
			if (this.modeRunning == null){
				return;
			}
			// Check if node is displayed
			let targetNode = this.layoutMap.get(name);
			if (targetNode != null && !targetNode.hidden){
				this.setLastFocused(targetNode);
				this.modeRunning = null;
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
					await this.onDetachedAncestorClick(nodeInAncestryBar!, true);
					setTimeout(() => this.expandToNode(name), this.uiOpts.transitionDuration);
				} else{
					await this.onDetachedAncestorClick(nodeInAncestryBar!, true, true);
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
				await this.onLeafClickHeld(targetNode!.parent!, true);
				setTimeout(() => this.setLastFocused(targetNode!), this.uiOpts.transitionDuration);
				this.modeRunning = null;
				return;
			}
			if (this.overflownRoot){
				await this.onLeafClickHeld(layoutNode, true);
				setTimeout(() => this.expandToNode(name), this.uiOpts.transitionDuration);
				return;
			}
			let success = await this.onLeafClick(layoutNode, true);
			if (success){
				setTimeout(() => this.expandToNode(name), this.uiOpts.transitionDuration);
				return;
			}
			// Attempt expand-to-view on an ancestor halfway to the active root
			if (layoutNode == this.activeRoot){
				console.log('Screen too small to expand active root');
				this.modeRunning = null;
				return;
			}
			let ancestorChain = [layoutNode];
			while (layoutNode.parent! != this.activeRoot){
				layoutNode = layoutNode.parent!;
				ancestorChain.push(layoutNode);
			}
			layoutNode = ancestorChain[Math.floor((ancestorChain.length - 1) / 2)]
			await this.onNonleafClickHeld(layoutNode, true);
			setTimeout(() => this.expandToNode(name), this.uiOpts.transitionDuration);
		},
		onSearchClose(){
			this.searchOpen = false;
			this.handleActionForTutorial('search');
		},
		// For auto-mode events
		onAutoIconClick(): void {
			if (this.isDisabled('autoMode')){
				return;
			}
			this.resetMode();
			this.modeRunning = 'autoMode';
			this.autoAction();
		},
		async autoAction(){
			if (this.modeRunning == null){
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
							success = await this.onLeafClick(node, true);
							break;
						case 'collapse':
							success = await this.onNonleafClick(node, true);
							break;
						case 'expandToView':
							success = await this.onNonleafClickHeld(node, true);
							break;
						case 'unhideAncestor':
							success = await this.onDetachedAncestorClick(node.parent!, true);
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
			if (this.isDisabled('settings')){
				return;
			}
			this.resetMode();
			this.settingsOpen = true;
		},
		async onSettingChg(optionType: OptionType, option: string,
			{relayout = false, reinit = false} = {}){
			// Save setting
			if (optionType == 'LYT'){
				localStorage.setItem(`${optionType} ${option}`,
					String(this.lytOpts[option as keyof LayoutOptions]));
			} else if (optionType == 'UI') {
				localStorage.setItem(`${optionType} ${option}`,
					String(this.uiOpts[option as keyof UiOptions]));
			}
			// Possibly relayout/reinitialise
			if (reinit){
				this.reInit();
			} else if (relayout){
				this.relayoutWithCollapse();
			}
		},
		onResetSettings(reinit: boolean): void {
			localStorage.clear();
			if (reinit){
				this.reInit();
			} else {
				this.relayoutWithCollapse();
			}
		},
		// For help events
		onHelpIconClick(): void {
			if (this.isDisabled('help')){
				return;
			}
			this.resetMode();
			this.helpOpen = true;
			this.handleActionForTutorial('help');
		},
		// For tutorial-pane events
		onTutPaneClose(): void {
			this.tutPaneOpen = false;
			this.tutWelcome = false;
			this.uiOpts.disabledActions.clear();
			this.updateAreaDims();
			this.relayoutWithCollapse();
		},
		onTutStageChg(triggerAction: Action | null): void {
			this.tutWelcome = false;
			this.tutTriggerAction = triggerAction;
		},
		onTutorialSkip(): void {
			localStorage.setItem('UI tutorialSkip', String(true));
		},
		onStartTutorial(): void {
			if (!this.tutPaneOpen){
				this.tutPaneOpen = true;
				this.updateAreaDims();
				this.relayoutWithCollapse();
			}
		},
		handleActionForTutorial(action: Action): void {
			this.actionsDone.add(action);
			if (this.tutPaneOpen){
				// Close welcome message on first action
				if (this.tutWelcome){
					this.onTutPaneClose();
				}
				// Tell TutorialPane if trigger-action was done
				if (this.tutTriggerAction == action){
					this.tutTriggerFlag = !this.tutTriggerFlag;
				}
			}
		},
		// For the loading-indicator
		async loadFromServer(urlParams: URLSearchParams){ // Like queryServer(), but enables the loading indicator
			this.primeLoadInd('Loading data');
			let responseObj = await queryServer(urlParams);
			this.endLoadInd();
			return responseObj;
		},
		primeLoadInd(msg: string){
			this.pendingLoadingRevealHdlr = setTimeout(() => {
				this.loadingMsg = msg;
			}, 300);
		},
		endLoadInd(){
			clearTimeout(this.pendingLoadingRevealHdlr);
			this.pendingLoadingRevealHdlr = 0;
			if (this.loadingMsg != null){
				this.loadingMsg = null;
			}
		},
		// For other events
		async onResize(){
			// Handle event if not recently done
			let handleResize = async () => {
				// Update layout/ui options with defaults, excluding user-modified ones
				let lytOpts = getDefaultLytOpts();
				let uiOpts = getDefaultUiOpts(lytOpts);
				let changedTree = false;
				for (let prop of Object.getOwnPropertyNames(lytOpts) as (keyof LayoutOptions)[]){
					let item = localStorage.getItem('LYT ' + prop);
					if (item == null && this.lytOpts[prop] != lytOpts[prop]){
						this.lytOpts[prop] = lytOpts[prop];
					}
				}
				for (let prop of Object.getOwnPropertyNames(uiOpts) as (keyof UiOptions)[]){
					let item = localStorage.getItem('UI ' + prop);
					//Note: Using JSON.stringify here to roughly deep-compare values
					if (item == null && JSON.stringify(this.uiOpts[prop]) != JSON.stringify(uiOpts[prop])){
						this.uiOpts[prop] = uiOpts[prop];
						if (prop == 'tree'){
							changedTree = true;
						}
					}
				}
				// Relayout
				if (!changedTree){
					this.updateAreaDims();
					this.relayoutWithCollapse();
				} else {
					this.reInit();
				}
			};
			let currentTime = new Date().getTime();
			if (currentTime - this.lastResizeHdlrTime > this.uiOpts.animationDelay){
				this.lastResizeHdlrTime = currentTime;
				await handleResize();
				this.lastResizeHdlrTime = new Date().getTime();
			}
			// Also setup a handler to execute after a run of resize events
			clearTimeout(this.afterResizeHdlr);
			this.afterResizeHdlr = setTimeout(async () => {
				this.afterResizeHdlr = 0;
				await handleResize();
				this.lastResizeHdlrTime = new Date().getTime();
			}, 200); // If too small, touch-device detection when swapping to/from mobile-mode gets unreliable
		},
		onKeyUp(evt: KeyboardEvent): void {
			if (this.uiOpts.disableShortcuts){
				return;
			}
			if (evt.key == 'Escape'){
				this.resetMode();
			} else if (evt.key == 'f' && evt.ctrlKey){
				evt.preventDefault();
				// Open/focus search bar
				if (!this.searchOpen){
					this.onSearchIconClick();
				} else {
					(this.$refs.searchModal as InstanceType<typeof SearchModal>).focusInput();
				}
			} else if (evt.key == 'F' && evt.ctrlKey){
				// If search bar is open, switch search mode
				if (this.searchOpen){
					this.uiOpts.searchJumpMode = !this.uiOpts.searchJumpMode;
					this.onSettingChg('UI', 'searchJumpMode');
				}
			}
		},
		// For initialisation
		async initTreeFromServer(firstInit = true){
			// Get possible target node from URL
			let nodeName = (new URL(window.location.href)).searchParams.get('node');
			// Query server
			let urlParams = new URLSearchParams({type: 'node', tree: this.uiOpts.tree});
			if (nodeName != null){
				urlParams.append('name', nodeName);
				urlParams.append('toroot', 'true');
			}
			let responseObj: {[x: string]: TolNode} = await this.loadFromServer(urlParams);
			if (responseObj == null){
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
			if (nodeName == null){
				this.layoutTree = initLayoutTree(this.tolMap, rootName, 0);
				this.layoutMap = initLayoutMap(this.layoutTree);
				this.activeRoot = this.layoutTree;
			} else {
				this.layoutTree = initLayoutTree(this.tolMap, rootName, -1);
				this.layoutMap = initLayoutMap(this.layoutTree);
				// Set active root
				let targetNode = this.layoutMap.get(nodeName)!;
				let newRoot = targetNode.parent == null ? targetNode : targetNode.parent;
				LayoutNode.hideUpward(newRoot, this.layoutMap);
				this.activeRoot = newRoot;
				setTimeout(() => this.setLastFocused(targetNode!), this.uiOpts.transitionDuration);
			}
			// Skip initial transition
			if (firstInit){
				this.justInitialised = true;
				setTimeout(() => {this.justInitialised = false}, this.uiOpts.transitionDuration);
			}
			// Relayout
			this.updateAreaDims();
			this.relayoutWithCollapse(false);
		},
		async reInit(){
			if (this.activeRoot != this.layoutTree){
				// Collapse tree to root
				await this.onDetachedAncestorClick(this.layoutTree, true);
			}
			await this.onNonleafClick(this.layoutTree, true);
			await this.initTreeFromServer(false);
		},
		getLytOpts(): LayoutOptions {
			let opts = getDefaultLytOpts();
			for (let prop of Object.getOwnPropertyNames(opts) as (keyof LayoutOptions)[]){
				let item = localStorage.getItem('LYT ' + prop);
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
				let item = localStorage.getItem('UI ' + prop);
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
		// For relayout
		relayoutWithCollapse(secondPass = true): boolean {
			if (this.overflownRoot){
				this.overflownRoot = false;
			}
			let success = tryLayout(this.activeRoot, this.tileAreaDims, this.lytOpts,
				{allowCollapse: true, layoutMap: this.layoutMap});
			if (secondPass){
				// Relayout again, which can help allocate remaining tiles 'evenly'
				success = tryLayout(this.activeRoot, this.tileAreaDims, this.lytOpts,
					{allowCollapse: false, layoutMap: this.layoutMap});
			}
			return success;
		},
		updateAreaDims(){
			// Set mainAreaDims and tileAreaDims
				// Note: Tried setting these by querying tut_pane+ancestry_bar dimensions repeatedly,
				// throughout their transitions, relayouting each time, but this makes the tile movements jerky
			let contentAreaEl = this.$refs.contentArea as HTMLElement;
			let w = contentAreaEl.offsetWidth, h = contentAreaEl.offsetHeight;
			if (this.tutPaneOpen && this.uiOpts.breakpoint == 'sm'){
				h -= this.uiOpts.tutPaneSz;
			}
			this.mainAreaDims = [w, h];
			if (this.detachedAncestors != null){
				if (w > h){
					w -= this.uiOpts.ancestryBarBreadth;
				} else {
					h -= this.uiOpts.ancestryBarBreadth;
				}
			}
			w -= this.lytOpts.tileSpacing * 2;
			h -= this.lytOpts.tileSpacing * 2;
			this.tileAreaDims = [w, h];
		},
		// Other
		resetMode(): void {
			this.infoModalNodeName = null;
			this.searchOpen = false;
			this.settingsOpen = false;
			this.helpOpen = false;
			this.modeRunning = null;
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
		isDisabled(...actions: Action[]): boolean {
			let disabledActions = this.uiOpts.disabledActions;
			return actions.some(a => disabledActions.has(a));
		},
	},
	watch: {
		infoModalNodeName(newVal, oldVal){
			// Possibly trigger tutorial advance
			if (newVal == null){
				this.handleActionForTutorial('tileInfo');
			}
		},
		modeRunning(newVal, oldVal){
			// For sweepToParent setting 'fallback', temporarily change to 'prefer' for efficiency
			if (newVal != null){
				if (this.lytOpts.sweepToParent == 'fallback'){
					this.lytOpts.sweepToParent = 'prefer';
					this.changedSweepToParent = true;
				}
			} else {
				if (this.changedSweepToParent){
					this.lytOpts.sweepToParent = 'fallback';
					this.changedSweepToParent = false;
				}
			}
			// Possibly trigger tutorial advance
			if (newVal == null){
				this.handleActionForTutorial(oldVal);
			}
		},
		settingsOpen(newVal, oldVal){
			// Possibly trigger tutorial advance
			if (newVal == false){
				this.handleActionForTutorial('settings');
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
		IconButton, SearchIcon, PlayIcon, PauseIcon, SettingsIcon, HelpIcon,
		TileInfoModal, SearchModal, SettingsModal, HelpModal, LoadingModal,
	},
});
</script>
