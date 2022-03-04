<script>
import tol from './tol.json';
function addChildArrays(tree){
	if (!tree.children){
		tree.children = [];
	} else {
		tree.children.forEach(addChildArrays);
	}
}
addChildArrays(tol);

import TileTree from "./components/TileTree.vue";
export default {
	data() {
		return {
			tree: this.genTreeForTol(tol, 1), //allow for zero-level?
			width: document.documentElement.clientWidth,
			height: document.documentElement.clientHeight,
		}
	},
	methods: {
		onResize(){
			this.width = document.documentElement.clientWidth;
			this.height = document.documentElement.clientHeight;
		},
		genTreeForTol(tol, lvl){
			if (lvl == 0){
				return {tolNode: tol, children: [], tileCount: 1};
			} else {
				let childTrees = tol.children.map(e => this.genTreeForTol(e, lvl-1));
				return {
					tolNode: tol,
					children: childTrees,
					tileCount: (childTrees.length == 0) ? 1 : childTrees.map(e => e.tileCount).reduce((x,y) => x+y)
				};
			}
		}
	},
	created(){
		window.addEventListener('resize', this.onResize);
	},
	unmounted(){
		window.removeEventListener('resize', this.onResize);
	},
	components: {
		TileTree
	}
}
</script>

<template>
<div class="h-[100vh]">
	<tile-tree :tree="tree" :x="0" :y="0" :width="width" :height="height" isRoot></tile-tree>
</div>
</template>

