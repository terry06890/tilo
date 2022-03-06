<script>
import tol from '/src/tol.json';
import {defaultLayout, initTree} from '/src/layout.js';
import Tile from './Tile.vue';

export default {
	data(){
		return {
			tree: initTree(this.preprocessTol(tol), 1),
			width: document.documentElement.clientWidth,
			height: document.documentElement.clientHeight,
			layoutSys: defaultLayout,
		}
	},
	methods: {
		preprocessTol(tree){
			if (!tree.children){
				tree.children = [];
			} else {
				tree.children.forEach(this.preprocessTol);
			}
			return tree;
		},
		onResize(){
			this.width = document.documentElement.clientWidth;
			this.height = document.documentElement.clientHeight;
		},
		onInnerTileClicked(nodeList){
			//nodeList holds an array of tree-objects, from the clicked-on-tile's tree-object upward
			let numNewTiles = nodeList[0].tolNode.children.length;
			if (numNewTiles == 0){
				console.log('Tile-to-expand has no children');
				return;
			}
			//add children
			nodeList[0].children = nodeList[0].tolNode.children.map(e => ({
				tolNode: e,
				children: [],
			}));
			this.layoutSys.updateLayoutInfoOnExpand(nodeList);
		},
		onInnerHeaderClicked(nodeList){
			//nodeList will hold an array of tree-objects, from the clicked-on-tile's tree-object upward
			nodeList[0].children = [];
			this.layoutSys.updateLayoutInfoOnCollapse(nodeList);
		},
	},
	created(){
		window.addEventListener('resize', this.onResize);
	},
	unmounted(){
		window.removeEventListener('resize', this.onResize);
	},
	components: {
		Tile
	}
}
</script>

<template>
<div class="h-[100vh]">
	<tile :tree="tree" :x="0" :y="0" :width="width" :height="height" hideHeader
		@tile-clicked="onInnerTileClicked" @header-clicked="onInnerHeaderClicked"></tile>
</div>
</template>

