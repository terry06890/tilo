<script lang="ts">
import {defineComponent} from 'vue';
import TileTree from './components/TileTree.vue';

export default defineComponent({
	data(){
		return {
			width: document.documentElement.clientWidth,
			height: document.documentElement.clientHeight,
			// For window-resize-handler throttling
			resizeThrottled: false,
			resizeDelay: 50, //ms
		}
	},
	computed: {
		styles(): Record<string,string> {
			return {
				position: 'absolute',
				left: '0',
				top: '0',
				width: this.width + 'px',
				height: this.height + 'px',
				backgroundColor: 'black',
			};
		}
	},
	methods: {
		onResize(){
			if (!this.resizeThrottled){
				this.width = document.documentElement.clientWidth;
				this.height = document.documentElement.clientHeight;
				// Prevent re-triggering until after a delay
				this.resizeThrottled = true;
				setTimeout(() => {this.resizeThrottled = false;}, this.resizeDelay);
			}
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
	},
})
</script>

<template>
<div :style="styles">
	<tile-tree :pos="[0, 0]" :dims="[width, height]"/>
</div>
</template>

