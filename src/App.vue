<script lang="ts">

import {defineComponent, PropType} from 'vue';
// Components
import Tile from './components/Tile.vue';
import AncestryBar from './components/AncestryBar.vue';
import TutorialPane from './components/TutorialPane.vue';
import TileInfoModal from './components/TileInfoModal.vue';
import SearchModal from './components/SearchModal.vue';
import SettingsModal from './components/SettingsModal.vue';
import HelpModal from './components/HelpModal.vue';
// Icons
import SearchIcon from './components/icon/SearchIcon.vue';
import PlayIcon from './components/icon/PlayIcon.vue';
import SettingsIcon from './components/icon/SettingsIcon.vue';
import HelpIcon from './components/icon/HelpIcon.vue';
// Classes and types
	// Note: Import paths lack a .ts or .js extension because .ts makes vue-tsc complain, and .js makes vite complain
import {TolNode} from './lib';
import type {TolMap, Action} from './lib';
import {LayoutNode} from './layout';
import type {LayoutOptions, LayoutTreeChg} from './layout';
// Functions
import {arraySum, randWeightedChoice, getScrollBarWidth, getBreakpoint} from './lib';
import {initLayoutTree, initLayoutMap, tryLayout} from './layout';

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

// Initialise tree-of-life data
const initialTolMap: TolMap = new Map();
initialTolMap.set("", new TolNode());

// Configurable options
function getDefaultLytOpts(): LayoutOptions {
	let screenSz = getBreakpoint();
	return {
		tileSpacing: screenSz == 'sm' ? 6 : 10, //px
		headerSz: 22, //px
		minTileSz: 50, //px
		maxTileSz: 200, //px
		// Layout-algorithm related
		layoutType: 'sweep', //'sqr' | 'rect' | 'sweep'
		rectMode: 'auto first-row', //'horz' | 'vert' | 'linear' | 'auto' | 'auto first-row'
		rectSensitivity: 0.9, //Between 0 and 1
		sweepMode: 'left', //'left' | 'top' | 'shorter' | 'auto'
		sweptNodesPrio: 'sqrt', //'linear' | 'sqrt' | 'pow-2/3'
		sweepToParent: 'prefer', //'none' | 'prefer' | 'fallback'
	};
}
function getDefaultUiOpts(){
	let screenSz = getBreakpoint();
	return {
		// For tiles
		borderRadius: 5, //px
		shadowNormal: '0 0 2px black',
		shadowHighlight: '0 0 1px 2px greenyellow',
		shadowFocused: '0 0 1px 2px orange',
		infoIconSz: 18, //px
		infoIconMargin: 2, //px
		childThresholds: [[1, 'greenyellow'], [10, 'orange'], [100, 'red']],
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
		tileAreaOffset: screenSz == 'sm' ? 6 : 10, //px (space between root tile and display boundary)
		scrollGap: getScrollBarWidth(),
		ancestryBarImgSz: 100, //px
		ancestryBarBgColor: '#44403c',
		ancestryTileMargin: 5, //px (gap between detached-ancestor tiles)
		infoModalImgSz: 200,
		searchSuggLimit: 5,
		autoWaitTime: 500, //ms (time to wait between actions (with their transitions))
		tutorialPaneSz: 200,
		tutorialPaneBgColor: '#1c1917',
		tutorialPaneTextColor: 'white',
		// Timing related
		tileChgDuration: 300, //ms (for tile move/expand/collapse)
		clickHoldDuration: 400, //ms (duration after mousedown when a click-and-hold is recognised)
		// Other
		useReducedTree: false,
		jumpToSearchedNode: false,
		disabledActions: new Set() as Set<Action>,
	};
}

