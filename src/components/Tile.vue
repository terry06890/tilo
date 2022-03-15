<script lang="ts">
import {defineComponent, PropType} from 'vue';
import {LayoutNode} from '../lib';

export default defineComponent({
	name: 'tile',
	data(){
		return {
			zIdx: 0,
			overFlow: 'visible',
		}
	},
	props: {
		layoutNode: {type: Object as PropType<LayoutNode>, required: true},
		transitionDuration: {type: Number, required: true},
		headerSz: {type: Number, required: true},
		tileSpacing: {type: Number, required: true},
		center: {type: Array as unknown as PropType<[number,number]>, default: null},
	},
	computed: {
		name(){return this.layoutNode.tolNode.name.replaceAll('\'', '\\\'')}
	},
	methods: {
		onImgClick(){
			this.$emit('tile-clicked', this.layoutNode);
			//increase z-index and hide overflow during transition
			this.zIdx = 1;
			this.overFlow = 'hidden';
			setTimeout(() => {this.zIdx = 0; this.overFlow = 'visible'}, this.transitionDuration);
		},
		onInnerTileClicked(node: LayoutNode){
			this.$emit('tile-clicked', node);
		},
		onHeaderClick(){
			this.$emit('header-clicked', this.layoutNode);
			//increase z-index and hide overflow during transition
			this.zIdx = 1;
			this.overFlow = 'hidden';
			setTimeout(() => {this.zIdx = 0; this.overFlow = 'visible'}, this.transitionDuration);
		},
		onInnerHeaderClicked(node: LayoutNode){
			this.$emit('header-clicked', node);
		}
	}
})
</script>

<template>
<div
	:style="{position: 'absolute',
		left: (center ? (center[0]-layoutNode.dims[0])/2 : layoutNode.pos[0]) + 'px',
		top: (center ? (center[1]-layoutNode.dims[1])/2 : layoutNode.pos[1]) + 'px',
		width: layoutNode.dims[0]+'px', height: layoutNode.dims[1]+'px',
		zIndex: zIdx, overflow: overFlow, transitionDuration: transitionDuration+'ms'}"
	class="transition-[left,top,width,height] ease-out outline outline-1 bg-white">
	<div v-if="layoutNode.children.length == 0"
		:style="{backgroundImage: 'url(\'/img/' + name + '.jpg\')',
			opacity: (layoutNode.tolNode.children.length > 0 ? 1 : 0.7)}"
		class="hover:cursor-pointer w-full h-full bg-cover" @click="onImgClick"
		/>
	<div v-else>
		<div
			v-if="(layoutNode.showHeader && !layoutNode.sepSweptArea) ||
				(layoutNode.sepSweptArea && layoutNode.sepSweptArea.sweptLeft)"
			:style="{height: headerSz+'px'}"
			class="text-center overflow-hidden text-ellipsis hover:cursor-pointer bg-stone-300"
			@click="onHeaderClick">
			{{layoutNode.tolNode.name}}
		</div>
		<div
			:style="{position: 'absolute',
				left: layoutNode.sepSweptArea ? layoutNode.sepSweptArea.pos[0]+'px' : 0,
				top: layoutNode.sepSweptArea ? layoutNode.sepSweptArea.pos[1]+'px' : headerSz+'px',
				width: layoutNode.sepSweptArea ?
					(layoutNode.sepSweptArea.dims[0]+(layoutNode.sepSweptArea.sweptLeft ? 1 : 0))+'px' : 0,
				height: layoutNode.sepSweptArea ?
					(layoutNode.sepSweptArea.dims[1]+(layoutNode.sepSweptArea.sweptLeft ? 0 : 1))+'px' : 0,
				transitionDuration: transitionDuration+'ms'}"
			class="transition-[left,top,width,height] ease-out bg-white
				before:absolute before:bg-black before:-top-[1px] before:-left-[1px] before:w-full before:h-full before:-z-10
				after:absolute after:bg-black after:-bottom-[1px] after:-left-[1px] after:w-full after:h-full after:-z-10">
			<div v-if="layoutNode.sepSweptArea && !layoutNode.sepSweptArea.sweptLeft" :style="{height: headerSz+'px'}"
				class="text-center overflow-hidden text-ellipsis hover:cursor-pointer bg-stone-300"
				@click="onHeaderClick">
				{{layoutNode.tolNode.name}}
			</div>
		</div>
		<tile v-for="child in layoutNode.children" :key="child.tolNode.name" :layoutNode="child"
			:headerSz="headerSz" :tileSpacing="tileSpacing" :transitionDuration="transitionDuration"
			@tile-clicked="onInnerTileClicked" @header-clicked="onInnerHeaderClicked"
			></tile>
	</div>
</div>
</template>
