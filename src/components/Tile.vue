<script lang="ts">
import {defineComponent, PropType} from 'vue';
import InfoIcon from './icon/InfoIcon.vue';
import {LayoutNode} from '../layout';
import type {LayoutOptions} from '../layout';

// Component holds a tree-node structure representing a tile or tile-group to be rendered
export default defineComponent({
	props: {
		layoutNode: {type: Object as PropType<LayoutNode>, required: true},
		lytOpts: {type: Object as PropType<LayoutOptions>, required: true},
		uiOpts: {type: Object, required: true},
		nonAbsPos: {type: Boolean, default: false}, // Don't use absolute positioning (only applies for leaf nodes)
	},
	data(){
		return {
			highlight: false,
			infoMouseOver: false,
			clickHoldTimer: 0, // Used to recognise a click-and-hold event
			animating: false, // Used to prevent content overlap and overflow during transitions
		}
	},
	computed: {
		isLeaf(){
			return this.layoutNode.children.length == 0;
		},
		isExpandable(){
			return this.layoutNode.tolNode.children.length > this.layoutNode.children.length;
		},
		showHeader(){
			return (this.layoutNode.showHeader && !this.layoutNode.sepSweptArea) ||
				(this.layoutNode.sepSweptArea && this.layoutNode.sepSweptArea.sweptLeft);
		},
		nonLeafBgColor(){
			let colorArray = this.uiOpts.nonLeafBgColors;
			return colorArray[this.layoutNode.depth % colorArray.length];
		},
		tileStyles(): Record<string,string> {
			return {
				// Places div using layoutNode, with centering if root
				position: this.nonAbsPos && this.isLeaf ? 'static' : 'absolute',
				left: (this.layoutNode.hidden ? 0 : this.layoutNode.pos[0]) + 'px',
				top: (this.layoutNode.hidden ? 0 : this.layoutNode.pos[1]) + 'px',
				width: (this.layoutNode.hidden ? 0 : this.layoutNode.dims[0]) + 'px',
				height: (this.layoutNode.hidden ? 0 : this.layoutNode.dims[1]) + 'px',
				visibility: this.layoutNode.hidden ? 'hidden' : 'visible',
				// Other bindings
				transitionDuration: this.uiOpts.transitionDuration + 'ms',
				zIndex: this.animating ? '1' : '0',
				overflow: this.animating && !this.isLeaf ? 'hidden' : 'visible',
				// Static styles
				transitionProperty: 'left, top, width, height, visibility',
				transitionTimingFunction: 'ease-out',
				// CSS variables
				'--nonLeafBgColor': this.nonLeafBgColor,
				'--tileSpacing': this.lytOpts.tileSpacing + 'px',
			};
		},
		leafStyles(): Record<string,string> {
			return {
				width: '100%',
				height: '100%',
				// Image
				backgroundImage:
					'linear-gradient(to bottom, rgba(0,0,0,0.4), rgba(0,0,0,0) 40%, rgba(0,0,0,0) 60%, rgba(0,0,0,0.4) 100%),' +
					'url(\'/img/' + this.layoutNode.tolNode.name.replaceAll('\'', '\\\'') + '.png\')',
				backgroundSize: 'cover',
				// Child layout
				display: 'flex',
				flexDirection: 'column',
				// Other
				borderRadius: this.uiOpts.borderRadius + 'px',
				boxShadow: this.highlight ? this.uiOpts.shadowHighlight :
					(this.layoutNode.hasFocus ? this.uiOpts.shadowFocused : this.uiOpts.shadowNormal),
			};
		},
		leafHeaderStyles(): Record<string,string> {
			return {
				height: (this.uiOpts.imgTileFontSz + this.uiOpts.imgTilePadding * 2) + 'px',
				lineHeight: this.uiOpts.imgTileFontSz + 'px',
				fontSize: this.uiOpts.imgTileFontSz + 'px',
				padding: this.uiOpts.imgTilePadding + 'px',
				color: this.isExpandable ? this.uiOpts.expandableImgTileColor : this.uiOpts.imgTileColor,
				// For ellipsis
				overflow: 'hidden',
				textOverflow: 'ellipsis',
				whiteSpace: 'nowrap',
			};
		},
		infoIconStyles(): Record<string,string> {
			return {
				width: this.uiOpts.infoIconSz + 'px',
				height: this.uiOpts.infoIconSz + 'px',
				marginTop: 'auto',
				marginBottom: this.uiOpts.infoIconPadding + 'px',
				marginRight: this.uiOpts.infoIconPadding + 'px',
				alignSelf: 'flex-end',
				color: this.infoMouseOver ? this.uiOpts.infoIconHoverColor : this.uiOpts.infoIconColor,
			};
		},
		nonLeafStyles(): Record<string,string> {
			let temp = {
				width: '100%',
				height: '100%',
				backgroundColor: this.nonLeafBgColor,
				borderRadius: this.uiOpts.borderRadius + 'px',
				boxShadow: this.animating ? 'none' : (this.highlight ? this.uiOpts.shadowHighlight :
					(this.layoutNode.hasFocus ? this.uiOpts.shadowFocused : this.uiOpts.shadowNormal)),
			};
			if (this.layoutNode.sepSweptArea != null){
				let r = this.uiOpts.borderRadius + 'px';
				temp = this.layoutNode.sepSweptArea.sweptLeft ?
					{...temp, borderRadius: `${r} ${r} ${r} 0`} :
					{...temp, borderRadius: `${r} 0 ${r} ${r}`};
			}
			return temp;
		},
		nonLeafHeaderStyles(): Record<string,string> {
			let r = this.uiOpts.borderRadius + 'px';
			return {
				height: this.lytOpts.headerSz + 'px',
				lineHeight: this.lytOpts.headerSz + 'px',
				fontSize: this.uiOpts.nonLeafHeaderFontSz + 'px',
				textAlign: 'center',
				color: this.uiOpts.nonLeafHeaderColor,
				backgroundColor: this.uiOpts.nonLeafHeaderBgColor,
				borderRadius: `${r} ${r} 0 0`,
				// For ellipsis
				overflow: 'hidden',
				textOverflow: 'ellipsis',
				whiteSpace: 'nowrap',
			};
		},
		sepSweptAreaStyles(): Record<string,string> {
			let commonStyles = {
				position: 'absolute',
				backgroundColor: this.nonLeafBgColor,
				boxShadow: this.animating ? 'none' : (this.highlight ? this.uiOpts.shadowHighlight :
					(this.layoutNode.hasFocus ? this.uiOpts.shadowFocused : this.uiOpts.shadowNormal)),
				transitionDuration: this.uiOpts.transitionDuration + 'ms',
				transitionProperty: 'left, top, width, height',
				transitionTimingFunction: 'ease-out',
			};
			let area = this.layoutNode.sepSweptArea;
			if (this.layoutNode.hidden || area == null){
				return {
					...commonStyles,
					visibility: 'hidden',
					left: '0',
					top: this.lytOpts.headerSz + 'px',
					width: '0',
					height: '0',
				};
			} else {
				let r = this.uiOpts.borderRadius + 'px';
				return {
					...commonStyles,
					left: area.pos[0] + 'px',
					top: area.pos[1] + 'px',
					width: area.dims[0] + 'px',
					height: area.dims[1] + 'px',
					borderRadius: area.sweptLeft ? `${r} 0 0 ${r}` : `${r} ${r} 0 0`,
				};
			}
		},
		collapseFailFlag(){
			return this.layoutNode.collapseFailFlag;
		},
		expandFailFlag(){
			return this.layoutNode.expandFailFlag;
		},
	},
	watch: {
		expandFailFlag(newVal){
			this.triggerAnimation('animate-expand-shrink');
		},
		collapseFailFlag(newVal){
			this.triggerAnimation('animate-shrink-expand');
		},
	},
	methods: {
		// Click handling
		onMouseDown(){
			this.highlight = false;
			clearTimeout(this.clickHoldTimer);
			this.clickHoldTimer = setTimeout(() => {
				this.clickHoldTimer = 0;
				this.onClickHold();
			}, this.uiOpts.clickHoldDuration);
		},
		onClickHold(){
			if (this.isLeaf && !this.isExpandable){
				console.log('Ignored click-hold on non-expandable node');
				return;
			}
			this.prepForTransition();
			if (this.isLeaf){
				this.$emit('leaf-click-held', this.layoutNode);
			} else {
				this.$emit('header-click-held', this.layoutNode);
			}
		},
		onMouseUp(){
			if (this.clickHoldTimer > 0){
				clearTimeout(this.clickHoldTimer);
				this.clickHoldTimer = 0;
				this.onClick();
			}
		},
		onClick(){
			if (this.isLeaf && !this.isExpandable){
				console.log('Ignored click on non-expandable node');
				return;
			}
			this.prepForTransition();
			if (this.isLeaf){
				this.$emit('leaf-clicked', this.layoutNode);
			} else {
				this.$emit('header-clicked', this.layoutNode);
			}
		},
		prepForTransition(){
			this.animating = true;
			setTimeout(() => {this.animating = false}, this.uiOpts.transitionDuration);
		},
		onInfoClick(evt: Event){
			this.$emit('info-icon-clicked', this.layoutNode);
		},
		// For coloured-outlines on hovered-over leaf-tiles or non-leaf-headers
		onMouseEnter(evt: Event){
			if (!this.isLeaf || this.isExpandable){
				this.highlight = true;
			}
		},
		onMouseLeave(evt: Event){
			if (!this.isLeaf || this.isExpandable){
				this.highlight = false;
			}
		},
		onInfoMouseEnter(evt: Event){
			this.infoMouseOver = true;
		},
		onInfoMouseLeave(evt: Event){
			this.infoMouseOver = false;
		},
		// Child event propagation
		onInnerLeafClicked(data: LayoutNode){
			this.$emit('leaf-clicked', data);
		},
		onInnerHeaderClicked(data: LayoutNode){
			this.$emit('header-clicked', data);
		},
		onInnerLeafClickHeld(data: LayoutNode){
			this.$emit('leaf-click-held', data);
		},
		onInnerHeaderClickHeld(data: LayoutNode){
			this.$emit('header-click-held', data);
		},
		onInnerInfoIconClicked(data: LayoutNode){
			this.$emit('info-icon-clicked', data);
		},
		//
		triggerAnimation(animationClass: string){
			this.$el.classList.remove(animationClass);
			this.$el.offsetWidth; // Triggers reflow
			this.$el.classList.add(animationClass);
		},
	},
	name: 'tile', // Need this to use self in template
	components: {InfoIcon, },
	emits: ['leaf-clicked', 'header-clicked', 'leaf-click-held', 'header-click-held', 'info-icon-clicked'],
});
</script>

