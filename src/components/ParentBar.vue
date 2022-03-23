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
		};
	},
	computed: {
		wideArea(){
			return this.dims[0] >= this.dims[1];
		},
		tileSz(){
			return (this.wideArea ? this.dims[1] : this.dims[0]) - (this.tileMargin * 2);
		},
		styles(): Record<string,string> {
			return {
				position: 'absolute',
				left: this.pos[0] + 'px',
				top: this.pos[1] + 'px',
				width: this.dims[0] + 'px',
				height: this.dims[1] + 'px',
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
