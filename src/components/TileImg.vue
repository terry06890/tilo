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
			infoMouseOver: false,
		};
	},
	computed: {
		isExpandable(){
			return this.layoutNode.tolNode.children.length > 0;
		},
		styles(): Record<string,string> {
			return {
				// Sizing
				width: this.tileSz + 'px',
				height: this.tileSz + 'px',
				minWidth: this.tileSz + 'px',
				minHeight: this.tileSz + 'px',
				// Image
				backgroundImage:
					'linear-gradient(to bottom, rgba(0,0,0,0.4), rgba(0,0,0,0) 40%, rgba(0,0,0,0) 60%, rgba(0,0,0,0.4) 100%),' +
					'url(\'/img/' + this.layoutNode.tolNode.name.replaceAll('\'', '\\\'') + '.png\')',
				backgroundSize: 'cover',
				// Child layout
				display: 'flex',
				flexDirection: 'column',
				// Other
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
		infoIconStyles(): Record<string,string> {
			return {
				width: this.options.infoIconSz + 'px',
				height: this.options.infoIconSz + 'px',
				marginTop: 'auto',
				marginBottom: this.options.infoIconPadding + 'px',
				marginRight: this.options.infoIconPadding + 'px',
				alignSelf: 'flex-end',
				color: this.infoMouseOver ? this.options.infoIconHoverColor : this.options.infoIconColor,
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
				this.highlight = false;
			}
		},
		onClick(evt: Event){
			if (this.isExpandable){
				this.highlight = false;
			}
		},
		onInfoMouseEnter(evt: Event){
			this.infoMouseOver = true;
		},
		onInfoMouseLeave(evt: Event){
			this.infoMouseOver = false;
		},
		onInfoClick(evt: Event){
			this.$emit('info-icon-clicked', this.layoutNode);
		},
	},
	emits: ['info-icon-clicked'],
});
</script>

<template>
<div :style="styles" @mouseenter="onMouseEnter" @mouseleave="onMouseLeave" @click="onClick"
	:class="isExpandable ? ['hover:cursor-pointer'] : []">
	<h1 :style="headerStyles">{{layoutNode.tolNode.name}}</h1>
	<svg :style="infoIconStyles" class="hover:cursor-pointer"
		@mouseenter="onInfoMouseEnter" @mouseleave="onInfoMouseLeave" @click.stop="onInfoClick"
		xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
		stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
		<circle cx="12" cy="12" r="10"/>
		<line x1="12" y1="16" x2="12" y2="12"/>
		<line x1="12" y1="8" x2="12.01" y2="8"/>
	</svg>
</div>
</template>
