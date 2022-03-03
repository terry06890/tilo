<script>
export default {
	name: "tile-tree",
	data(){
		return {
			TILE_SPACING: 5,
			HEADER_SZ: 20,
		}
	},
	props: {
		tree: Object,
		x: Number,
		y: Number,
		width: Number,
		height: Number,
		isRoot: Boolean,
	},
	computed: {
		layout(){
			if (!this.tree.children || this.tree.children.length == 0)
				return {};
			let hOffset = (this.isRoot ? 0 : this.HEADER_SZ);
			let x = 0, y = hOffset, w = this.width, h = this.height - hOffset;
			//return this.basicSquaresLayout(this.tree.children, 0, hOffset, this.width, this.height - hOffset);
			return this.sweepToSideLayout(this.tree.children, 0, hOffset, this.width, this.height - hOffset);
		}
	},
	methods: {
		basicSquaresLayout(nodes, x0, y0, w, h){
			//determine layout for squares in a specified rectangle, with spacing
			let numCols = this.pickNumCols(nodes.length, w/h);
			let numRows = Math.ceil(nodes.length / numCols);
			let tileSz = Math.min(
				((w - this.TILE_SPACING) / numCols) - this.TILE_SPACING,
				((h - this.TILE_SPACING) / numRows) - this.TILE_SPACING);
			return Object.fromEntries(
				nodes.map((el, idx) => [el.name, {
					x: x0 + (idx % numCols)*(tileSz + this.TILE_SPACING) + this.TILE_SPACING,
					y: y0 + Math.floor(idx / numCols)*(tileSz + this.TILE_SPACING) + this.TILE_SPACING,
					w: tileSz,
					h: tileSz
					}])
				);
		},
		pickNumCols(numTiles, aspectRatio){ //account for tile-spacing?
			//look for number of columns with highest occupied-fraction of rectangles with aspectRatio
			let bestNum, bestFrac = 0;
			for (let numCols = 1; numCols <= numTiles; numCols++){
				let numRows = Math.ceil(numTiles/numCols);
				let ar = numCols/numRows;
				let frac = aspectRatio > ar ? ar/aspectRatio : aspectRatio/ar;
				if (frac > bestFrac){
					bestFrac = frac;
					bestNum = numCols;
				}
			}
			return bestNum;
		},
		sweepToSideLayout(nodes, x0, y0, w, h){
			//separate leaf and non-leaf nodes
			let leaves = [], nonLeaves = [];
			nodes.forEach(e => ((e.children && e.children.length > 0) ? nonLeaves : leaves).push(e));
			//determine layout
			if (nonLeaves.length == 0){ //if all leaves, use squares-layout
				return this.basicSquaresLayout(this.tree.children, x0, y0, w, h);
			} else { //if some non-leaves, use rect-layout
				let retVal = {};
				if (leaves.length > 0){
					let ratio = leaves.length / this.tree.tileCount;
					retVal = this.basicSquaresLayout(leaves, x0, y0, w*ratio, h);
					x0 += w*ratio;
					w -= w*ratio;
				}
				return {...retVal, ...this.basicSquaresLayout(nonLeaves, x0, y0, w, h)};
			}
		}
	}
}
</script>

<template>
<div v-if="tree.children && tree.children.length > 0" class="border border-black"
	:style="{position: 'absolute', left: x + 'px', top: y + 'px', width: + width + 'px', height: height + 'px'}">
	<div v-if="!isRoot" :style="{height: HEADER_SZ + 'px'}" class="text-center">{{tree.name}}</div>
	<tile-tree v-for="child in tree.children" :tree="child"
		:x="layout[child.name].x" :y="layout[child.name].y" :width="layout[child.name].w" :height="layout[child.name].h"
		></tile-tree>
</div>
<img v-else
	:src="'/src/assets/' + tree.name + '.jpg'" :alt="tree.name"
	:style="{position: 'absolute', left: x + 'px', top: y + 'px'}" :width="width" :height="height"
	class="transition-all duration-300 ease-out border-2 border-amber-900"
	/>
</template>

