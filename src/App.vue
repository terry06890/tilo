<script>
import tol from './tol.json';
import TileTree from "./components/TileTree.vue";
export default {
	data() {
		return {
			//tree: tol.map(e => ({...e, children:[]})),
			tree: tol,
			width: document.documentElement.clientWidth,
			height: document.documentElement.clientHeight,
		}
	},
	methods: {
		onResize(){
			this.width = document.documentElement.clientWidth;
			this.height = document.documentElement.clientHeight;
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

