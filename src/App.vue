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
			tree: {tolNode: tol, children: []},
			width: document.documentElement.clientWidth,
			height: document.documentElement.clientHeight,
		}
	},
	methods: {
		onResize(){
			this.width = document.documentElement.clientWidth;
			this.height = document.documentElement.clientHeight;
		},
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
	<tile-tree :treeIn="tree" :x="0" :y="0" :width="width" :height="height" isRoot></tile-tree>
</div>
</template>

