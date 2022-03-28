<script lang="ts">
import {defineComponent, PropType} from 'vue';
import {LayoutNode} from '../layout';
import Tile from './Tile.vue'

export default defineComponent({
	props: {
		pos: {type: Array as unknown as PropType<[number,number]>, required: true},
		dims: {type: Array as unknown as PropType<[number,number]>, required: true},
		nodes: {type: Array as PropType<LayoutNode[]>, required: true},
		options: {type: Object, required: true},
	},
	data(){
		return {
			tileMargin: 5, //px (gap between detached-ancestor tiles)
			scrollBarOffset: 10, //px (gap for scrollbar, used to prevent overlap with tiles)
		};
	},
	computed: {
		wideArea(){
			return this.dims[0] >= this.dims[1];
		},
		tileSz(){
			return (this.wideArea ? this.dims[1] : this.dims[0]) - (this.tileMargin * 2) - this.scrollBarOffset;
		},
		usedNodes(){
			return this.nodes.map(n => {
				let newNode = new LayoutNode(n.tolNode, []);
				newNode.dims = [this.tileSz, this.tileSz];
				return newNode;
			});
		},
		hasOverflow(){
			let len = this.tileMargin + (this.tileSz + this.tileMargin) * this.nodes.length;
			return len > (this.wideArea ? this.dims[0] : this.dims[1]);
		},
		styles(): Record<string,string> {
			return {
				position: 'absolute',
				left: this.pos[0] + 'px',
				top: this.pos[1] + 'px',
				width: (this.dims[0] + (this.wideArea || this.hasOverflow ? 0 : -this.scrollBarOffset)) + 'px',
				height: (this.dims[1] + (!this.wideArea || this.hasOverflow ? 0 : -this.scrollBarOffset)) + 'px',
				overflowX: this.wideArea ? 'auto' : 'hidden',
				overflowY: this.wideArea ? 'hidden' : 'auto',
				// Extra padding for scrollbar inclusion
				paddingRight: (this.hasOverflow && !this.wideArea ? this.scrollBarOffset : 0) + 'px',
				paddingBottom: (this.hasOverflow && this.wideArea ? this.scrollBarOffset : 0) + 'px',
				// For child layout
				display: 'flex',
				flexDirection: this.wideArea ? 'row' : 'column',
				gap: this.tileMargin + 'px',
				padding: this.tileMargin + 'px',
				//
				backgroundColor: '#44403c',
				boxShadow: this.options.shadowNormal,
			};
		},
	},
	methods: {
		onClick(node: LayoutNode){
			this.$emit('detached-ancestor-clicked', node);
		},
		onInnerInfoIconClicked(data: LayoutNode){
			this.$emit('info-icon-clicked', data);
		}
	},
	components: {
		Tile,
	},
	emits: ['detached-ancestor-clicked', 'info-icon-clicked'],
});
</script>

<template>
<div :style="styles">
	<tile v-for="(node, idx) in usedNodes" :key="node.tolNode.name" :layoutNode="node"
		:nonAbsPos="true" :headerSz="0" :tileSpacing="0" :options="options"
		@leaf-clicked="onClick(nodes[idx])" @info-icon-clicked="onInnerInfoIconClicked"/>
</div>
</template>
