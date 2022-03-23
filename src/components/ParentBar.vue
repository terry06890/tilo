<script lang="ts">
import {defineComponent, PropType} from 'vue';
import {LayoutNode} from '../lib';
import ParentBarTile from './ParentBarTile.vue'

export default defineComponent({
	props: {
		pos: {type: Array as unknown as PropType<[number,number]>, required: true},
		dims: {type: Array as unknown as PropType<[number,number]>, required: true},
		nodes: {type: Array as PropType<LayoutNode[]>, required: true},
	},
	data(){
		return {
			tileMargin: 5, //px (gap between separated-parent tiles)
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
				paddingRight: (this.hasOverflow && !this.wideArea ? this.scrollBarOffset : 0) + 'px',
				paddingBottom: (this.hasOverflow && this.wideArea ? this.scrollBarOffset : 0) + 'px',
				overflowX: this.wideArea ? 'auto' : 'hidden',
				overflowY: this.wideArea ? 'hidden' : 'auto',
				display: 'flex',
				flexDirection: this.wideArea ? 'row' : 'column',
				gap: this.tileMargin + 'px',
				padding: this.tileMargin + 'px',
				backgroundColor: 'gray',
			};
		},
	},
	components: {
		ParentBarTile,
	},
});
</script>

<template>
<div :style="styles">
	<parent-bar-tile v-for="node in nodes" :key="node.tolNode.name"
		:layoutNode="node" :tileSz="tileSz"/>
</div>
</template>
