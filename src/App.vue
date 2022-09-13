<template>
<div class="absolute left-0 top-0 w-screen h-screen overflow-hidden flex flex-col"
	:style="{backgroundColor: uiOpts.bgColor, scrollbarColor: uiOpts.altColorDark + ' ' + uiOpts.bgColorDark}">
	<!-- Title bar -->
	<div class="flex shadow gap-2 p-2" :style="{backgroundColor: uiOpts.bgColorDark2, color: uiOpts.altColor}">
		<h1 class="my-auto ml-2 text-4xl hover:cursor-pointer" @click="collapseTree" title="Reset tree">Tilo</h1>
		<div class="mx-auto"/> <!-- Spacer -->
		<!-- Icons -->
		<icon-button :disabled="isDisabled('help')" :size="45" :style="buttonStyles"
			@click="onHelpIconClick" title="Show help info">
			<help-icon/>
		</icon-button>
		<icon-button :disabled="isDisabled('settings')" :size="45" :style="buttonStyles"
			@click="onSettingsIconClick" title="Show settings">
			<settings-icon/>
		</icon-button>
		<icon-button :disabled="isDisabled('autoMode')" :size="45" :style="buttonStyles"
			@click="onAutoIconClick" title="Auto mode">
			<play-icon v-if="modeRunning != 'autoMode'"/>
			<pause-icon v-else/>
		</icon-button>
		<icon-button :disabled="isDisabled('search')" :size="45" :style="buttonStyles"
			@click="onSearchIconClick" title="Search">
			<search-icon/>
		</icon-button>
	</div>
	<!-- Content area -->
	<div class="grow min-h-0 flex flex-col relative" ref="contentAreaRef">
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
				<tol-tile :layoutNode="layoutTree" :tolMap="tolMap" :lytOpts="lytOpts" :uiOpts="uiOpts"
					:overflownDim="overflownRoot ? tileAreaDims[1] : 0" :skipTransition="justInitialised"
					@leaf-click="onLeafClick" @nonleaf-click="onNonleafClick"
					@leaf-click-held="onLeafClickHeld" @nonleaf-click-held="onNonleafClickHeld"
					@info-click="onInfoClick"/>
			</div>
		</div>
		<transition name="fade">
			<icon-button v-if="!tutPaneOpen && !uiOpts.tutorialSkip" @click="onStartTutorial" title="Start Tutorial"
				:size="45" :style="buttonStyles" class="absolute bottom-2 right-2 z-10 shadow-[0_0_2px_black]">
				<edu-icon/>
			</icon-button>
		</transition>
	</div>
	<!-- Modals -->
	<transition name="fade">
		<search-modal v-if="searchOpen"
			:tolMap="tolMap" :lytMap="layoutMap" :activeRoot="activeRoot" :lytOpts="lytOpts" :uiOpts="uiOpts"
			@close="onSearchClose" @search="onSearch" @info-click="onInfoClick" @setting-chg="onSettingChg"
			@net-wait="onSearchNetWait" @net-get="endLoadInd" class="z-10"/>
	</transition>
	<transition name="fade">
		<tile-info-modal v-if="infoModalNodeName != null && infoModalData != null"
			:nodeName="infoModalNodeName" :infoResponse="infoModalData" :tolMap="tolMap" :lytOpts="lytOpts"
			:uiOpts="uiOpts" class="z-10" @close="onInfoClose"/>
	</transition>
	<transition name="fade">
		<help-modal v-if="helpOpen" :tutOpen="tutPaneOpen" :uiOpts="uiOpts" class="z-10"
			@close="onHelpClose" @start-tutorial="onStartTutorial"/>
	</transition>
	<transition name="fade">
		<settings-modal v-if="settingsOpen" :lytOpts="lytOpts" :uiOpts="uiOpts" class="z-10"
			@close="onSettingsClose" @reset="onResetSettings" @setting-chg="onSettingChg"/>
	</transition>
	<transition name="fade">
		<loading-modal v-if="loadingMsg != null" :msg="loadingMsg" :uiOpts="uiOpts" class="z-10"/>
	</transition>
	<!-- Overlay used to capture clicks during auto mode, etc -->
	<div :style="{visibility: modeRunning != null ? 'visible' : 'hidden'}"
		class="absolute left-0 top-0 w-full h-full z-20" @click="resetMode"></div>
</div>
</template>

<script setup lang="ts">
import {ref, computed, watch, onMounted, onUnmounted, nextTick} from 'vue';
// Components
import TolTile from './components/TolTile.vue';
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
import EduIcon from './components/icon/EduIcon.vue';
// Other
	// Note: Import paths lack a .ts or .js because .ts makes vue-tsc complain, and .js makes vite complain
import {TolNode, TolMap} from './tol';
import {LayoutNode, LayoutOptions, LayoutTreeChg,
	initLayoutTree, initLayoutMap, tryLayout} from './layout';
