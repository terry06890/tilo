<script lang="ts">
import {defineComponent} from 'vue';
import Tile from './Tile.vue';
import {TolNode, LayoutTree, LayoutNode} from '../lib';
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
		return {
			layoutTree: new LayoutTree(tol, defaultLayoutOptions, 0),
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
				if (!this.layoutTree.tryLayout([0,0], [this.width,this.height], true)){
					console.log('Unable to layout tree');
				}
				// Prevent re-triggering until after a delay
				this.resizeThrottled = true;
				setTimeout(() => {this.resizeThrottled = false;}, this.otherOptions.resizeDelay);
			}
		},
		onInnerLeafClicked({layoutNode, domNode}: {layoutNode: LayoutNode, domNode: HTMLElement}){
			if (layoutNode.tolNode.children.length == 0){
				//console.log('Tile to expand has no children');
				return;
			}
			let success = this.layoutTree.tryLayout([0,0], [this.width,this.height], false,
				{type: 'expand', node: layoutNode});
			if (!success){
				// Trigger failure animation
				domNode.classList.remove('animate-expand-shrink');
				domNode.offsetWidth; // Triggers reflow
				domNode.classList.add('animate-expand-shrink');
				//console.log('Unable to layout tree');
			}
		},
		onInnerHeaderClicked({layoutNode, domNode}: {layoutNode: LayoutNode, domNode: HTMLElement}){
			let success = this.layoutTree.tryLayout([0,0], [this.width,this.height], false,
				{type: 'collapse', node: layoutNode});
			if (!success){
				// Trigger failure animation
				domNode.classList.remove('animate-shrink-expand');
				domNode.offsetWidth; // Triggers reflow
				domNode.classList.add('animate-shrink-expand');
				//console.log('Unable to layout tree');
			}
		},
		onInnerLeafDblClicked(layoutNode: LayoutNode){
			console.log('double clicked leaf: ' + layoutNode.tolNode.name);
		},
		onInnerHeaderDblClicked(layoutNode: LayoutNode){
			console.log('double clicked header: ' + layoutNode.tolNode.name);
		},
	},
	created(){
		window.addEventListener('resize', this.onResize);
		if (!this.layoutTree.tryLayout([0,0], [this.width,this.height], true)){
			console.log('Unable to layout tree');
		}
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
	<tile :layoutNode="layoutTree.root"
		:headerSz="layoutOptions.headerSz" :tileSpacing="layoutOptions.tileSpacing"
		:transitionDuration="otherOptions.transitionDuration" :isRoot="true"
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
