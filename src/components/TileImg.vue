<script lang="ts">
import {defineComponent, PropType} from 'vue';
import {LayoutNode} from '../lib';

export default defineComponent({
	props: {
		layoutNode: {type: Object as PropType<LayoutNode>, required: true},
		tileSz: {type: Number, required: true}, //px (edge length)
		options: {type: Object, required: true},
	},
	data(){
		return {
			highlight: false,
		};
	},
	computed: {
		isExpandable(){
			return this.layoutNode.tolNode.children.length > 0;
		},
		styles(): Record<string,string> {
			return {
				border: '1px black solid',
				width: this.tileSz + 'px',
				height: this.tileSz + 'px',
				minWidth: this.tileSz + 'px',
				minHeight: this.tileSz + 'px',
				backgroundImage:
					'linear-gradient(to bottom, rgba(0,0,0,0.4), rgba(0,0,0,0) 40%),' +
					'url(\'/img/' + this.layoutNode.tolNode.name.replaceAll('\'', '\\\'') + '.png\')',
				backgroundSize: 'cover',
				borderRadius: this.options.borderRadius + 'px',
				boxShadow: this.highlight ? this.options.shadowHighlight : this.options.shadowNormal,
			};
		},
		headerStyles(): Record<string,string> {
			return {
				height: (this.options.imgTileFontSz + this.options.imgTilePadding * 2) + 'px',
				lineHeight: this.options.imgTileFontSz + 'px',
				fontSize: this.options.imgTileFontSz + 'px',
				padding: this.options.imgTilePadding + 'px',
				color: this.isExpandable ? this.options.expandableImgTileColor : this.options.imgTileColor,
				// For ellipsis
				overflow: 'hidden',
				textOverflow: 'ellipsis',
				whiteSpace: 'nowrap',
			};
		},
	},
	methods: {
		onMouseEnter(evt: Event){
			if (this.isExpandable){
				this.highlight = true;
			}
		},
		onMouseLeave(evt: Event){
			if (this.isExpandable){
				this.highlight = false; }
		},
		onClick(evt: Event){
			if (this.isExpandable){
				this.highlight = false;
			}
		},
	},
});
</script>

<template>
<div :style="styles" @mouseenter="onMouseEnter" @mouseleave="onMouseLeave" @click="onClick"
	:class="isExpandable ? ['hover:cursor-pointer'] : []">
	<h1 :style="headerStyles">{{layoutNode.tolNode.name}}</h1>
</div>
</template>
