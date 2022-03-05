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

import {initTree} from './components/layout.js';
import TileTree from './components/TileTree.vue';
export default {
	data() {
		return {
			tree: initTree(tol, 1),
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
	<tile-tree :tree="tree" :x="0" :y="0" :width="width" :height="height" isRoot></tile-tree>
</div>
</template>