import {queryServer, InfoResponse, Action,
	UiOptions, getDefaultLytOpts, getDefaultUiOpts, OptionType} from './lib';
import {arraySum, randWeightedChoice} from './util';

// Constants
const SERVER_WAIT_MSG = 'Loading data';
const PROCESSING_WAIT_MSG = 'Processing';
const EXCESS_TOLNODE_THRESHOLD = 1000; // Threshold where excess tolMap entries get removed

// Refs
const contentAreaRef = ref(null as HTMLElement | null);

// Get/load option values
function getLytOpts(): LayoutOptions {
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
}
function getUiOpts(): UiOptions {
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
}
const lytOpts = ref(getLytOpts());
const uiOpts = ref(getUiOpts());

// Tree/layout data
const tolMap = ref(new Map() as TolMap);
tolMap.value.set('', new TolNode())
const layoutTree = ref(initLayoutTree(tolMap.value, "", 0));
layoutTree.value.hidden = true;
const activeRoot = ref(layoutTree.value); // Root of the displayed subtree
const layoutMap = ref(initLayoutMap(layoutTree.value)); // Maps names to LayoutNodes
// Nodes to show in ancestry-bar (ordered from root downwards)
const detachedAncestors = computed((): LayoutNode[] | null => {
	if (activeRoot.value == layoutTree.value){
		return null;
	}
	let ancestors = [];
	let node = activeRoot.value.parent;
	while (node != null){
		ancestors.push(node);
		node = node.parent;
	}
	return ancestors.reverse();
});

// For initialisation
const justInitialised = ref(false); // Used to skip transition for the tile initially loaded from server
async function initTreeFromServer(firstInit = true){
	// Get possible target node from URL
	let nodeName = (new URL(window.location.href)).searchParams.get('node');
	// Query server
	let urlParams = new URLSearchParams({type: 'node', tree: uiOpts.value.tree});
	if (nodeName != null && firstInit){
		urlParams.append('name', nodeName);
		urlParams.append('toroot', '1');
	}
	let responseObj: {[x: string]: TolNode} = await loadFromServer(urlParams);
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
	tolMap.value.clear();
	nodeNames.forEach(n => {tolMap.value.set(n, responseObj[n])});
	if (nodeName == null){
		layoutTree.value = initLayoutTree(tolMap.value, rootName, 0);
		layoutMap.value = initLayoutMap(layoutTree.value);
		activeRoot.value = layoutTree.value;
	} else {
		layoutTree.value = initLayoutTree(tolMap.value, rootName, -1);
		layoutMap.value = initLayoutMap(layoutTree.value);
		// Set active root
		let targetNode = layoutMap.value.get(nodeName)!;
		let newRoot = targetNode.parent == null ? targetNode : targetNode.parent;
		LayoutNode.hideUpward(newRoot, layoutMap.value);
		activeRoot.value = newRoot;
		setTimeout(() => setLastFocused(targetNode!), uiOpts.value.transitionDuration);
	}
	// Skip initial transition
	if (firstInit){
		justInitialised.value = true;
		setTimeout(() => {justInitialised.value = false}, uiOpts.value.transitionDuration);
	}
	// Relayout
	updateAreaDims();
	relayoutWithCollapse(false);
}
async function reInit(){
	if (activeRoot.value != layoutTree.value){
		// Collapse tree to root
		await onDetachedAncestorClick(layoutTree.value, true);
	}
	await onNonleafClick(layoutTree.value, null, true);
	await initTreeFromServer(false);
}
onMounted(() => initTreeFromServer());

// For layouting
const mainAreaDims = ref([0, 0] as [number, number]);
const tileAreaDims = ref([0, 0] as [number, number]);
const wideMainArea = computed(() => mainAreaDims.value[0] > mainAreaDims.value[1]);
const overflownRoot = ref(false); // Set when displaying a root tile with many children, with overflow
function relayoutWithCollapse(secondPass = true, keepOverflow = false): boolean {
	let success: boolean;
	if (overflownRoot.value){
		if (keepOverflow){
			success = tryLayout(activeRoot.value, tileAreaDims.value,
				{...lytOpts.value, layoutType: 'sqr-overflow'}, {layoutMap: layoutMap.value});
			return success;
		}
		overflownRoot.value = false;
	}
	success = tryLayout(activeRoot.value, tileAreaDims.value, lytOpts.value,
		{allowCollapse: true, layoutMap: layoutMap.value});
	if (secondPass){
		// Relayout again, which can help allocate remaining tiles 'evenly'
		success = tryLayout(activeRoot.value, tileAreaDims.value, lytOpts.value,
			{allowCollapse: false, layoutMap: layoutMap.value});
	}
	return success;
}
function updateAreaDims(){
	// Set mainAreaDims and tileAreaDims
		// Note: Tried setting these by querying tut_pane+ancestry_bar dimensions repeatedly,
		// throughout their transitions, relayouting each time, but this makes the tile movements jerky
	let contentAreaEl = contentAreaRef.value!;
	let w = contentAreaEl.offsetWidth, h = contentAreaEl.offsetHeight;
	if (tutPaneOpen.value && uiOpts.value.breakpoint == 'sm'){
		h -= uiOpts.value.tutPaneSz;
	}
	mainAreaDims.value = [w, h];
	if (detachedAncestors.value != null){
		if (w > h){
			w -= uiOpts.value.ancestryBarBreadth;
		} else {
			h -= uiOpts.value.ancestryBarBreadth;
		}
	}
	w -= lytOpts.value.tileSpacing * 2;
	h -= lytOpts.value.tileSpacing * 2;
	tileAreaDims.value = [w, h];
}

