<script lang="ts">
import {defineComponent, PropType} from 'vue';
import {LayoutNode} from '../types';

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
		layoutNode: {type: Object as PropType<LayoutNode>, required: true},
	},
	computed: {
		name(){return this.layoutNode.tolNode.name.replaceAll('\'', '\\\'')}
	},
	methods: {
		onImgClick(){
			this.$emit('tile-clicked', [this.layoutNode]);
			//increase z-index and hide overflow during transition
			this.zIdx = 1;
			this.overFlow = 'hidden';
			setTimeout(() => {this.zIdx = 0; this.overFlow = 'visible'}, this.transitionDuration);
		},
		onInnerTileClicked(nodeList: LayoutNode[]){
			this.$emit('tile-clicked', [...nodeList, this.layoutNode]);
		},
		onHeaderClick(){
			this.$emit('header-clicked', [this.layoutNode]);
			//increase z-index and hide overflow during transition
			this.zIdx = 1;
			this.overFlow = 'hidden';
			setTimeout(() => {this.zIdx = 0; this.overFlow = 'visible'}, this.transitionDuration);
		},
		onInnerHeaderClicked(nodeList: LayoutNode[]){
			this.$emit('header-clicked', [...nodeList, this.layoutNode]);
		}
	}
})
</script>

<template>
<div
	:style="{position: 'absolute',
		left: layoutNode.x+'px', top: layoutNode.y+'px', width: layoutNode.w+'px', height: layoutNode.h+'px',
		zIndex: zIdx, overflow: overFlow, transitionDuration: transitionDuration+'ms'}"
	class="transition-[left,top,width,height] ease-out border border-stone-900 bg-white">
	<div v-if="layoutNode.children.length == 0"
		:style="{backgroundImage: 'url(\'/img/' + name + '.jpg\')',
			opacity: (layoutNode.tolNode.children.length > 0 ? 1 : 0.7)}"
		class="hover:cursor-pointer w-full h-full bg-cover" @click="onImgClick"
		/>
	<div v-else>
		<div
			v-if="(layoutNode.headerSz && !layoutNode.sepSweptArea) || 
				(layoutNode.sepSweptArea && layoutNode.sepSweptArea.sweptLeft)"
			:style="{height: layoutNode.headerSz+'px'}"
			class="text-center hover:cursor-pointer bg-stone-300" @click="onHeaderClick">
			{{layoutNode.tolNode.name}}
		</div>
		<div v-if="layoutNode.sepSweptArea"
			:style="{position: 'absolute', left: layoutNode.sepSweptArea.x+'px', top: layoutNode.sepSweptArea.y+'px',
				width: (layoutNode.sepSweptArea.w +
					(layoutNode.sepSweptArea.sweptLeft ? layoutNode.sepSweptArea.tileSpacing+1 : 0))+'px',
				height: (layoutNode.sepSweptArea.h +
					(layoutNode.sepSweptArea.sweptLeft ? 0 : layoutNode.sepSweptArea.tileSpacing+1))+'px',
				borderRightColor: (layoutNode.sepSweptArea.sweptLeft ? 'white' : 'currentColor'),
				borderBottomColor: (layoutNode.sepSweptArea.sweptLeft ? 'currentColor' : 'white'),
				transitionDuration: transitionDuration+'ms'}"
			class="transition-[left,top,width,height] ease-out border border-stone-900 bg-white">
			<div v-if="!layoutNode.sepSweptArea.sweptLeft" :style="{height: layoutNode.headerSz+'px'}"
				class="text-center hover:cursor-pointer bg-stone-300" @click="onHeaderClick">
				{{layoutNode.tolNode.name}}
			</div>
		</div>
		<tile v-for="child in layoutNode.children" :key="child.tolNode.name" :layoutNode="child"
			@tile-clicked="onInnerTileClicked" @header-clicked="onInnerHeaderClicked"
			></tile>
	</div>
</div>
</template>

