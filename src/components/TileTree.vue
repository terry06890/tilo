<script lang="ts">
import {defineComponent} from 'vue';
import Tile from './Tile.vue';
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
const defaultOtherOptions = {
	rootOffset: 5, //px (min offset of root tile from display area boundary)
	transitionDuration: 300, //ms
	resizeDelay: 100, //ms (delay for non-continous relayout during window-resizing)
};

// Component holds a tree structure representing a subtree of 'tol' to be rendered
// Collects events about tile expansion/collapse and window-resize, and initiates relayout of tiles
export default defineComponent({
	data(){
		let layoutTree = initLayoutTree(tol, 0);
		return {
			layoutTree: layoutTree,
			activeRoot: layoutTree,
			layoutOptions: {...defaultLayoutOptions},
			otherOptions: {...defaultOtherOptions},
			width: document.documentElement.clientWidth - (defaultOtherOptions.rootOffset * 2),
			height: document.documentElement.clientHeight - (defaultOtherOptions.rootOffset * 2),
			resizeThrottled: false,
		}
	},
	methods: {
		onResize(){
			if (!this.resizeThrottled){
				// Update data and relayout tiles
				this.width = document.documentElement.clientWidth - (this.otherOptions.rootOffset * 2);
				this.height = document.documentElement.clientHeight - (this.otherOptions.rootOffset * 2);
				tryLayout(this.activeRoot, [0,0], [this.width,this.height], this.layoutOptions, true);
				// Prevent re-triggering until after a delay
				this.resizeThrottled = true;
				setTimeout(() => {this.resizeThrottled = false;}, this.otherOptions.resizeDelay);
			}
		},
		onInnerLeafClicked({layoutNode, domNode}: {layoutNode: LayoutNode, domNode: HTMLElement}){
			let success = tryLayout(this.activeRoot, [0,0], [this.width,this.height], this.layoutOptions, false,
				{type: 'expand', node: layoutNode});
			if (!success){
				// Trigger failure animation
				domNode.classList.remove('animate-expand-shrink');
				domNode.offsetWidth; // Triggers reflow
				domNode.classList.add('animate-expand-shrink');
			}
		},
		onInnerHeaderClicked({layoutNode, domNode}: {layoutNode: LayoutNode, domNode: HTMLElement}){
			let success = tryLayout(this.activeRoot, [0,0], [this.width,this.height], this.layoutOptions, false,
				{type: 'collapse', node: layoutNode});
			if (!success){
				// Trigger failure animation
				domNode.classList.remove('animate-shrink-expand');
				domNode.offsetWidth; // Triggers reflow
				domNode.classList.add('animate-shrink-expand');
			}
		},
		onInnerLeafDblClicked(layoutNode: LayoutNode){
			if (layoutNode == this.activeRoot){
				console.log('Ignored expand-to-view on root node');
				return;
			}
			LayoutNode.hideUpward(layoutNode);
			this.activeRoot = layoutNode;
			tryLayout(layoutNode, [0,0], [this.width,this.height], this.layoutOptions, true,
				{type: 'expand', node: layoutNode});
		},
		onInnerHeaderDblClicked(layoutNode: LayoutNode){
			if (layoutNode.parent == null){
				console.log('Ignored expand-to-view on root node');
				return;
			}
			LayoutNode.hideUpward(layoutNode);
			this.activeRoot = layoutNode;
			tryLayout(layoutNode, [0,0], [this.width,this.height], this.layoutOptions, true);
		},
	},
	created(){
		window.addEventListener('resize', this.onResize);
		tryLayout(this.activeRoot, [0,0], [this.width,this.height], this.layoutOptions, true);
	},
	unmounted(){
		window.removeEventListener('resize', this.onResize);
	},
	components: {
		Tile,
	},
});
</script>

<template>
<div class="h-screen bg-stone-800">
	<tile :layoutNode="layoutTree"
		:headerSz="layoutOptions.headerSz" :tileSpacing="layoutOptions.tileSpacing"
		:transitionDuration="otherOptions.transitionDuration"
		@leaf-clicked="onInnerLeafClicked" @header-clicked="onInnerHeaderClicked"
		@leaf-dbl-clicked="onInnerLeafDblClicked" @header-dbl-clicked="onInnerHeaderDblClicked"/>
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
