<script lang="ts">
import {defineComponent} from 'vue';
import Tile from './Tile.vue';

import {staticSqrLayout, staticRectLayout, sweepToSideLayout, layoutInfoHooks} from '../layout';
	//for importing f1.ts:
		//using 'import f1.ts' makes vue-tsc complain, and 'import f1.js' makes vite complain
		//using 'import f1' might cause problems with build systems other than vite
import type {TolNode, TreeNode, LayoutNode} from '../layout';
let LAYOUT_FUNC = sweepToSideLayout;

import tol from '../tol.json';
function preprocessTol(tree: any): void {
	if (!tree.children){
		tree.children = [];
	} else {
		tree.children.forEach(preprocessTol);
	}
}
preprocessTol(tol);

export default defineComponent({
	data(){
		return {
			tree: this.initTree(tol as TolNode, 1),
			width: document.documentElement.clientWidth,
			height: document.documentElement.clientHeight,
			resizeThrottled: false,
		}
	},
	methods: {
		initTree(tol: TolNode, lvl: number): TreeNode {
			let tree = {
				tolNode:tol, children:[],
				x:0, y:0, w:0, h:0, headerSz:0,
				sideArea:null, tileCount:0,
			};
			function initTreeRec(tree: TreeNode, lvl: number){
				if (lvl > 0)
					tree.children = tree.tolNode.children.map((tNode: TolNode) => initTreeRec({
						tolNode: tNode, children: [],
						x:0, y:0, w:0, h:0, headerSz:0,
						sideArea:null, tileCount:0,
					}, lvl-1));
				return tree;
			}
			initTreeRec(tree, lvl);
			layoutInfoHooks.initLayoutInfo(tree)
			return tree;
		},
		onResize(){
			if (!this.resizeThrottled){
				this.width = document.documentElement.clientWidth;
				this.height = document.documentElement.clientHeight;
				this.tryLayout();
				//prevent re-triggering until after a delay
				this.resizeThrottled = true;
				setTimeout(() => {this.resizeThrottled = false;}, 100);
			}
		},
		onInnerTileClicked(nodeList: TreeNode[]){
			//nodeList holds an array of tree-objects, from the clicked-on-tile's tree-object upward
			let numNewTiles = nodeList[0].tolNode.children.length;
			if (numNewTiles == 0){
				console.log('Tile-to-expand has no children');
				return;
			}
			//add children
			nodeList[0].children = nodeList[0].tolNode.children.map((tNode: TolNode) => ({
				tolNode: tNode, children: [],
				x:0, y:0, w:0, h:0, headerSz:0,
				sideArea: null, tileCount:0,
			}));
			layoutInfoHooks.updateLayoutInfoOnExpand(nodeList);
			//try to layout tree
			if (!this.tryLayout())
				nodeList[0].children = [];
		},
		onInnerHeaderClicked(nodeList: TreeNode[]){ //nodeList is array of tree-objects, from clicked-on-tile's tree-object upward
			let children = nodeList[0].children;
			nodeList[0].children = [];
			layoutInfoHooks.updateLayoutInfoOnCollapse(nodeList);
			if (!this.tryLayout())
				nodeList[0].children = children;
		},
		tryLayout(){
			let layout = LAYOUT_FUNC(this.tree, 0, 0, this.width, this.height, true);
			if (layout == null){
				console.log('Unable to layout tree');
				return false;
			} else {
				this.applyLayout(layout, this.tree);
				return true;
			}
		},
		applyLayout(layout: LayoutNode, tree: TreeNode){
			tree.x = layout.x;
			tree.y = layout.y;
			tree.w = layout.w;
			tree.h = layout.h;
			tree.headerSz = layout.headerSz;
			layout.children.forEach((n,i) => this.applyLayout(n, tree.children[i]));
			//handle case where leaf nodes placed in leftover space from parent-sweep
			if (layout.sideArea != null){
				//add parent area coords
				tree.sideArea = layout.sideArea;
				//move leaf node children to parent area
				tree.children.filter(n => n.children.length == 0).map(n => {
					n.x += layout.sideArea!.x;
					n.y += layout.sideArea!.y;
				});
			} else {
				tree.sideArea = null;
			}
		}
	},
	created(){
		window.addEventListener('resize', this.onResize);
		this.tryLayout();
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
	<tile :tree="tree" @tile-clicked="onInnerTileClicked" @header-clicked="onInnerHeaderClicked"></tile>
</div>
</template>