export default defineComponent({
	data(){
		let layoutTree = initLayoutTree(initialTolMap, "", 0);
		layoutTree.hidden = true;
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
			tutorialOpen: true,
			welcomeOpen: true,
			ancestryBarInTransition: false,
			tutTriggerAction: null as Action | null,
			tutTriggerFlag: false,
			tutPaneInTransition: false,
			// For search and auto-mode
			modeRunning: false,
			lastFocused: null as LayoutNode | null,
			// For auto-mode
			autoPrevAction: null as AutoAction | null, // Used to help prevent action cycles
			autoPrevActionFail: false, // Used to avoid re-trying a failed expand/collapse
			// Options
			lytOpts: this.getLytOpts(),
			uiOpts: this.getUiOpts(),
			// For layout and resize-handling
			mainAreaDims: [0, 0] as [number, number],
			tileAreaDims: [0, 0] as [number, number],
			lastResizeHdlrTime: 0, // Used to throttle resize handling
			pendingResizeHdlr: 0, // Set via setTimeout() for a non-initial resize event
			// Other
			justInitialised: false,
			changedSweepToParent: false, // Set during search animation for efficiency
			excessTolNodeThreshold: 1000, // Threshold where excess tolMap entries are removed (done on tile collapse)
		};
	},
	computed: {
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
		tutPaneContainerStyles(): Record<string,string> {
			return {
				minHeight: (this.tutorialOpen ? this.uiOpts.tutorialPaneSz : 0) + 'px',
				maxHeight: (this.tutorialOpen ? this.uiOpts.tutorialPaneSz : 0) + 'px',
				transitionDuration: this.uiOpts.tileChgDuration + 'ms',
				transitionProperty: 'max-height, min-height',
				overflow: 'hidden',
			};
		},
		ancestryBarContainerStyles(): Record<string,string> {
			let ancestryBarBreadth = this.detachedAncestors == null ? 0 :
				this.uiOpts.ancestryBarImgSz + this.uiOpts.ancestryTileMargin*2 + this.uiOpts.scrollGap;
			let styles = {
				minWidth: 'auto',
				maxWidth: 'none',
				minHeight: 'auto',
				maxHeight: 'none',
				transitionDuration: this.uiOpts.tileChgDuration + 'ms',
				transitionProperty: '',
				overflow: 'hidden'
			};
			if (this.mainAreaDims[0] > this.mainAreaDims[1]){
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
		onLeafClick(layoutNode: LayoutNode){
			if (this.uiOpts.disabledActions.has('expand')){
				return Promise.resolve(false);
			}
			this.handleActionForTutorial('expand');
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
				let success = tryLayout(this.activeRoot, [0,0], this.tileAreaDims, this.lytOpts, lytFnOpts);
				// If expanding active-root with too many children to fit, allow overflow
				if (!success && layoutNode == this.activeRoot){
					success = tryLayout(this.activeRoot, [0,0], this.tileAreaDims,
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
		onNonleafClick(layoutNode: LayoutNode, skipClean = false){
			if (this.uiOpts.disabledActions.has('collapse')){
				return false;
			}
			this.handleActionForTutorial('collapse');
			this.setLastFocused(null);
			let success = tryLayout(this.activeRoot, [0,0], this.tileAreaDims, this.lytOpts, {
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
		onLeafClickHeld(layoutNode: LayoutNode){
			if (this.uiOpts.disabledActions.has('expandToView')){
				return;
			}
			this.handleActionForTutorial('expandToView');
			this.setLastFocused(null);
			if (layoutNode == this.activeRoot){
				this.onLeafClick(layoutNode);
				return;
			}
			// Function for expanding tile
			let doExpansion = () => {
				LayoutNode.hideUpward(layoutNode, this.layoutMap);
				this.activeRoot = layoutNode;
				// Repeatedly relayout tiles during ancestry-bar transition
				this.ancestryBarInTransition = true;
				let timerId = setInterval(() => {
					this.updateAreaDims().then(() => this.relayoutWithCollapse());
					if (!this.ancestryBarInTransition){
						clearTimeout(timerId);
					}
				}, 100);
				//
				return this.updateAreaDims().then(() => {
					this.overflownRoot = false;
					let lytFnOpts = {
						allowCollapse: false,
						chg: {type: 'expand', node: layoutNode, tolMap: this.tolMap} as LayoutTreeChg,
						layoutMap: this.layoutMap
					};
					let success = tryLayout(this.activeRoot, [0,0], this.tileAreaDims, this.lytOpts, lytFnOpts);
					if (!success){
						success = tryLayout(this.activeRoot, [0,0], this.tileAreaDims,
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
				});
			};
			// Check if data for node-to-expand exists, getting from server if needed
			let tolNode = this.tolMap.get(layoutNode.name)!;
			if (!this.tolMap.has(tolNode.children[0])){
				let urlPath = '/data/node?name=' + encodeURIComponent(layoutNode.name)
				urlPath += this.uiOpts.useReducedTree ? '&tree=reduced' : '';
				return fetch(urlPath)
					.then(response => response.json())
					.then(obj => {Object.getOwnPropertyNames(obj).forEach(key => {this.tolMap.set(key, obj[key])})})
					.then(doExpansion)
					.catch(error => {
						console.log('ERROR loading tolnode data', error);
					});
			} else {
				return doExpansion();
			}
		},
		onNonleafClickHeld(layoutNode: LayoutNode){
			if (this.uiOpts.disabledActions.has('expandToView')){
				return;
			}
			this.handleActionForTutorial('expandToView');
			this.setLastFocused(null);
			if (layoutNode == this.activeRoot){
				console.log('Ignored expand-to-view on active-root node');
				return;
			}
			LayoutNode.hideUpward(layoutNode, this.layoutMap);
			this.activeRoot = layoutNode;
			// Repeatedly relayout tiles during ancestry-bar transition
			this.ancestryBarInTransition = true;
			let timerId = setInterval(() => {
				this.updateAreaDims().then(() => this.relayoutWithCollapse());
				if (!this.ancestryBarInTransition){
					clearTimeout(timerId);
				}
			}, 100);
			//
			this.updateAreaDims().then(() => this.relayoutWithCollapse());
		},
		onDetachedAncestorClick(layoutNode: LayoutNode, alsoCollapse = false){
			if (this.uiOpts.disabledActions.has('unhideAncestor')){
				return Promise.resolve(false);
			}
			this.handleActionForTutorial('unhideAncestor');
			this.setLastFocused(null);
			this.activeRoot = layoutNode;
			this.overflownRoot = false;
			// Repeatedly relayout tiles during ancestry-bar transition
			this.ancestryBarInTransition = true;
			let timerId = setInterval(() => {
				this.updateAreaDims().then(() => this.relayoutWithCollapse());
				if (!this.ancestryBarInTransition){
					clearTimeout(timerId);
				}
			}, 100);
			//
			if (alsoCollapse){
				this.onNonleafClick(layoutNode, true);
			}
			return this.updateAreaDims().then(() => {
				this.relayoutWithCollapse();
				LayoutNode.showDownward(layoutNode);
			});
		},
		// For tile-info events
		onInfoClick(nodeName: string){
			this.handleActionForTutorial('tileInfo');
			if (!this.searchOpen){
				this.resetMode();
			}
			this.infoModalNodeName = nodeName;
		},
		// For search events
		onSearchIconClick(){
			this.handleActionForTutorial('search');
			this.resetMode();
			this.searchOpen = true;
		},
		onSearch(name: string){
			if (this.modeRunning){
				console.log("WARNING: Unexpected search event while search/auto mode is running")
				return;
			}
			this.searchOpen = false;
			this.modeRunning = true;
			if (this.lytOpts.sweepToParent == 'fallback'){
				this.lytOpts.sweepToParent = 'prefer';
				this.changedSweepToParent = true;
			}
			this.expandToNode(name);
		},
		expandToNode(name: string){
			if (!this.modeRunning){
				return;
			}
			// Check if searched node is displayed
			let targetNode = this.layoutMap.get(name);
			if (targetNode != null && !targetNode.hidden){
				this.setLastFocused(targetNode);
				this.modeRunning = false;
				if (this.changedSweepToParent){
					this.lytOpts.sweepToParent = 'fallback';
					this.changedSweepToParent = false;
				}
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
				if (!this.uiOpts.jumpToSearchedNode){
					this.onDetachedAncestorClick(nodeInAncestryBar!);
					setTimeout(() => this.expandToNode(name), this.uiOpts.tileChgDuration);
				} else{
					this.onDetachedAncestorClick(nodeInAncestryBar, true)
						.then(() => this.expandToNode(name));
				}
				return;
			}
			// Attempt tile-expand
			if (this.uiOpts.jumpToSearchedNode){
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
				this.onLeafClickHeld(targetNode!.parent!);
				//
				setTimeout(() => {this.setLastFocused(targetNode!);}, this.uiOpts.tileChgDuration);
				this.modeRunning = false;
				return;
			}
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
				this.onNonleafClickHeld(layoutNode);
				setTimeout(() => this.expandToNode(name), this.uiOpts.tileChgDuration);
			});
		},
		// For auto-mode events
		onPlayIconClick(){
			this.handleActionForTutorial('autoMode');
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
				let action: AutoAction | null;
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
						'collapse': 1, 'expandToView': 1, 'unhideAncestor': 1
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
						actionWeights['expandToView'] = 0; // Only expand-to-view if direct child of activeRoot
					}
					if (this.activeRoot.parent == null || node != this.activeRoot){
						actionWeights['unhideAncestor'] = 0; // Only expand ancestry-bar if able and activeRoot
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
					action = actionList[randWeightedChoice(weightList)!] as AutoAction;
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
					case 'expandToView':
						this.onNonleafClickHeld(node);
						break;
					case 'unhideAncestor':
						this.onDetachedAncestorClick(node.parent!);
						break;
				}
				setTimeout(this.autoAction, this.uiOpts.tileChgDuration + this.uiOpts.autoWaitTime);
				this.autoPrevAction = action;
			}
		},
		// For settings events
		onSettingsIconClick(){
			this.handleActionForTutorial('settings');
			this.resetMode();
			this.settingsOpen = true;
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
		onSettingsChg(changedLytOpts: Iterable<string>, changedUiOpts: Iterable<string>){
			let changed = false;
			for (let opt of changedLytOpts){
				localStorage.setItem('lyt ' + opt, String(this.lytOpts[opt as keyof LayoutOptions]));
				changed = true;
			}
			for (let opt of changedUiOpts){
				localStorage.setItem('ui ' + opt, String(this.uiOpts[opt]));
				changed = true;
			}
			if (changed){
				console.log('Settings saved');
			}
		},
		onResetSettings(){
			localStorage.clear();
			let defaultLytOpts = getDefaultLytOpts();
			let defaultUiOpts = getDefaultUiOpts();
			if (this.uiOpts.useReducedTree != defaultUiOpts.useReducedTree){
				this.onTreeChange();
			}
			Object.assign(this.lytOpts, defaultLytOpts);
			Object.assign(this.uiOpts, defaultUiOpts);
			console.log('Settings reset');
			this.relayoutWithCollapse();
		},
		// For help events
		onHelpIconClick(){
			this.handleActionForTutorial('help');
			this.resetMode();
			this.helpOpen = true;
		},
		// For tutorial events
		onStartTutorial(){
			if (this.tutorialOpen == false){
				this.tutorialOpen = true;
				// Repeatedly relayout tiles during tutorial-pane transition
				this.tutPaneInTransition = true;
				let timerId = setInterval(() => {
					this.updateAreaDims().then(() => this.relayoutWithCollapse());
					if (!this.tutPaneInTransition){
						clearTimeout(timerId);
					}
				}, 100);
			}
		},
		onTutorialClose(){
			this.tutorialOpen = false;
			this.welcomeOpen = false;
			this.uiOpts.disabledActions.clear();
			// Repeatedly relayout tiles during tutorial-pane transition
			this.tutPaneInTransition = true;
			let timerId = setInterval(() => {
				this.updateAreaDims().then(() => this.relayoutWithCollapse());
				if (!this.tutPaneInTransition){
					clearTimeout(timerId);
				}
			}, 100);
		},
		onTutStageChg(triggerAction: Action | null){
			this.welcomeOpen = false;
			this.tutTriggerAction = triggerAction;
		},
		handleActionForTutorial(action: Action){
			if (!this.tutorialOpen){
				return;
			}
			// Close welcome message on first action
			if (this.welcomeOpen){
				this.onTutorialClose();
			}
			// Tell TutorialPane if trigger-action was done
			if (this.tutTriggerAction == action){
				this.tutTriggerFlag = !this.tutTriggerFlag;
			}
		},
		// For other events
		onResize(){
			// Handle event, delaying/ignoring if this was recently done
			if (this.pendingResizeHdlr == 0){
				const resizeDelay = 100;
				let handleResize = () => {
					// Update unmodified layout/ui options with defaults
					let lytOpts = getDefaultLytOpts();
					let uiOpts = getDefaultUiOpts();
					let changedTree = false;
					for (let prop of Object.getOwnPropertyNames(lytOpts)){
						let item = localStorage.getItem('lyt ' + prop);
						if (item == null && this.lytOpts[prop] != lytOpts[prop as keyof LayoutOptions]){
							this.lytOpts[prop] = lytOpts[prop as keyof LayoutOptions];
						}
					}
					for (let prop of Object.getOwnPropertyNames(uiOpts)){
						let item = localStorage.getItem('lyt ' + prop);
						if (item == null && this.uiOpts[prop] != uiOpts[prop as keyof typeof uiOpts]){
							this.uiOpts[prop] = uiOpts[prop as keyof typeof uiOpts];
							if (prop == 'useReducedTree'){
								changedTree = true;
							}
						}
					}
					//
					this.overflownRoot = false;
					if (!changedTree){
						return this.updateAreaDims().then(() => this.relayoutWithCollapse());
					} else {
						return Promise.resolve(this.onTreeChange());
					}
				};
				let currentTime = new Date().getTime();
				if (currentTime - this.lastResizeHdlrTime > resizeDelay){
					this.lastResizeHdlrTime = currentTime;
					handleResize().then(() => {
						this.lastResizeHdlrTime = new Date().getTime();
					});
				} else {
					let remainingDelay = resizeDelay - (currentTime - this.lastResizeHdlrTime);
					this.pendingResizeHdlr = setTimeout(() => {
						this.pendingResizeHdlr = 0;
						handleResize().then(() => {
							this.lastResizeHdlrTime = new Date().getTime();
						});
					}, remainingDelay);
				}
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
			let urlPath = '/data/node';
			urlPath += this.uiOpts.useReducedTree ? '?tree=reduced' : '';
			fetch(urlPath)
				.then(response => response.json())
				.then(obj => {
					// Get root node name
					let rootName = null;
					let nodeNames = Object.getOwnPropertyNames(obj);
					for (let n of nodeNames){
						if (obj[n].parent == null){
							rootName = n;
							break;
						}
					}
					if (rootName == null){
						throw new Error('Server response has no root node');
					}
					// Initialise tree
					this.tolMap.clear();
					nodeNames.forEach(n => {this.tolMap.set(n, obj[n])});
					this.layoutTree = initLayoutTree(this.tolMap, rootName, 0);
					this.activeRoot = this.layoutTree;
					this.layoutMap = initLayoutMap(this.layoutTree);
					this.updateAreaDims().then(() => {
						this.relayoutWithCollapse(false);
						this.justInitialised = true;
						setTimeout(() => {this.justInitialised = false;}, 300);
					});
				})
				.catch(error => {
					console.log('ERROR loading initial tolnode data', error);
				});
		},
		getLytOpts(){
			let opts: {[x: string]: boolean|number|string} = getDefaultLytOpts();
			for (let prop of Object.getOwnPropertyNames(opts)){
				let item = localStorage.getItem('lyt ' + prop);
				if (item != null){
					switch (typeof(opts[prop])){
						case 'boolean': opts[prop] = Boolean(item); break;
						case 'number': opts[prop] = Number(item); break;
						case 'string': opts[prop] = item; break;
						default: console.log(`WARNING: Found saved layout setting "${prop}" with unexpected type`);
					}
				}
			}
			return opts;
		},
		getUiOpts(){
			let opts: {[x: string]: boolean|number|string|string[]|(string|number)[][]|Set<Action>} = getDefaultUiOpts();
			for (let prop of Object.getOwnPropertyNames(opts)){
				let item = localStorage.getItem('ui ' + prop);
				if (item != null){
					switch (typeof(opts[prop])){
						case 'boolean': opts[prop] = item == 'true'; break;
						case 'number': opts[prop] = Number(item); break;
						case 'string': opts[prop] = item; break;
						default: console.log(`WARNING: Found saved UI setting "${prop}" with unexpected type`);
					}
				}
			}
			return opts;
		},
		resetMode(){
			this.infoModalNodeName = null;
			this.searchOpen = false;
			this.helpOpen = false;
			this.settingsOpen = false;
			this.modeRunning = false;
			this.setLastFocused(null);
			if (this.changedSweepToParent){
				this.lytOpts.sweepToParent = 'fallback';
				this.changedSweepToParent = false;
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
		relayoutWithCollapse(secondPass = true){
			if (this.overflownRoot){
				tryLayout(this.activeRoot, [0,0], this.tileAreaDims,
					{...this.lytOpts, layoutType: 'flex-sqr'}, {allowCollapse: false, layoutMap: this.layoutMap});
				return;
			}
			tryLayout(this.activeRoot, [0,0], this.tileAreaDims, this.lytOpts,
				{allowCollapse: true, layoutMap: this.layoutMap});
			if (secondPass){
				// Relayout again to allocate remaining tiles 'evenly'
				tryLayout(this.activeRoot, [0,0], this.tileAreaDims, this.lytOpts,
					{allowCollapse: false, layoutMap: this.layoutMap});
			}
		},
		updateAreaDims(){
			let mainAreaEl = this.$refs.mainArea as HTMLElement;
			this.mainAreaDims = [mainAreaEl.offsetWidth, mainAreaEl.offsetHeight];
			// Need to wait until ancestor-bar is laid-out before computing tileAreaDims
			return this.$nextTick(() => {
				let tileAreaEl = this.$refs.tileArea as HTMLElement;
				this.tileAreaDims = [tileAreaEl.offsetWidth, tileAreaEl.offsetHeight];
			});
		},
		ancestryBarTransitionEnd(){
			this.ancestryBarInTransition = false;
		},
		tutPaneTransitionEnd(){
			this.tutPaneInTransition = false;
		},
	},
	created(){
		window.addEventListener('resize', this.onResize);
		window.addEventListener('keyup', this.onKeyUp);
		this.initTreeFromServer();
	},
	unmounted(){
		window.removeEventListener('resize', this.onResize);
		window.removeEventListener('keyup', this.onKeyUp);
	},
	components: {
		Tile, AncestryBar,
		HelpIcon, SettingsIcon, SearchIcon, PlayIcon,
		TileInfoModal, HelpModal, SearchModal, SettingsModal, TutorialPane,
	},
});
</script>

<template>
<div class="absolute left-0 top-0 w-screen h-screen overflow-hidden flex flex-col"
	:style="{backgroundColor: uiOpts.appBgColor}">
	<div class="flex bg-black shadow">
		<h1 class="text-lime-500 px-4 my-auto text-2xl">Tree of Life</h1>
		<!-- Icons -->
		<div v-if="!uiOpts.disabledActions.has('search')"
			class="ml-auto mr-2 my-2 w-9 aspect-square p-2 rounded-full bg-lime-600 text-lime-100
				hover:brightness-125 active:brightness-125 hover:cursor-pointer" @click="onSearchIconClick">
			<search-icon/>
		</div>
		<div v-if="!uiOpts.disabledActions.has('autoMode')"
			class="mr-2 my-2 w-9 aspect-square p-2 rounded-full bg-lime-600 text-lime-100
				hover:brightness-125 active:brightness-125 hover:cursor-pointer" @click="onPlayIconClick">
			<play-icon/>
		</div>
		<div v-if="!uiOpts.disabledActions.has('settings')"
			class="mr-2 my-2 w-9 aspect-square p-2 rounded-full bg-lime-600 text-lime-100
				hover:brightness-125 active:brightness-125 hover:cursor-pointer" @click="onSettingsIconClick">
			<settings-icon/>
		</div>
		<div v-if="!uiOpts.disabledActions.has('help')"
			class="mr-2 my-2 w-9 aspect-square p-2 rounded-full bg-lime-600 text-lime-100
				hover:brightness-125 active:brightness-125 hover:cursor-pointer" @click="onHelpIconClick">
			<help-icon/>
		</div>
	</div>
	<div :style="tutPaneContainerStyles"> <!-- Used to slide-in/out the tutorial pane -->
		<transition name="fade" @after-enter="tutPaneTransitionEnd" @after-leave="tutPaneTransitionEnd">
			<tutorial-pane v-if="tutorialOpen" :height="uiOpts.tutorialPaneSz + 'px'"
				:uiOpts="uiOpts" :triggerFlag="tutTriggerFlag" :skipWelcome="!welcomeOpen"
				@close="onTutorialClose" @stage-chg="onTutStageChg"/>
		</transition>
	</div>
	<div :class="['flex', mainAreaDims[0] > mainAreaDims[1] ? 'flex-row' : 'flex-col', 'grow', 'min-h-0']" ref="mainArea">
		<div :style="ancestryBarContainerStyles">
			<transition name="fade" @after-enter="ancestryBarTransitionEnd" @after-leave="ancestryBarTransitionEnd">
				<ancestry-bar v-if="detachedAncestors != null" class="w-full h-full"
					:nodes="detachedAncestors" :vert="mainAreaDims[0] > mainAreaDims[1]"
					:tolMap="tolMap" :lytOpts="lytOpts" :uiOpts="uiOpts"
					@ancestor-click="onDetachedAncestorClick" @info-click="onInfoClick"/>
			</transition>
		</div>
		<div class="relative grow" :style="{margin: uiOpts.tileAreaOffset + 'px'}" ref="tileArea">
			<tile :layoutNode="layoutTree" :tolMap="tolMap" :lytOpts="lytOpts" :uiOpts="uiOpts"
				:overflownDim="overflownRoot ? tileAreaDims[1] : 0" :skipTransition="justInitialised"
				@leaf-click="onLeafClick" @nonleaf-click="onNonleafClick"
				@leaf-click-held="onLeafClickHeld" @nonleaf-click-held="onNonleafClickHeld"
				@info-click="onInfoClick"/>
		</div>
	</div>
	<!-- Modals -->
	<transition name="fade">
		<search-modal v-if="searchOpen" :tolMap="tolMap" :uiOpts="uiOpts" ref="searchModal"
			@close="searchOpen = false" @search="onSearch" @info-click="onInfoClick" @settings-chg="onSettingsChg" />
	</transition>
	<transition name="fade">
		<tile-info-modal v-if="infoModalNodeName != null"
			:nodeName="infoModalNodeName" :tolMap="tolMap" :lytOpts="lytOpts" :uiOpts="uiOpts"
			@close="infoModalNodeName = null"/>
	</transition>
	<transition name="fade">
		<help-modal v-if="helpOpen" :uiOpts="uiOpts"
			@close="helpOpen = false" @start-tutorial="onStartTutorial"/>
	</transition>
	<settings-modal v-if="settingsOpen" :lytOpts="lytOpts" :uiOpts="uiOpts" class="z-10"
		@close="settingsOpen = false" @settings-chg="onSettingsChg" @reset="onResetSettings"
		@layout-setting-chg="relayoutWithCollapse" @tree-chg="onTreeChange"/>
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
</style>