// For resize handling
let lastResizeHdlrTime = 0; // Used to throttle resize handling
let afterResizeHdlr = 0; // Set via setTimeout() to execute after a run of resize events
async function onResize(){
	// Handle event if not recently done
	let handleResize = async () => {
		// Update layout/ui options with defaults, excluding user-modified ones
		let lytOpts2 = getDefaultLytOpts();
		let uiOpts2 = getDefaultUiOpts(lytOpts2);
		let changedTree = false;
		for (let prop of Object.getOwnPropertyNames(lytOpts2) as (keyof LayoutOptions)[]){
			let item = localStorage.getItem('LYT ' + prop);
			if (item == null && lytOpts.value[prop] != lytOpts2[prop]){
				(lytOpts.value[prop] as any) = lytOpts2[prop];
			}
		}
		for (let prop of Object.getOwnPropertyNames(uiOpts2) as (keyof UiOptions)[]){
			let item = localStorage.getItem('UI ' + prop);
			//Note: Using JSON.stringify here to roughly deep-compare values
			if (item == null && JSON.stringify(uiOpts.value[prop]) != JSON.stringify(uiOpts2[prop])){
				(uiOpts.value[prop] as any) = uiOpts2[prop];
				if (prop == 'tree'){
					changedTree = true;
				}
			}
		}
		// Relayout
		if (!changedTree){
			updateAreaDims();
			relayoutWithCollapse();
		} else {
			reInit();
		}
	};
	let currentTime = new Date().getTime();
	if (currentTime - lastResizeHdlrTime > uiOpts.value.transitionDuration){
		lastResizeHdlrTime = currentTime;
		await handleResize();
		lastResizeHdlrTime = new Date().getTime();
	}
	// Also setup a handler to execute after a run of resize events
	clearTimeout(afterResizeHdlr);
	afterResizeHdlr = setTimeout(async () => {
		afterResizeHdlr = 0;
		await handleResize();
		lastResizeHdlrTime = new Date().getTime();
	}, 200); // If too small, touch-device detection when swapping to/from mobile-mode gets unreliable
}
onMounted(() => window.addEventListener('resize', onResize));
onUnmounted(() => window.removeEventListener('resize', onResize));