<template>
<div :style="tileStyles">
	<div v-if="isLeaf" :style="leafStyles" :class="isExpandable ? ['hover:cursor-pointer'] : []"
		@mouseenter="onMouseEnter" @mouseleave="onMouseLeave"
		@mousedown="onMouseDown" @mouseup="onMouseUp">
		<h1 :style="leafHeaderStyles">{{layoutNode.tolNode.name}}</h1>
		<info-icon :style="infoIconStyles" class="hover:cursor-pointer"
			@mouseenter="onInfoMouseEnter" @mouseleave="onInfoMouseLeave"
			@click.stop="onInfoClick" @mousedown.stop @mouseup.stop/>
	</div>
	<div v-else :style="nonLeafStyles" ref="nonLeaf">
		<h1 v-if="showHeader" :style="nonLeafHeaderStyles" class="hover:cursor-pointer"
			@mouseenter="onMouseEnter" @mouseleave="onMouseLeave"
			@mousedown="onMouseDown" @mouseup="onMouseUp">
			{{layoutNode.tolNode.name}}
		</h1>
		<div :style="sepSweptAreaStyles" ref="sepSweptArea"
			:class="layoutNode?.sepSweptArea?.sweptLeft ? 'hide-right-edge' : 'hide-top-edge'">
			<h1 v-if="layoutNode?.sepSweptArea?.sweptLeft === false"
				:style="nonLeafHeaderStyles" class="hover:cursor-pointer"
				@mouseenter="onMouseEnter" @mouseleave="onMouseLeave"
				@mousedown="onMouseDown" @mouseup="onMouseUp">
				{{layoutNode.tolNode.name}}
			</h1>
		</div>
		<tile v-for="child in layoutNode.children" :key="child.tolNode.name" :layoutNode="child"
			:lytOpts="lytOpts" :uiOpts="uiOpts"
			@leaf-clicked="onInnerLeafClicked" @header-clicked="onInnerHeaderClicked"
			@leaf-click-held="onInnerLeafClickHeld" @header-click-held="onInnerHeaderClickHeld"
			@info-icon-clicked="onInnerInfoIconClicked"/>
	</div>
</div>
</template>

<style>
.hide-right-edge::before {
	content: '';
	position: absolute;
	background-color: var(--nonLeafBgColor);
	right: calc(0px - var(--tileSpacing));
	bottom: 0;
	width: var(--tileSpacing);
	height: calc(100% + var(--tileSpacing));
}
.hide-top-edge::before {
	content: '';
	position: absolute;
	background-color: var(--nonLeafBgColor);
	bottom: calc(0px - var(--tileSpacing));
	right: 0;
	width: calc(100% + var(--tileSpacing));
	height: var(--tileSpacing);
}
</style>
