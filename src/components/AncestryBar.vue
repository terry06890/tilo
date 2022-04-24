<script lang="ts">
import {defineComponent, PropType} from 'vue';
import Tile from './Tile.vue'
import {LayoutNode} from '../layout';
import type {LayoutOptions} from '../layout';
import type {TolMap} from '../tol';

// Displays a sequence of nodes, representing ancestors from a tree-of-life root to a currently-active root
export default defineComponent({
	props: {
		// For absolute positioning
		pos: {type: Array as unknown as PropType<[number,number]>, required: true},
		dims: {type: Array as unknown as PropType<[number,number]>, required: true},
		// The ancestors to display
		nodes: {type: Array as PropType<LayoutNode[]>, required: true},
		// Other
		tolMap: {type: Object as PropType<TolMap>, required: true},
		lytOpts: {type: Object as PropType<LayoutOptions>, required: true},
		uiOpts: {type: Object, required: true},
	},
	computed: {
		wideArea(){
			return this.dims[0] >= this.dims[1];
		},
		tileSz(){
			return (this.wideArea ? this.dims[1] : this.dims[0]) -
				(this.uiOpts.ancestryTileMargin * 2) - this.uiOpts.ancestryBarScrollGap;
		},
		usedNodes(){ // Childless versions of 'nodes' used to parameterise <tile>
			return this.nodes.map(n => {
				let newNode = new LayoutNode(n.name, []);
				newNode.dims = [this.tileSz, this.tileSz];
				return newNode;
			});
		},
		overflowing(){
			let len = this.uiOpts.ancestryTileMargin +
				(this.tileSz + this.uiOpts.ancestryTileMargin) * this.nodes.length;
			return len > (this.wideArea ? this.dims[0] : this.dims[1]);
		},
		width(){
			return this.dims[0] + (this.wideArea || this.overflowing ? 0 : -this.uiOpts.ancestryBarScrollGap);
		},
		height(){
			return this.dims[1] + (!this.wideArea || this.overflowing ? 0 : -this.uiOpts.ancestryBarScrollGap);
		},
		styles(): Record<string,string> {
			return {
				position: 'absolute',
				left: this.pos[0] + 'px',
				top: this.pos[1] + 'px',
				width: this.width + 'px',
				height: this.height + 'px',
				overflowX: this.wideArea ? 'auto' : 'hidden',
				overflowY: this.wideArea ? 'hidden' : 'auto',
				// Extra padding for scrollbar inclusion
				paddingRight: (this.overflowing && !this.wideArea ? this.uiOpts.ancestryBarScrollGap : 0) + 'px',
				paddingBottom: (this.overflowing && this.wideArea ? this.uiOpts.ancestryBarScrollGap : 0) + 'px',
				// For child layout
				display: 'flex',
				flexDirection: this.wideArea ? 'row' : 'column',
				gap: this.uiOpts.ancestryTileMargin + 'px',
				padding: this.uiOpts.ancestryTileMargin + 'px',
				// Other
				backgroundColor: this.uiOpts.ancestryBarBgColor,
				boxShadow: this.uiOpts.shadowNormal,
			};
		},
	},
	methods: {
		onTileClick(node: LayoutNode){
			this.$emit('detached-ancestor-click', node);
		},
		onInfoIconClick(data: LayoutNode){
			this.$emit('info-icon-click', data);
		}
	},
	components: {Tile, },
	emits: ['detached-ancestor-click', 'info-icon-click', ],
});
</script>

<template>
<div :style="styles">
	<tile v-for="(node, idx) in usedNodes" :key="node.name" class="shrink-0"
		:layoutNode="node" :tolMap="tolMap" :nonAbsPos="true" :lytOpts="lytOpts" :uiOpts="uiOpts"
		@leaf-click="onTileClick(nodes[idx])" @info-icon-click="onInfoIconClick"/>
</div>
</template>
