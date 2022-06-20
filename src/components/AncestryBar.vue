<script lang="ts">
import {defineComponent, PropType} from 'vue';
import Tile from './Tile.vue'
import {LayoutNode} from '../layout';
import type {LayoutOptions} from '../layout';
import type {TolMap} from '../lib';

// Displays a sequence of nodes, representing ancestors from a tree-of-life root to a currently-active root
export default defineComponent({
	props: {
		nodes: {type: Array as PropType<LayoutNode[]>, required: true},
		vert: {type: Boolean, default: false},
		// Other
		tolMap: {type: Object as PropType<TolMap>, required: true},
		lytOpts: {type: Object as PropType<LayoutOptions>, required: true},
		uiOpts: {type: Object, required: true},
	},
	computed: {
		usedNodes(){ // Childless versions of 'nodes' used to parameterise <tile>
			return this.nodes.map(n => {
				let newNode = new LayoutNode(n.name, []);
				newNode.dims = [this.uiOpts.ancestryBarImgSz, this.uiOpts.ancestryBarImgSz];
				return newNode;
			});
		},
		styles(): Record<string,string> {
			return {
				overflowX: this.vert ? 'hidden' : 'auto',
				overflowY: this.vert ? 'auto' : 'hidden',
				maxHeight: '100vh',
				// For child layout
				display: 'flex',
				flexDirection: this.vert ? 'column' : 'row',
				gap: this.uiOpts.ancestryTileMargin + 'px',
				padding: this.uiOpts.ancestryTileMargin + 'px',
				// Other
				backgroundColor: this.uiOpts.ancestryBarBgColor,
				boxShadow: this.uiOpts.shadowNormal,
			};
		},
	},
	watch: {
		nodes(){
			setTimeout(() => this.scrollToEnd(), 0); // Without timeout, seems to run before new tiles are added
		},
		vert(){
			setTimeout(() => this.scrollToEnd(), 0);
		},
	},
	methods: {
		onTileClick(node: LayoutNode){
			this.$emit('detached-ancestor-click', node);
		},
		onInfoIconClick(data: string){
			this.$emit('info-icon-click', data);
		},
		onWheelEvt(evt: WheelEvent){
			// Possibly convert vertical scroll to horizontal
			if (!this.vert && Math.abs(evt.deltaX) < Math.abs(evt.deltaY)){
				this.$el.scrollLeft -= (evt.deltaY > 0 ? 30 : -30);
			}
		},
		scrollToEnd(){
			if (this.vert){
				this.$el.scrollTop = this.$el.scrollHeight;
			} else {
				this.$el.scrollLeft = this.$el.scrollWidth;
			}
		},
	},
	mounted(){
		this.scrollToEnd();
	},
	components: {Tile, },
	emits: ['detached-ancestor-click', 'info-icon-click', ],
});
</script>

<template>
<div :style="styles" @wheel.stop="onWheelEvt">
	<tile v-for="(node, idx) in usedNodes" :key="node.name" class="shrink-0"
		:layoutNode="node" :tolMap="tolMap" :nonAbsPos="true" :lytOpts="lytOpts" :uiOpts="uiOpts"
		@leaf-click="onTileClick(nodes[idx])" @info-icon-click="onInfoIconClick"/>
</div>
</template>
