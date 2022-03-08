<script>
export default {
	name: 'tile',
	data(){
		return {
			zIdx: 0,
		}
	},
	props: {
		tree: Object,
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
	:style="{position: 'absolute', left: tree.x+'px', top: tree.y+'px',
		width: tree.w+'px', height: tree.h+'px', zIndex: zIdx}"
	class="transition-[left,top,width,height] duration-300 ease-out border border-stone-900 bg-white overflow-hidden">
	<div v-if="tree.children.length == 0"
		:style="{backgroundImage: 'url(\'/src/assets/' + tree.tolNode.name + '.jpg\')'}"
		class="hover:cursor-pointer w-full h-full bg-cover" @click="onImgClick"
		/>
	<div v-else>
		<div v-if="tree.headerSz > 0" :style="{height: tree.headerSz+'px'}"
			class="text-center hover:cursor-pointer bg-stone-300" @click="onHeaderClick">
			{{tree.tolNode.name}}
		</div>
		<tile v-for="child in tree.children" :key="child.tolNode.name" :tree="child"
			@tile-clicked="onInnerTileClicked" @header-clicked="onInnerHeaderClicked"
			></tile>
	</div>
</div>
</template>

