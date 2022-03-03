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
		childTiles(){ //add minSize, maxSize, 
			if (this.tree.children && this.tree.children.length){
				let nodes = this.tree.children;
				let hOffset = (this.isRoot ? 0 : this.HEADER_SZ);
				let adjustedHeight = this.height - hOffset;
				let numCols = this.pickNumCols(nodes.length, this.width/adjustedHeight);
				let numRows = Math.ceil(nodes.length / numCols);
				let tileSz = Math.min(
					((this.width - this.TILE_SPACING) / numCols) - this.TILE_SPACING,
					((adjustedHeight - this.TILE_SPACING) / numRows) - this.TILE_SPACING);
				return nodes.map((el, idx) => ({
					node: el,
					x: (idx % numCols)*(tileSz + this.TILE_SPACING) + this.TILE_SPACING,
					y: Math.floor(idx / numCols)*(tileSz + this.TILE_SPACING) + this.TILE_SPACING + hOffset,
					sz: tileSz,
					}));
			}
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
		}
	}
}
</script>

<template>
<div v-if="tree.children && tree.children.length > 0" class="border border-black"
	:style="{position: 'absolute', left: x + 'px', top: y + 'px', width: + width + 'px', height: height + 'px'}">
	<div v-if="!isRoot" :style="{height: HEADER_SZ + 'px'}" class="text-center">{{tree.name}}</div>
	<tile-tree v-for="child in childTiles" :tree="child.node"
		:x="child.x" :y="child.y" :width="child.sz" :height="child.sz"
		></tile-tree>
</div>
<img v-else
	:src="'/src/assets/' + tree.name + '.jpg'" :alt="tree.name"
	:style="{position: 'absolute', left: x + 'px', top: y + 'px'}" :width="width" :height="height"
	class="transition-all duration-300 ease-out border-2 border-amber-900"
	/>
</template>

