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
		//determines layout for squares in a specified rectangle, with spacing
		basicSquaresLayout(nodes, x0, y0, w, h){
			//get number-of-columns with highest occupied-fraction of rectangles with aspect-ratio w/h
				//account for tile-spacing?
			let numTiles = nodes.length, ar = w/h;
			let numCols, numRows, bestFrac = 0;
			for (let nc = 1; nc <= numTiles; nc++){
				let nr = Math.ceil(numTiles/nc);
				let ar2 = nc/nr;
				let frac = ar > ar2 ? ar2/ar : ar/ar2;
				if (frac > bestFrac){
					bestFrac = frac;
					numCols = nc;
					numRows = nr;
				}
			}
			//compute other parameters
			let tileSz = Math.min(
				((w - this.TILE_SPACING) / numCols) - this.TILE_SPACING,
				((h - this.TILE_SPACING) / numRows) - this.TILE_SPACING);
			//determine layout
			return Object.fromEntries(
				nodes.map((el, idx) => [el.name, {
					x: x0 + (idx % numCols)*(tileSz + this.TILE_SPACING) + this.TILE_SPACING,
					y: y0 + Math.floor(idx / numCols)*(tileSz + this.TILE_SPACING) + this.TILE_SPACING,
					w: tileSz,
					h: tileSz
					}])
				);
		},
		basicRectsLayout(nodes, x0, y0, w, h){
			//get number-of-columns with highest tileCount-proportions-alignment
			let numTiles = nodes.length;
			let tileCounts = nodes.map(e => e.tileCount);
			let tileCountTotal = tileCounts.reduce((x, y) => x+y);
			let numCols, bestScore = Number.NEGATIVE_INFINITY, rowProportions, colProportions;
			for (let nc = 1; nc <= numTiles; nc++){
				let nr = Math.ceil(numTiles/nc);
				//create grid representing each tile's tileCount (0 for no tile)
				let grid = Array(nr).fill().map(e => Array(nc).fill(0));
				for (let i = 0; i < tileCounts.length; i++){
					grid[Math.floor(i / nc)][i % nc] = tileCounts[i];
				}
				//get totals across each row/column divided by tileCountTotal
				let rowProp = grid.map(e => e.reduce((x, y) => x+y) / tileCountTotal);
				let colProp = [...Array(nc).keys()].map(c => 
					[...Array(nr).keys()].map(r => grid[r][c]).reduce((x,y) => x+y) / tileCountTotal);
				//get score
				let score = 0;
				for (let r = 0; r < nr; r++){
					for (let c = 0; c < nc; c++){
						score -= Math.abs(grid[r][c] - (rowProp[r] * colProp[c]));
					}
				}
				if (score > bestScore){
					bestScore = score;
					numCols = nc;
					rowProportions = rowProp;
					colProportions = colProp;
				}
			}
			//determine layout
			let rowNetProps = [0];
			for (let i = 0; i < rowProportions.length-1; i++){
				rowNetProps.push(rowNetProps[i] + rowProportions[i]);
			}
			let colNetProps = [0];
			for (let i = 0; i < colProportions.length-1; i++){
				colNetProps.push(colNetProps[i] + colProportions[i]);
			}
			let retVal = Object.fromEntries(
				nodes.map((el, idx) => [el.name, {
					x: x0 + colNetProps[idx % numCols]*(w - this.TILE_SPACING) + this.TILE_SPACING,
					y: y0 + rowNetProps[Math.floor(idx / numCols)]*(h - this.TILE_SPACING) + this.TILE_SPACING,
					w: colProportions[idx % numCols]*(w - this.TILE_SPACING) - this.TILE_SPACING,
					h: rowProportions[Math.floor(idx / numCols)]*(h - this.TILE_SPACING) - this.TILE_SPACING
					}]));
			return retVal;
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
					x0 += w*ratio - this.TILE_SPACING;
					w -= (w*ratio - this.TILE_SPACING);
				}
				//return {...retVal, ...this.basicSquaresLayout(nonLeaves, x0, y0, w, h)};
				return {...retVal, ...this.basicRectsLayout(nonLeaves, x0, y0, w, h)};
			}
		}
	}
}
</script>

<template>
<div v-if="tree.children && tree.children.length > 0" class="border border-black"
	:style="{position: 'absolute', left: x + 'px', top: y + 'px', width: + width + 'px', height: height + 'px'}">
	<div v-if="!isRoot" :style="{height: HEADER_SZ + 'px'}" class="text-center">{{tree.name}}</div>
	<tile-tree v-for="child in tree.children" :key="child.name" :tree="child"
		:x="layout[child.name].x" :y="layout[child.name].y" :width="layout[child.name].w" :height="layout[child.name].h"
		></tile-tree>
</div>
<img v-else
	:src="'/src/assets/' + tree.name + '.jpg'" :alt="tree.name"
	:style="{position: 'absolute', left: x + 'px', top: y + 'px'}" :width="width" :height="height"
	class="transition-all duration-300 ease-out border-2 border-amber-900"
	/>
</template>

