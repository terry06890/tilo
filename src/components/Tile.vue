<script lang="ts">
import {defineComponent, PropType} from 'vue';
import {TreeNode} from '../types';

const TRANSITION_DURATION = 300;
export default defineComponent({
	name: 'tile',
	data(){
		return {
			zIdx: 0,
			transitionDuration: TRANSITION_DURATION,
			overFlow: 'visible',
		}
	},
	props: {
		tree: {type: Object as PropType<TreeNode>, required: true},
	},
	computed: {
		name(){return this.tree.tolNode.name.replaceAll('\'', '\\\'')}
	},
	methods: {
		onImgClick(){
			this.$emit('tile-clicked', [this.tree]);
			//increase z-index and hide overflow during transition
			this.zIdx = 1;
			this.overFlow = 'hidden';
			setTimeout(() => {this.zIdx = 0; this.overFlow = 'visible'}, this.transitionDuration);
		},
		onInnerTileClicked(nodeList: TreeNode[]){
			this.$emit('tile-clicked', [...nodeList, this.tree]);
		},
		onHeaderClick(){
			this.$emit('header-clicked', [this.tree]);
			//increase z-index and hide overflow during transition
			this.zIdx = 1;
			this.overFlow = 'hidden';
			setTimeout(() => {this.zIdx = 0; this.overFlow = 'visible'}, this.transitionDuration);
		},
		onInnerHeaderClicked(nodeList: TreeNode[]){
			this.$emit('header-clicked', [...nodeList, this.tree]);
		}
	}
})
</script>

<template>
<div
	:style="{position: 'absolute',
		left: tree.x+'px', top: tree.y+'px', width: tree.w+'px', height: tree.h+'px',
		zIndex: zIdx, overflow: overFlow, transitionDuration: transitionDuration+'ms'}"
	class="transition-[left,top,width,height] ease-out border border-stone-900 bg-white">
	<div v-if="tree.children.length == 0"
		:style="{backgroundImage: 'url(\'/img/' + name + '.jpg\')',
			opacity: (tree.tolNode.children.length > 0 ? 1 : 0.7)}"
		class="hover:cursor-pointer w-full h-full bg-cover" @click="onImgClick"
		/>
	<div v-else>
		<div v-if="(tree.headerSz && !tree.sideArea) || (tree.sideArea && tree.sideArea.sweptLeft)"
			:style="{height: tree.headerSz+'px'}"
			class="text-center hover:cursor-pointer bg-stone-300" @click="onHeaderClick">
			{{tree.tolNode.name}}
		</div>
		<div v-if="tree.sideArea"
			:style="{position: 'absolute', left: tree.sideArea.x+'px', top: tree.sideArea.y+'px',
				width: (tree.sideArea.w + (tree.sideArea.sweptLeft ? tree.sideArea.extraSz : 0))+'px',
				height: (tree.sideArea.h + (tree.sideArea.sweptLeft ? 0 : tree.sideArea.extraSz))+'px',
				borderRightColor: (tree.sideArea.sweptLeft ? 'white' : 'currentColor'),
				borderBottomColor: (tree.sideArea.sweptLeft ? 'currentColor' : 'white'),
				transitionDuration: transitionDuration+'ms'}"
			class="transition-[left,top,width,height] ease-out border border-stone-900 bg-white">
			<div v-if="!tree.sideArea.sweptLeft" :style="{height: tree.headerSz+'px'}"
				class="text-center hover:cursor-pointer bg-stone-300" @click="onHeaderClick">
				{{tree.tolNode.name}}
			</div>
		</div>
		<tile v-for="child in tree.children" :key="child.tolNode.name" :tree="child"
			@tile-clicked="onInnerTileClicked" @header-clicked="onInnerHeaderClicked"
			></tile>
	</div>
</div>
</template>

