<script>
import {defaultLayout} from './layout.js';

let lastChangedTile = null; //used to increase TileTree z-index during a transition
function updateZForTransition(tileTree){
	if (lastChangedTile !== null){
		lastChangedTile.zIdx = 0;
	}
	tileTree.zIdx = 1;
	lastChangedTile = tileTree;
}

export default {
	name: 'tile-tree',
	data(){
		return {
			zIdx: 0,
			layoutSys: defaultLayout,
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
			let hOffset = (this.isRoot ? 0 : this.layoutSys.HEADER_SZ);
			let x = 0, y = hOffset, w = this.width, h = this.height - hOffset;
			return this.layoutSys.genLayout(this.tree.children, 0, hOffset, this.width, this.height - hOffset);
		}
	},
	methods: {
		onImgClick(){
			if (!this.isRoot){
				this.$emit('tile-clicked', [this.tree]);
			} else {
				this.onInnerTileClicked([this.tree]);
			}
			updateZForTransition(this);
		},
		onInnerTileClicked(nodeList){
			if (!this.isRoot){
				this.$emit('tile-clicked', [...nodeList, this.tree]);
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
				}));
				this.layoutSys.updateLayoutInfoOnExpand(nodeList);
			}
		},
		onHeaderClick(){
			this.$emit('header-clicked', [this.tree]);
			updateZForTransition(this);
		},
		onInnerHeaderClicked(nodeList){
			if (!this.isRoot){
				this.$emit('header-clicked', [...nodeList, this.tree]);
			} else { //nodeList will hold an array of tree-objects, from the clicked-on-tile's tree-object upward
				this.layoutSys.updateLayoutInfoOnCollapse(nodeList);
				nodeList[0].children = [];
			}
		}
	}
}
</script>

<template>
<div
	:style="{position: 'absolute', left: x+'px', top: y+'px', width: width+'px', height: height+'px', zIndex: zIdx}"
	class="transition-[left,top,width,height] duration-300 ease-out border border-stone-900 bg-white">
	<img v-if="tree.children.length == 0"
		:src="'/src/assets/' + tree.tolNode.name + '.jpg'" :alt="tree.tolNode.name"
		class="h-full hover:cursor-pointer" @click="onImgClick"
		/>
	<div v-else>
		<div v-if="!isRoot" :style="{height: this.layoutSys.HEADER_SZ + 'px'}"
			class="text-center hover:cursor-pointer bg-stone-300" @click="onHeaderClick">
			{{tree.tolNode.name}}
		</div>
		<tile-tree v-for="child in tree.children" :key="child.tolNode.name" :tree="child"
			:x="layout[child.tolNode.name].x" :y="layout[child.tolNode.name].y"
			:width="layout[child.tolNode.name].w" :height="layout[child.tolNode.name].h"
			@tile-clicked="onInnerTileClicked" @header-clicked="onInnerHeaderClicked"
			></tile-tree>
	</div>
</div>
</template>

