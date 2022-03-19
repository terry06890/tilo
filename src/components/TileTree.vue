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

// Configurable settings (integer values specify pixels)
let layoutOptions: LayoutOptions = {
	tileSpacing: 8,
	headerSz: 20,
	minTileSz: 50,
	maxTileSz: 200,
	layoutType: 'sweep', //'sqr' | 'rect' | 'sweep'
	rectMode: 'auto', //'horz' | 'vert' | 'linear' | 'auto'
	sweepMode: 'left', //'left' | 'top' | 'shorter' | 'auto'
	sweptNodesPrio: 'linear', //'linear' | 'sqrt' | 'pow-2/3'
	sweepingToParent: true,
};
let otherOptions = {
	// Integer values specify milliseconds
	transitionDuration: 300,
	resizeDelay: 100, // During window-resizing, relayout tiles after this delay instead of continously
};

// Component holds a tree structure representing a subtree of 'tol' to be rendered
// Collects events about tile expansion/collapse and window-resize, and initiates relayout of tiles
export default defineComponent({
	data(){
		return {
			layoutTree: new LayoutTree(tol, layoutOptions, 0),
			width: document.documentElement.clientWidth,
			height: document.documentElement.clientHeight,
			layoutOptions: layoutOptions,
			otherOptions: otherOptions,
			resizeThrottled: false,
		}
	},
	methods: {
		onResize(){
			if (!this.resizeThrottled){
				// Update data and relayout tiles
				this.width = document.documentElement.clientWidth;
				this.height = document.documentElement.clientHeight;
				if (!this.layoutTree.tryLayout([0,0], [this.width,this.height])){
					console.log('Unable to layout tree');
				}
				// Prevent re-triggering until after a delay
				this.resizeThrottled = true;
				setTimeout(() => {this.resizeThrottled = false;}, otherOptions.resizeDelay);
			}
		},
		onInnerLeafClicked(clickedNode: LayoutNode){
			if (clickedNode.tolNode.children.length == 0){
				console.log('Tile-to-expand has no children');
				return;
			}
			if (!this.layoutTree.tryLayoutOnExpand([0,0], [this.width,this.height], clickedNode)){
				console.log('Unable to layout tree');
			}
		},
		onInnerHeaderClicked(clickedNode: LayoutNode){
			if (!this.layoutTree.tryLayoutOnCollapse([0,0], [this.width,this.height], clickedNode)){
				console.log('Unable to layout tree');
			}
		},
	},
	created(){
		window.addEventListener('resize', this.onResize);
		if (!this.layoutTree.tryLayout([0,0], [this.width,this.height])){
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
		@leaf-clicked="onInnerLeafClicked" @header-clicked="onInnerHeaderClicked"/>
</div>
</template>
