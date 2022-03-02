<script>
import tol from './tol.json';
export default {
	data() {
		return {
			drawnTol: tol.map(e => ({...e, children:[]})),
			width: document.documentElement.clientWidth,
			height: document.documentElement.clientHeight,
		}
	},
	computed: {
		tiles(){
			//minSize, maxSize, 
			let nodes = this.drawnTol;
			let spacing = 5;
			let numCols = this.pickNumCols(nodes.length, this.width/this.height);
			let numRows = Math.ceil(nodes.length / numCols);
			let tileSz = Math.min(
				((this.width - spacing) / numCols) - spacing,
				((this.height - spacing) / numRows) - spacing);
			let res = nodes.map((el, idx) => ({
				name: el.name,
				x: (idx % numCols)*(tileSz + spacing) + spacing,
				y: Math.floor(idx / numCols)*(tileSz + spacing) + spacing,
				sz: tileSz,
				}));
			console.log(res)
			return res;
		}
	},
	methods: {
		pickNumCols(numTiles, aspectRatio){ //account for tile-spacing?
			//find number of columns with corresponding aspect-ratio closest to aspectRatio
			let closest, smallestDiff = Number.MAX_VALUE;
			for (let numCols = 1; numCols <= numTiles; numCols++){
				let ratio = numCols/Math.ceil(numTiles/numCols);
				let diff = Math.abs(ratio - aspectRatio);
				if (diff < smallestDiff){
					smallestDiff = diff;
					closest = numCols;
				}
			}
			return closest;
		},
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
	}
}
</script>

<template>
	<div class="bg-black h-[100vh]">
		<img v-for="tile in tiles" :src="'/src/assets/' + tile.name + '.jpg'" :alt="tile.name" :id="tile.name"
			:width="tile.sz" :height="tile.sz"
			:style="{position: 'absolute', left: tile.x + 'px', top: tile.y + 'px'}"
			class="transition-all duration-300 ease-out border-2 border-amber-900"
			/>
	</div>
</template>

<style>
</style>
