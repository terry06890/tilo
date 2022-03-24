<script lang="ts">
import {defineComponent, PropType} from 'vue';
import Tile from './Tile.vue';
import ParentBar from './ParentBar.vue';
import TileInfoModal from './TileInfoModal.vue';
import {TolNode, LayoutNode, initLayoutTree, tryLayout} from '../lib';
import type {LayoutOptions} from '../lib';
// Import paths lack a .ts or .js extension because .ts makes vue-tsc complain, and .js makes vite complain

// Obtain tree-of-life data
import tolRaw from '../tol.json';
function preprocessTol(node: any): any {
	// Add 'children' fields if missing
	if (node.children == null){
		node.children = [];
	} else {
		node.children.forEach(preprocessTol);
	}
	return node;
}
const tol: TolNode = preprocessTol(tolRaw);

// Configurable settings
const defaultLayoutOptions: LayoutOptions = {
	tileSpacing: 8, //px
	headerSz: 20, //px
	minTileSz: 50, //px
	maxTileSz: 200, //px
	layoutType: 'sweep', //'sqr' | 'rect' | 'sweep'
	rectMode: 'auto', //'horz' | 'vert' | 'linear' | 'auto'
	sweepMode: 'left', //'left' | 'top' | 'shorter' | 'auto'
	sweptNodesPrio: 'pow-2/3', //'linear' | 'sqrt' | 'pow-2/3'
	sweepingToParent: true,
};
const defaultComponentOptions = {
	// For leaf/non_leaf tile and separated-parent components
	borderRadius: 5, //px
	shadowNormal: '0 0 2px black',
	shadowHighlight: '0 0 1px 2px greenyellow',
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
	dblClickWait: 200, //ms
};
const defaultOwnOptions = {
	tileAreaOffset: 5, //px (space between root tile and display boundary)
	parentBarSz: defaultLayoutOptions.minTileSz * 2, //px (breadth of separated-parents area)
};

// Component holds a tree structure representing a subtree of 'tol' to be rendered
// Collects events about tile expansion/collapse and window-resize, and initiates relayout of tiles
export default defineComponent({
	data(){
		let layoutTree = initLayoutTree(tol, 0);
		return {
			layoutTree: layoutTree,
			activeRoot: layoutTree,
			infoModalNode: null as TolNode | null, // Hides/unhides info modal, and provides the node to display
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
			};
		},
	},
	methods: {
		onResize(){
			if (!this.resizeThrottled){
				this.width = document.documentElement.clientWidth;
				this.height = document.documentElement.clientHeight;
				tryLayout(this.activeRoot, this.tileAreaPos, this.tileAreaDims, this.layoutOptions, true);
				// Prevent re-triggering until after a delay
				this.resizeThrottled = true;
				setTimeout(() => {this.resizeThrottled = false;}, this.resizeDelay);
			}
		},
		// For tile expand/collapse events
		onInnerLeafClicked({layoutNode, domNode}: {layoutNode: LayoutNode, domNode: HTMLElement}){
			let success = tryLayout(this.activeRoot, this.tileAreaPos, this.tileAreaDims, this.layoutOptions, false,
				{type: 'expand', node: layoutNode});
			if (!success){
				// Trigger failure animation
				domNode.classList.remove('animate-expand-shrink');
				domNode.offsetWidth; // Triggers reflow
				domNode.classList.add('animate-expand-shrink');
			}
		},
		onInnerHeaderClicked({layoutNode, domNode}: {layoutNode: LayoutNode, domNode: HTMLElement}){
			let success = tryLayout(this.activeRoot, this.tileAreaPos, this.tileAreaDims, this.layoutOptions, false,
				{type: 'collapse', node: layoutNode});
			if (!success){
				// Trigger failure animation
				domNode.classList.remove('animate-shrink-expand');
				domNode.offsetWidth; // Triggers reflow
				domNode.classList.add('animate-shrink-expand');
			}
		},
		// For expand-to-view events
		onInnerLeafDblClicked(layoutNode: LayoutNode){
			if (layoutNode == this.activeRoot){
				console.log('Ignored expand-to-view on root node');
				return;
			}
			LayoutNode.hideUpward(layoutNode);
			this.activeRoot = layoutNode;
			tryLayout(layoutNode, this.tileAreaPos, this.tileAreaDims, this.layoutOptions, true,
				{type: 'expand', node: layoutNode});
		},
		onInnerHeaderDblClicked(layoutNode: LayoutNode){
			if (layoutNode.parent == null){
				console.log('Ignored expand-to-view on root node');
				return;
			}
			LayoutNode.hideUpward(layoutNode);
			this.activeRoot = layoutNode;
			tryLayout(layoutNode, this.tileAreaPos, this.tileAreaDims, this.layoutOptions, true);
		},
		onSepdParentClicked(layoutNode: LayoutNode){
			LayoutNode.showDownward(layoutNode);
			this.activeRoot = layoutNode;
			tryLayout(layoutNode, this.tileAreaPos, this.tileAreaDims, this.layoutOptions, true);
		},
		// For info modal events
		onInnerInfoIconClicked(node: LayoutNode){
			this.infoModalNode = node.tolNode;
		},
		onInfoModalClose(){
			this.infoModalNode = null;
		},
		// For preventing double-clicks from highlighting text
		onMouseDown(evt: UIEvent){
			if (evt.detail == 2){
				evt.preventDefault();
			}
		},
	},
	created(){
		window.addEventListener('resize', this.onResize);
		tryLayout(this.activeRoot, this.tileAreaPos, this.tileAreaDims, this.layoutOptions, true);
	},
	unmounted(){
		window.removeEventListener('resize', this.onResize);
	},
	components: {
		Tile,
		ParentBar,
		TileInfoModal,
	},
});
</script>

<template>
<div :style="styles" @mousedown="onMouseDown">
	<tile :layoutNode="layoutTree"
		:headerSz="layoutOptions.headerSz" :tileSpacing="layoutOptions.tileSpacing" :options="componentOptions"
		@leaf-clicked="onInnerLeafClicked" @header-clicked="onInnerHeaderClicked"
		@leaf-dbl-clicked="onInnerLeafDblClicked" @header-dbl-clicked="onInnerHeaderDblClicked"
		@info-icon-clicked="onInnerInfoIconClicked"/>
	<parent-bar v-if="sepdParents != null"
		:pos="[0,0]" :dims="parentBarDims" :nodes="sepdParents" :options="componentOptions"
		@sepd-parent-clicked="onSepdParentClicked" @info-icon-clicked="onInnerInfoIconClicked"/>
	<tile-info-modal :tolNode="infoModalNode" :options="componentOptions" @info-modal-close="onInfoModalClose"/>
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
</style>
