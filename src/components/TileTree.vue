<script lang="ts">
import {defineComponent} from 'vue';
import Tile from './Tile.vue';

import {TolNode, LayoutNode} from '../types';
import {genLayout, layoutInfoHooks} from '../layout';
//regarding importing a file f1.ts:
	//using 'import f1.ts' makes vue-tsc complain, and 'import f1.js' makes vite complain
	//using 'import f1' might cause problems with build systems other than vite

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
			layoutTree: this.initLayoutTree(tol as TolNode, 1),
			width: document.documentElement.clientWidth,
			height: document.documentElement.clientHeight,
			resizeThrottled: false,
		}
	},
	methods: {
		initLayoutTree(tol: TolNode, lvl: number): LayoutNode {
			let node = new LayoutNode(tol, []);
			function initRec(node: LayoutNode, lvl: number){
				if (lvl > 0)
					node.children = node.tolNode.children.map(
						(n: TolNode) => initRec(new LayoutNode(n, []), lvl-1));
				return node;
			}
			initRec(node, lvl);
			layoutInfoHooks.initLayoutInfo(node)
			return node;
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
		onInnerTileClicked(nodeList: LayoutNode[]){
			//nodeList is an array of layout-nodes, from the clicked-on-tile's node upward
			let numNewTiles = nodeList[0].tolNode.children.length;
			if (numNewTiles == 0){
				console.log('Tile-to-expand has no children');
				return;
			}
			//add children
			nodeList[0].children = nodeList[0].tolNode.children.map((n: TolNode) => new LayoutNode(n, []));
			layoutInfoHooks.updateLayoutInfoOnExpand(nodeList);
			//try to re-layout
			if (!this.tryLayout())
				nodeList[0].children = [];
		},
		onInnerHeaderClicked(nodeList: LayoutNode[]){
			//nodeList is an array of layout-nodes, from the clicked-on-tile's node upward
			let children = nodeList[0].children;
			nodeList[0].children = [];
			layoutInfoHooks.updateLayoutInfoOnCollapse(nodeList);
			if (!this.tryLayout())
				nodeList[0].children = children;
		},
		tryLayout(){
			let newLayout = genLayout(this.layoutTree, 0, 0, this.width, this.height, true);
			if (newLayout == null){
				console.log('Unable to layout tree');
				return false;
			} else {
				this.applyLayout(newLayout, this.layoutTree);
				return true;
			}
		},
		applyLayout(newLayout: LayoutNode, layoutTree: LayoutNode){
			layoutTree.x = newLayout.x;
			layoutTree.y = newLayout.y;
			layoutTree.w = newLayout.w;
			layoutTree.h = newLayout.h;
			layoutTree.headerSz = newLayout.headerSz;
			newLayout.children.forEach((n,i) => this.applyLayout(n, layoutTree.children[i]));
			//handle case where leaf nodes placed in leftover space from parent-sweep
			if (newLayout.sepSweptArea != null){
				//add parent area coords
				layoutTree.sepSweptArea = newLayout.sepSweptArea;
				//move leaf node children to parent area
				layoutTree.children.filter(n => n.children.length == 0).map(n => {
					n.x += newLayout.sepSweptArea!.x;
					n.y += newLayout.sepSweptArea!.y;
				});
			} else {
				layoutTree.sepSweptArea = null;
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
	<tile :layoutNode="layoutTree" @tile-clicked="onInnerTileClicked" @header-clicked="onInnerHeaderClicked"></tile>
</div>
</template>