// For tile expand/collapse events
async function onLeafClick(
	layoutNode: LayoutNode, onFail: null | (() => void) = null, subAction = false): Promise<boolean> {
	if (!subAction && !onActionStart('expand')){
		return false;
	}
	// Function for expanding tile
	let doExpansion = async () => {
		primeLoadInd(PROCESSING_WAIT_MSG);
		let lytFnOpts = {
			allowCollapse: false,
			chg: {type: 'expand', node: layoutNode, tolMap: tolMap.value} as LayoutTreeChg,
			layoutMap: layoutMap.value,
		};
		let success = tryLayout(activeRoot.value, tileAreaDims.value, lytOpts.value, lytFnOpts);
		// Handle auto-hide
		if (!success && uiOpts.value.autoHide){
			while (!success && layoutNode != activeRoot.value){
				let node = layoutNode;
				while (node.parent != activeRoot.value){
					node = node.parent!;
				}
				// Hide ancestor
					// Note: Not using onNonleafClickHeld() here to avoid a relayoutWithCollapse()
				LayoutNode.hideUpward(node, layoutMap.value);
				activeRoot.value = node;
				// Try relayout
				updateAreaDims();
				success = tryLayout(activeRoot.value, tileAreaDims.value, lytOpts.value, lytFnOpts);
			}
		}
		// If expanding active-root with too many children to fit, allow overflow
		if (!success && layoutNode == activeRoot.value){
			success = tryLayout(activeRoot.value, tileAreaDims.value,
				{...lytOpts.value, layoutType: 'sqr-overflow'}, lytFnOpts);
			if (success){
				overflownRoot.value = true;
			}
		}
		//
		if (!subAction && !success && onFail != null){
			onFail(); // Triggers failure animation
		}
		nextTick(endLoadInd);
		return success;
	};
	//
	let success: boolean;
	if (overflownRoot.value){ // If clicking child of overflowing active-root
		if (!uiOpts.value.autoHide){
			if (!subAction && onFail != null){
				onFail(); // Triggers failure animation
			}
			success = false;
		} else {
			success = await onLeafClickHeld(layoutNode);
		}
	} else {
		// Check if data for node-to-expand exists, getting from server if needed
		let tolNode = tolMap.value.get(layoutNode.name)!;
		if (!tolMap.value.has(tolNode.children[0])){
			let urlParams = new URLSearchParams({type: 'node', name: layoutNode.name, tree: uiOpts.value.tree});
			let responseObj: {[x: string]: TolNode} = await loadFromServer(urlParams);
			if (responseObj == null){
				success = false;
			} else {
				Object.getOwnPropertyNames(responseObj).forEach(n => {tolMap.value.set(n, responseObj[n])});
				success = await doExpansion();
			}
		} else {
			success = await doExpansion();
		}
	}
	if (!subAction){
		onActionEnd('expand');
	}
	return success;
}
async function onNonleafClick(
	layoutNode: LayoutNode, onFail: null | (() => void) = null, subAction = false): Promise<boolean> {
	if (!subAction && !onActionStart('collapse')){
		return false;
	}
	// Relayout
	primeLoadInd(PROCESSING_WAIT_MSG);
	let success = tryLayout(activeRoot.value, tileAreaDims.value, lytOpts.value, {
		allowCollapse: false,
		chg: {type: 'collapse', node: layoutNode, tolMap: tolMap.value},
		layoutMap: layoutMap.value,
	});
	// Update overflownRoot if root was collapsed
	if (success && overflownRoot.value){
		overflownRoot.value = false;
	}
	if (!subAction){
		if (!success){
			if (onFail != null){
				onFail(); // Triggers failure animation
			}
		} else {
			// Possibly clear out excess nodes when a threshold is reached
			let numNodes = tolMap.value.size;
			let extraNodes = numNodes - layoutMap.value.size;
			if (extraNodes > EXCESS_TOLNODE_THRESHOLD){
				for (let n of tolMap.value.keys()){
					if (!layoutMap.value.has(n)){
						tolMap.value.delete(n)
					}
				}
				console.log(`Cleaned up tolMap (removed ${numNodes - tolMap.value.size} out of ${numNodes})`);
			}
		}
	}
	if (!subAction){
		onActionEnd('collapse');
	}
	nextTick(endLoadInd);
	return success;
}
// For expand-to-view and ancestry-bar events
async function onLeafClickHeld(
	layoutNode: LayoutNode, onFail: null | (() => void) = null, subAction = false): Promise<boolean> {
	// Special case for active root
	if (layoutNode == activeRoot.value){
		console.log('Ignored expand-to-view on active-root node');
		return false;
	}
	//
	if (!subAction && !onActionStart('expandToView')){
		return false;
	}
	// Function for expanding tile
	let doExpansion = async () => {
		primeLoadInd(PROCESSING_WAIT_MSG);
		// Hide ancestors
		LayoutNode.hideUpward(layoutNode, layoutMap.value);
		activeRoot.value = layoutNode;
		// Relayout
		updateAreaDims();
		overflownRoot.value = false;
		let lytFnOpts = {
			allowCollapse: false,
			chg: {type: 'expand', node: layoutNode, tolMap: tolMap.value} as LayoutTreeChg,
			layoutMap: layoutMap.value,
		};
		let success = tryLayout(activeRoot.value, tileAreaDims.value, lytOpts.value, lytFnOpts);
		// If expanding active-root with too many children to fit, allow overflow
		if (!success){
			success = tryLayout(activeRoot.value, tileAreaDims.value,
				{...lytOpts.value, layoutType: 'sqr-overflow'}, lytFnOpts);
			if (success){
				overflownRoot.value = true;
			}
		}
		//
		if (!success && !subAction && onFail != null){
			onFail(); // Triggers failure animation
		}
		nextTick(endLoadInd);
		return success;
	};
	// Check if data for node-to-expand exists, getting from server if needed
	let success: boolean;
	let tolNode = tolMap.value.get(layoutNode.name)!;
	if (!tolMap.value.has(tolNode.children[0])){
		let urlParams = new URLSearchParams({type: 'node', name: layoutNode.name, tree: uiOpts.value.tree});
		let responseObj: {[x: string]: TolNode} = await loadFromServer(urlParams);
		if (responseObj == null){
			success = false;
		} else {
			Object.getOwnPropertyNames(responseObj).forEach(n => {tolMap.value.set(n, responseObj[n])});
			success = await doExpansion();
		}
	} else {
		success = await doExpansion();
	}
	if (!subAction){
		onActionEnd('expandToView');
	}
	return success;
}
async function onNonleafClickHeld(
	layoutNode: LayoutNode, onFail: null | (() => void) = null, subAction = false): Promise<boolean> {
	// Special case for active root
	if (layoutNode == activeRoot.value){
		console.log('Ignored expand-to-view on active-root node');
		return false;
	}
	//
	if (!subAction && !onActionStart('expandToView')){
		return false;
	}
	primeLoadInd(PROCESSING_WAIT_MSG);
	// Hide ancestors
	LayoutNode.hideUpward(layoutNode, layoutMap.value);
	activeRoot.value = layoutNode;
	// Relayout
	updateAreaDims();
	let success = relayoutWithCollapse();
	//
	if (!subAction){
		onActionEnd('expandToView');
	}
	nextTick(endLoadInd);
	return success;
}
async function onDetachedAncestorClick(layoutNode: LayoutNode, subAction = false, collapse = false): Promise<boolean> {
	if (!subAction && !onActionStart('unhideAncestor')){
		return false;
	}
	primeLoadInd(PROCESSING_WAIT_MSG);
	// Unhide ancestors
	activeRoot.value = layoutNode;
	overflownRoot.value = false;
	//
	let success: boolean;
	updateAreaDims();
	if (!collapse){
		// Relayout, attempting to have the ancestor expanded
		relayoutWithCollapse(false);
		if (layoutNode.children.length > 0){
			success = relayoutWithCollapse(false); // Second pass for regularity
		} else {
			success = await onLeafClick(layoutNode, null, true);
		}
	} else {
		success = await onNonleafClick(layoutNode, null, true); // For reducing tile-flashing on-screen
	}
	LayoutNode.showDownward(layoutNode);
	//
	if (!subAction){
		onActionEnd('unhideAncestor');
	}
	nextTick(endLoadInd);
	return success;
}

