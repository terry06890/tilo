<template>
<div :style="styles" @wheel.stop="onWheelEvt">
	<tile v-for="(node, idx) in dummyNodes" :key="node.name" class="shrink-0"
		:layoutNode="node" :tolMap="tolMap" :nonAbsPos="true" :lytOpts="lytOpts" :uiOpts="uiOpts"
		@leaf-click="onTileClick(nodes[idx])" @info-click="onInfoIconClick"/>
</div>
</template>

<script lang="ts">
import {defineComponent, PropType} from 'vue';
import Tile from './Tile.vue'
import {TolMap, UiOptions} from '../lib';
import {LayoutNode, LayoutOptions} from '../layout';

export default defineComponent({
	props: {
		nodes: {type: Array as PropType<LayoutNode[]>, required: true},
		vert: {type: Boolean, default: false},
		breadth: {type: Number, required: true},
		// Other
		lytOpts: {type: Object as PropType<LayoutOptions>, required: true},
		uiOpts: {type: Object as PropType<UiOptions>, required: true},
		tolMap: {type: Object as PropType<TolMap>, required: true},
	},
	computed: {
		imgSz(){
			return this.breadth - this.lytOpts.tileSpacing - this.uiOpts.scrollGap;
		},
		dummyNodes(){ // Childless versions of 'nodes' used to parameterise <tile>s
			return this.nodes.map(n => {
				let newNode = new LayoutNode(n.name, []);
				newNode.dims = [this.imgSz, this.imgSz];
				return newNode;
			});
		},
		styles(): Record<string,string> {
			return {
				// For child layout
				display: 'flex',
				flexDirection: this.vert ? 'column' : 'row',
				alignItems: 'center',
				gap: this.lytOpts.tileSpacing + 'px',
				padding: this.lytOpts.tileSpacing + 'px',
				overflowX: this.vert ? 'hidden' : 'auto',
				overflowY: this.vert ? 'auto' : 'hidden',
				// Other
				backgroundColor: this.uiOpts.ancestryBarBgColor,
				boxShadow: this.uiOpts.shadowNormal,
			};
		},
	},
	watch: {
		// Used to scroll to end of bar upon node/screen changes
		nodes(){
			this.$nextTick(() => this.scrollToEnd()); // Without timeout, seems to run before new tiles are added
		},
		vert(){
			setTimeout(() => this.scrollToEnd(), 0);
		},
	},
	methods: {
		// Click events
		onTileClick(node: LayoutNode){
			this.$emit('ancestor-click', node);
		},
		onInfoIconClick(data: string){
			this.$emit('info-click', data);
		},
		// For converting vertical scroll to horizontal
		onWheelEvt(evt: WheelEvent){
			if (!this.vert && Math.abs(evt.deltaX) < Math.abs(evt.deltaY)){
				this.$el.scrollLeft -= (evt.deltaY > 0 ? -30 : 30);
			}
		},
		// Other
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
	emits: ['ancestor-click', 'info-click', ],
});
</script>
