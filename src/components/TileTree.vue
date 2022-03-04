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
			if (this.tree.children.length == 0)
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
				nodes.map((el, idx) => [el.tolNode.name, {
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
				nodes.map((el, idx) => [el.tolNode.name, {
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
			nodes.forEach(e => (e.children.length == 0 ? leaves : nonLeaves).push(e));
			//determine layout
			if (nonLeaves.length == 0){ //if all leaves, use squares-layout
				return this.basicSquaresLayout(nodes, x0, y0, w, h);
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
		},
		onImgClick(){
			this.$emit('tile-clicked', [this.tree]);
		},
		onInnerTileClicked(nodeList){
			if (!this.isRoot){
				this.$emit('tile-clicked', nodeList.concat([this.tree]));
			} else { //nodeList will hold an array of tree-objects, from the clicked-on-tile's tree-object upward
				let numNewTiles = nodeList[0].tolNode.children.length;
				if (numNewTiles == 0){
					console.log('Tile-to-expand has no children');
					return;
				}
				//add children
				nodeList[0].children = nodeList[0].tolNode.children.map(e => ({
					tolNode: e,
					children: [],
					tileCount: 1
				}));
				//update tile counts
				nodeList[0].tileCount = numNewTiles;
				for (let i = 1; i < nodeList.length; i++){
					nodeList[i].tileCount += numNewTiles;
				}
				this.tree.tileCount += numNewTiles; //redundant?
			}
		},
		onHeaderClick(){
			console.log('Header clicked');
		}
	}
}
</script>

<template>
<div v-if="tree.children.length > 0" class="border border-black"
	:style="{position: 'absolute', left: x + 'px', top: y + 'px', width: width + 'px', height: height + 'px'}">
	<div v-if="!isRoot" :style="{height: HEADER_SZ + 'px'}"
		class="text-center hover:cursor-pointer" @click="onHeaderClick">
		{{tree.tolNode.name}}
	</div>
	<tile-tree v-for="child in tree.children" :key="child.tolNode.name" :tree="child"
		:x="layout[child.tolNode.name].x" :y="layout[child.tolNode.name].y"
		:width="layout[child.tolNode.name].w" :height="layout[child.tolNode.name].h"
		@tile-clicked="onInnerTileClicked"
		></tile-tree>
</div>
<img v-else
	:src="'/src/assets/' + tree.tolNode.name + '.jpg'" :alt="tree.tolNode.name"
	:style="{position: 'absolute', left: x + 'px', top: y + 'px'}" :width="width" :height="height"
	class="transition-all duration-300 ease-out border-2 border-amber-900 hover:cursor-pointer"
	@click="onImgClick"
	/>
</template>

