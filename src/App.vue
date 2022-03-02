<script>
import tol from './tol.json';
export default {
	data() {
		return {
			drawnTol: tol.map(e => ({...e, children:[]})),
			mode: 'row'
		}
	},
	computed: {
		tiles(){
			//minSize, maxSize, 
			let nodes = this.drawnTol;
			let width = document.documentElement.clientWidth;
			let height = document.documentElement.clientHeight;
			let spacing = 5;
			if (this.mode == 'row'){
				return nodes.map((el, idx) => ({
					name: el.name,
					x: idx*((width - spacing) / nodes.length) + spacing,
					y: spacing,
					w: ((width - spacing) / nodes.length) - spacing,
					h: ((width - spacing) / nodes.length) - spacing,
					}));
			} else if (this.mode == 'col'){
				return nodes.map((el, idx) => ({
					name: el.name,
					x: spacing,
					y: idx*((height - spacing) / nodes.length) + spacing,
					w: ((height - spacing) / nodes.length) - spacing,
					h: ((height - spacing) / nodes.length) - spacing,
					}));
			}
		}
	},
	methods: {
		toggleMode(){
			this.mode = this.mode == 'row' ? 'col' : 'row';
		}
	}
}
</script>

<template>
	<div class="bg-black h-[100vh]">
		<img v-for="tile in tiles" :src="'/src/assets/' + tile.name + '.jpg'" :alt="tile.name" :id="tile.name"
			:width="tile.w" :height="tile.h"
			:style="{position: 'absolute', left: tile.x + 'px', top: tile.y + 'px'}"
			class="transition-all duration-300 ease-out border-2 border-amber-900"
			@click="toggleMode()"
			/>
	</div>
</template>

<style>
</style>