// For tile-info modal
const infoModalNodeName = ref(null as string | null); // Name of node to display info for, or null
const infoModalData = ref(null as InfoResponse | null);
async function onInfoClick(nodeName: string){
	if (!onActionStart('tileInfo')){
		return;
	}
	if (!searchOpen.value){ // Close an active non-search mode
		resetMode();
	}
	// Query server for tol-node info
	let urlParams = new URLSearchParams({type: 'info', name: nodeName, tree: uiOpts.value.tree});
	let responseObj: InfoResponse = await loadFromServer(urlParams);
	if (responseObj != null){
		// Set fields from response
		infoModalNodeName.value = nodeName;
		infoModalData.value = responseObj;
	}
}
function onInfoClose(){
	infoModalNodeName.value = null;
	onActionEnd('tileInfo');
}

// For search modal
const searchOpen = ref(false);
function onSearchIconClick(){
	if (!onActionStart('search')){
		return;
	}
	if (!searchOpen.value){
		resetMode();
		searchOpen.value = true;
	}
}
function onSearch(name: string){
	if (modeRunning.value != null){
		console.log('WARNING: Unexpected search event while search/auto mode is running')
		return;
	}
	searchOpen.value = false;
	modeRunning.value = 'search';
	if (tutWelcome.value){ // Don't keep welcome message up during an initial search
		onActionEnd('search');
	}
	expandToNode(name);
}
async function expandToNode(name: string){
	if (modeRunning.value == null){
		return;
	}
	// Check if node is displayed
	let targetNode = layoutMap.value.get(name);
	if (targetNode != null && !targetNode.hidden){
		setLastFocused(targetNode);
		onSearchClose();
		return;
	}
	// Get nearest in-layout-tree ancestor
	let ancestorName = name;
	while (layoutMap.value.get(ancestorName) == null){
		ancestorName = tolMap.value.get(ancestorName)!.parent!;
	}
	let layoutNode = layoutMap.value.get(ancestorName)!;
	// If hidden, expand self/ancestor in ancestry-bar
	if (layoutNode.hidden){
		let nodeInAncestryBar = layoutNode;
		while (!detachedAncestors.value!.includes(nodeInAncestryBar)){
			nodeInAncestryBar = nodeInAncestryBar.parent!;
		}
		if (!uiOpts.value.searchJumpMode){
			await onDetachedAncestorClick(nodeInAncestryBar!, true);
			setTimeout(() => expandToNode(name), uiOpts.value.transitionDuration);
		} else{
			await onDetachedAncestorClick(nodeInAncestryBar!, true, true);
			expandToNode(name);
		}
		return;
	}
	// Attempt tile-expand
	if (uiOpts.value.searchJumpMode){
		// Extend layout tree
		let tolNode = tolMap.value.get(name)!;
		let nodesToAdd = [name] as string[];
		while (tolNode.parent != layoutNode.name){
			nodesToAdd.push(tolNode.parent!);
			tolNode = tolMap.value.get(tolNode.parent!)!;
		}
		nodesToAdd.reverse();
		layoutNode.addDescendantChain(nodesToAdd, tolMap.value, layoutMap.value);
		// Expand-to-view on target-node's parent
		targetNode = layoutMap.value.get(name);
		if (targetNode!.parent != activeRoot.value){
			// Hide ancestors
			LayoutNode.hideUpward(targetNode!.parent!, layoutMap.value);
			activeRoot.value = targetNode!.parent!;
			updateAreaDims();
			await onNonleafClick(activeRoot.value, null, true);
			await onLeafClick(activeRoot.value, null, true);
		} else {
			await onLeafClick(activeRoot.value, null, true);
		}
		setTimeout(() => expandToNode(name), uiOpts.value.transitionDuration);
		return;
	}
	if (overflownRoot.value){
		await onLeafClickHeld(layoutNode, null, true);
		setTimeout(() => expandToNode(name), uiOpts.value.transitionDuration);
		return;
	}
	let success = await onLeafClick(layoutNode, null, true);
	if (success){
		setTimeout(() => expandToNode(name), uiOpts.value.transitionDuration);
		return;
	}
	// Attempt expand-to-view on an ancestor halfway to the active root
	if (layoutNode == activeRoot.value){
		console.log('Screen too small to expand active root');
		onSearchClose();
		return;
	}
	let ancestorChain = [layoutNode];
	while (layoutNode.parent! != activeRoot.value){
		layoutNode = layoutNode.parent!;
		ancestorChain.push(layoutNode);
	}
	layoutNode = ancestorChain[Math.floor((ancestorChain.length - 1) / 2)]
	await onNonleafClickHeld(layoutNode, null, true);
	setTimeout(() => expandToNode(name), uiOpts.value.transitionDuration);
}
function onSearchClose(){
	modeRunning.value = null;
	searchOpen.value = false;
	onActionEnd('search');
}
function onSearchNetWait(){
	primeLoadInd(SERVER_WAIT_MSG);
}

