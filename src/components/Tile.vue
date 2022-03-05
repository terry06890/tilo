<script>
import {defaultLayout} from './layout.js';
export default {
	name: 'tile',
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
		hideHeader: Boolean,
	},
	computed: {
		layout(){
			if (this.tree.children.length == 0)
				return {};
			let hOffset = (this.hideHeader ? 0 : this.layoutSys.HEADER_SZ);
			let x = 0, y = hOffset, w = this.width, h = this.height - hOffset;
			return this.layoutSys.genLayout(this.tree.children, 0, hOffset, this.width, this.height - hOffset);
		}
	},
	methods: {
		onImgClick(){
			this.$emit('tile-clicked', [this.tree]);
			//increase z-index during transition
			this.zIdx = 1;
			setTimeout(() => this.zIdx = 0, 300);
		},
		onInnerTileClicked(nodeList){
			this.$emit('tile-clicked', [...nodeList, this.tree]);
		},
		onHeaderClick(){
			this.$emit('header-clicked', [this.tree]);
			//increase z-index during transition
			this.zIdx = 1;
			setTimeout(() => this.zIdx = 0, 300);
		},
		onInnerHeaderClicked(nodeList){
			this.$emit('header-clicked', [...nodeList, this.tree]);
		}
	}
}
</script>

<template>
<div
	:style="{position: 'absolute', left: x+'px', top: y+'px', width: width+'px', height: height+'px', zIndex: zIdx}"
	class="transition-[left,top,width,height] duration-300 ease-out border border-stone-900 bg-white overflow-hidden">
	<div v-if="tree.children.length == 0"
		:style="{backgroundImage: 'url(/src/assets/' + tree.tolNode.name + '.jpg)'}"
		class="hover:cursor-pointer w-full h-full bg-cover" @click="onImgClick"
		/>
	<div v-else>
		<div v-if="!hideHeader" :style="{height: this.layoutSys.HEADER_SZ + 'px'}"
			class="text-center hover:cursor-pointer bg-stone-300" @click="onHeaderClick">
			{{tree.tolNode.name}}
		</div>
		<tile v-for="child in tree.children" :key="child.tolNode.name" :tree="child"
			:x="layout[child.tolNode.name].x" :y="layout[child.tolNode.name].y"
			:width="layout[child.tolNode.name].w" :height="layout[child.tolNode.name].h"
			@tile-clicked="onInnerTileClicked" @header-clicked="onInnerHeaderClicked"
			></tile>
	</div>
</div>
</template>

