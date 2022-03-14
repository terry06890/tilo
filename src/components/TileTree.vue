<script lang="ts">
import {defineComponent} from 'vue';
import Tile from './Tile.vue';

import {TolNode} from '../types';
import tol from '../tol.json';
function preprocessTol(tree: any): void {
	if (!tree.children){
		tree.children = [];
	} else {
		tree.children.forEach(preprocessTol);
	}
}
preprocessTol(tol);

import {LayoutTree, LayoutNode} from '../layout';
import type {LayoutOptions} from '../layout';
//regarding importing a file f1.ts:
	//using 'import f1.ts' makes vue-tsc complain, and 'import f1.js' makes vite complain
	//using 'import f1' might cause problems with build systems other than vite

let defaultLayoutOptions: LayoutOptions = {
	tileSpacing: 5,
	headerSz: 20,
	minTileSz: 50,
	maxTileSz: 200,
	layoutType: 'sweep', //'sqr' | 'rect' | 'sweep'
	rectMode: 'auto', //'horz' | 'vert' | 'linear' | 'auto'
	rectSpaceShifting: true,
	sweepMode: 'left', //'left' | 'top' | 'shorter' | 'auto'
	sweepingToParent: true,
};
let defaultOtherOptions = {
	transitionDuration: 300,
};

export default defineComponent({
	data(){
		return {
			layoutOptions: defaultLayoutOptions,
			otherOptions: defaultOtherOptions,
			layoutTree: new LayoutTree(tol as TolNode, 1, defaultLayoutOptions),
			width: document.documentElement.clientWidth,
			height: document.documentElement.clientHeight,
			resizeThrottled: false,
		}
	},
	methods: {
		onResize(){
			if (!this.resizeThrottled){
				this.width = document.documentElement.clientWidth;
				this.height = document.documentElement.clientHeight;
				if (!this.layoutTree.tryLayout([0,0], [this.width,this.height]))
					console.log('Unable to layout tree');
				//prevent re-triggering until after a delay
				this.resizeThrottled = true;
				setTimeout(() => {this.resizeThrottled = false;}, 100);
			}
		},
		onInnerTileClicked(node: LayoutNode){
			if (node.tolNode.children.length == 0){
				console.log('Tile-to-expand has no children');
				return;
			}
			if (!this.layoutTree.tryLayoutOnExpand([0,0], [this.width,this.height], node))
				console.log('Unable to layout tree');
		},
		onInnerHeaderClicked(node: LayoutNode){
			if (!this.layoutTree.tryLayoutOnCollapse([0,0], [this.width,this.height], node))
				console.log('Unable to layout tree');
		},
	},
	created(){
		window.addEventListener('resize', this.onResize);
		if (!this.layoutTree.tryLayout([0,0], [this.width,this.height]))
			console.log('Unable to layout tree');
	},
	unmounted(){
		window.removeEventListener('resize', this.onResize);
	},
	components: {
		Tile
	}
})
</script>

<template>
<div class="h-[100vh]">
	<tile :layoutNode="layoutTree.root"
		:headerSz="layoutOptions.headerSz" :tileSpacing="layoutOptions.tileSpacing"
		:transitionDuration="otherOptions.transitionDuration"
		@tile-clicked="onInnerTileClicked" @header-clicked="onInnerHeaderClicked"></tile>
</div>
</template>