// For auto-mode
type AutoAction = 'move across' | 'move down' | 'move up' | Action;
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
const autoPrevAction = ref(null as AutoAction | null); // Used to help prevent action cycles
const autoPrevActionFail = ref(false); // Used to avoid re-trying a failed expand/collapse
function onAutoIconClick(){
	if (!onActionStart('autoMode')){
		return;
	}
	resetMode();
	modeRunning.value = 'autoMode';
	if (tutWelcome.value){ // Don't keep welcome message up during an initial auto-mode
		onActionEnd('autoMode');
	}
	autoAction();
}
async function autoAction(){
	if (modeRunning.value == null){
		return;
	}
	if (lastFocused.value == null){
		// Pick random leaf LayoutNode
		let layoutNode = activeRoot.value;
		while (layoutNode.children.length > 0){
			let childWeights = layoutNode.children.map(n => n.tips);
			let idx = randWeightedChoice(childWeights);
			layoutNode = layoutNode.children[idx!];
		}
		setLastFocused(layoutNode);
		setTimeout(autoAction, uiOpts.value.autoActionDelay);
	} else {
		// Determine available actions
		let action: AutoAction | null;
		let actionWeights: {[key: string]: number}; // Maps actions to choice weights
		let node: LayoutNode = lastFocused.value;
		if (node.children.length == 0){
			actionWeights = {'move across': 1, 'move up': 2, 'expand': 3};
		} else {
			actionWeights = {
				'move across': 1, 'move down': 2, 'move up': 1,
				'collapse': 1, 'expandToView': 1, 'unhideAncestor': 1
			};
		}
		// Zero weights for disallowed actions
		if (node == activeRoot.value || node.parent!.children.length == 1){
			actionWeights['move across'] = 0;
		}
		if (node == activeRoot.value){
			actionWeights['move up'] = 0;
		}
		if (tolMap.value.get(node.name)!.children.length == 0 || overflownRoot.value){
			actionWeights['expand'] = 0;
		}
		if (!node.children.every(n => n.children.length == 0)){
			actionWeights['collapse'] = 0; // Only collapse if all children are leaves
		}
		if (node.parent != activeRoot.value){
			actionWeights['expandToView'] = 0; // Only expand-to-view if direct child of activeRoot
		}
		if (activeRoot.value.parent == null || node != activeRoot.value){
			actionWeights['unhideAncestor'] = 0; // Only expand ancestry-bar if able and activeRoot
		}
		// Avoid undoing previous action
		if (autoPrevAction.value != null){
			let revAction = getReverseAction(autoPrevAction.value);
			if (revAction != null && revAction in actionWeights){
				actionWeights[revAction as keyof typeof actionWeights] = 0;
			}
			if (autoPrevActionFail.value){
				actionWeights[autoPrevAction.value as keyof typeof actionWeights] = 0;
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
		autoPrevAction.value = action;
		let success = true;
		try {
			switch (action){
				case 'move across': { // Bias towards siblings with higher tips
					let siblings = node.parent!.children.filter(n => n != node);
					let siblingWeights = siblings.map(n => n.tips + 1);
					setLastFocused(siblings[randWeightedChoice(siblingWeights)!]);
					break;
				}
				case 'move down': { // Bias towards children with higher tips
					let childWeights = node.children.map(n => n.tips + 1);
					setLastFocused(node.children[randWeightedChoice(childWeights)!]);
					break;
				}
				case 'move up':
					setLastFocused(node.parent!);
					break;
				case 'expand':
					success = await onLeafClick(node, null, true);
					break;
				case 'collapse':
					success = await onNonleafClick(node, null, true);
					break;
				case 'expandToView':
					success = await onNonleafClickHeld(node, null, true);
					break;
				case 'unhideAncestor':
					success = await onDetachedAncestorClick(node.parent!, true);
					break;
			}
		} catch (error) {
			autoPrevActionFail.value = true;
			onAutoClose();
			return;
		}
		autoPrevActionFail.value = !success;
		setTimeout(autoAction, uiOpts.value.transitionDuration + uiOpts.value.autoActionDelay);
	}
}
function onAutoClose(){
	modeRunning.value = null;
	onActionEnd('autoMode');
}

// For settings modal
const settingsOpen = ref(false);
function onSettingsIconClick(){
	if (!onActionStart('settings')){
		return;
	}
	resetMode();
	settingsOpen.value = true;
}
function onSettingsClose(){
	settingsOpen.value = false;
	onActionEnd('settings');
}
async function onSettingChg(optionType: OptionType, option: string, {relayout = false, reinit = false} = {}){
	// Save setting
	if (optionType == 'LYT'){
		localStorage.setItem(`${optionType} ${option}`,
			String(lytOpts.value[option as keyof LayoutOptions]));
	} else if (optionType == 'UI') {
		localStorage.setItem(`${optionType} ${option}`,
			String(uiOpts.value[option as keyof UiOptions]));
	}
	// Possibly relayout/reinitialise
	if (reinit){
		reInit();
	} else if (relayout){
		relayoutWithCollapse();
	}
}
function onResetSettings(reinit: boolean){
	localStorage.clear();
	if (reinit){
		reInit();
	} else {
		relayoutWithCollapse();
	}
}

// For help modal
const helpOpen = ref(false);
function onHelpIconClick(){
	if (!onActionStart('help')){
		return;
	}
	resetMode();
	helpOpen.value = true;
}
function onHelpClose(){
	helpOpen.value = false;
	onActionEnd('help');
}

// For tutorial pane
const tutPaneOpen = ref(!uiOpts.value.tutorialSkip);
const tutWelcome = ref(!uiOpts.value.tutorialSkip);
const tutTriggerAction = ref(null as Action | null); // Used to advance tutorial upon user-actions
const tutTriggerFlag = ref(false);
const actionsDone = ref(new Set() as Set<Action>); // Used to avoid disabling actions the user has already seen
function onStartTutorial(){
	if (!tutPaneOpen.value){
		tutPaneOpen.value = true;
		updateAreaDims();
		relayoutWithCollapse();
	}
}
function onTutorialSkip(){
	uiOpts.value.tutorialSkip = true;
	onSettingChg('UI', 'tutorialSkip');
}
function onTutStageChg(triggerAction: Action | null){
	tutWelcome.value = false;
	tutTriggerAction.value = triggerAction;
}
function onTutPaneClose(){
	tutPaneOpen.value = false;
	if (tutWelcome.value){
		tutWelcome.value = false;
	} else if (uiOpts.value.tutorialSkip == false){
		uiOpts.value.tutorialSkip = true;
		onSettingChg('UI', 'tutorialSkip');
	}
	uiOpts.value.disabledActions.clear();
	updateAreaDims();
	relayoutWithCollapse(true, true);
}

// For highlighting a node (after search, auto-mode, or startup)
const lastFocused = ref(null as LayoutNode | null); // Used to un-focus 
function setLastFocused(node: LayoutNode | null){
	if (lastFocused.value != null){
		lastFocused.value.hasFocus = false;
	}
	lastFocused.value = node;
	if (node != null){
		node.hasFocus = true;
	}
}

// For general action handling
const modeRunning = ref(null as null | 'search' | 'autoMode');
function resetMode(){
	if (infoModalNodeName.value != null){
		onInfoClose();
	}
	if (searchOpen.value || modeRunning.value == 'search'){
		onSearchClose();
	}
	if (modeRunning.value == 'autoMode'){
		onAutoClose();
	}
	if (settingsOpen.value){
		onSettingsClose();
	}
	if (helpOpen.value){
		onHelpClose();
	}
}
function onActionStart(action: Action): boolean {
	if (isDisabled(action)){
		return false;
	}
	setLastFocused(null);
	return true;
}
function onActionEnd(action: Action){
	// Update info used by tutorial pane
	actionsDone.value.add(action);
	if (tutPaneOpen.value){
		// Close welcome message on first action
		if (tutWelcome.value){
			onTutPaneClose();
		}
		// Tell TutorialPane if trigger-action was done
		if (tutTriggerAction.value == action){
			tutTriggerFlag.value = !tutTriggerFlag.value;
		}
	}
}
function isDisabled(...actions: Action[]): boolean {
	let disabledActions = uiOpts.value.disabledActions;
	return actions.some(a => disabledActions.has(a));
}

// For the loading-indicator
const loadingMsg = ref(null as null | string); // Message to display in loading-indicator
const pendingLoadingRevealHdlr = ref(0); // Used to delay showing the loading-indicator
function primeLoadInd(msg: string){ // Sets up a loading message to display after a timeout
	clearTimeout(pendingLoadingRevealHdlr.value);
	pendingLoadingRevealHdlr.value = setTimeout(() => {
		loadingMsg.value = msg;
	}, 500);
}
function endLoadInd(){ // Cancels or closes a loading message
	clearTimeout(pendingLoadingRevealHdlr.value);
	pendingLoadingRevealHdlr.value = 0;
	if (loadingMsg.value != null){
		loadingMsg.value = null;
	}
}
async function loadFromServer(urlParams: URLSearchParams){ // Like queryServer(), but enables the loading indicator
	primeLoadInd(SERVER_WAIT_MSG);
	let responseObj = await queryServer(urlParams);
	endLoadInd();
	return responseObj;
}

// For collapsing tree upon clicking 'Tilo'
async function collapseTree(){
	if (activeRoot.value != layoutTree.value){
		await onDetachedAncestorClick(layoutTree.value, true);
	}
	if (layoutTree.value.children.length > 0){
		await onNonleafClick(layoutTree.value);
	}
}

// For temporarily changing a sweepToParent setting of 'fallback' to 'prefer',  for efficiency
const changedSweepToParent = ref(false);
watch(modeRunning, (newVal) => {
	if (newVal != null){
		if (lytOpts.value.sweepToParent == 'fallback'){
			lytOpts.value.sweepToParent = 'prefer';
			changedSweepToParent.value = true;
		}
	} else {
		if (changedSweepToParent.value){
			lytOpts.value.sweepToParent = 'fallback';
			changedSweepToParent.value = false;
		}
	}
});

// For keyboard shortcuts
function onKeyDown(evt: KeyboardEvent){
	if (uiOpts.value.disableShortcuts){
		return;
	}
	if (evt.key == 'Escape'){
		resetMode();
	} else if (evt.key == 'f' && evt.ctrlKey){
		evt.preventDefault();
		// Open/focus search bar
		if (!searchOpen.value){
			onSearchIconClick();
		}
	} else if (evt.key == 'F' && evt.ctrlKey){
		// If search bar is open, switch search mode
		if (searchOpen.value){
			uiOpts.value.searchJumpMode = !uiOpts.value.searchJumpMode;
			onSettingChg('UI', 'searchJumpMode');
		}
	}
}
onMounted(() => {
	window.addEventListener('keydown', onKeyDown); // 'keydown' needed to override default CTRL-F
});
onUnmounted(() => {
	window.removeEventListener('keydown', onKeyDown);
});

// Styles
const buttonStyles = computed(() => ({
	color: uiOpts.value.textColor,
	backgroundColor: uiOpts.value.altColorDark,
}));
const tutPaneContainerStyles = computed((): Record<string,string> => {
	if (uiOpts.value.breakpoint == 'sm'){
		return {
			minHeight: (tutPaneOpen.value ? uiOpts.value.tutPaneSz : 0) + 'px',
			maxHeight: (tutPaneOpen.value ? uiOpts.value.tutPaneSz : 0) + 'px',
			transitionProperty: 'max-height, min-height',
			transitionDuration: uiOpts.value.transitionDuration + 'ms',
			overflow: 'hidden',
		};
	} else {
		return {
			position: 'absolute',
			bottom: '0.5cm',
			right: '0.5cm',
			visibility: tutPaneOpen.value ? 'visible' : 'hidden',
			transitionProperty: 'visibility',
			transitionDuration: uiOpts.value.transitionDuration + 'ms',
		};
	}
});
const tutPaneStyles = computed((): Record<string,string> => {
	if (uiOpts.value.breakpoint == 'sm'){
		return {
			height: uiOpts.value.tutPaneSz + 'px',
		}
	} else {
		return {
			height: uiOpts.value.tutPaneSz + 'px',
			minWidth: '10cm',
			maxWidth: '10cm',
			borderRadius: uiOpts.value.borderRadius + 'px',
			boxShadow: '0 0 3px black',
		};
	}
});
const ancestryBarContainerStyles = computed((): Record<string,string> => {
	let ancestryBarBreadth = detachedAncestors.value == null ? 0 : uiOpts.value.ancestryBarBreadth;
	let styles = {
		minWidth: 'auto',
		maxWidth: 'none',
		minHeight: 'auto',
		maxHeight: 'none',
		transitionDuration: uiOpts.value.transitionDuration + 'ms',
		transitionProperty: '',
		overflow: 'hidden',
	};
	if (wideMainArea.value){
		styles.minWidth = ancestryBarBreadth + 'px';
		styles.maxWidth = ancestryBarBreadth + 'px';
		styles.transitionProperty = 'min-width, max-width';
	} else {
		styles.minHeight = ancestryBarBreadth + 'px';
		styles.maxHeight = ancestryBarBreadth + 'px';
		styles.transitionProperty = 'min-height, max-height';
	}
	return styles;
});
</script>
