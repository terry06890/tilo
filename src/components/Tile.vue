<script lang="ts">
import {defineComponent, PropType} from 'vue';
import {LayoutNode} from '../lib';
import TileImg from './TileImg.vue';

// Component holds a tree-node structure representing a tile or tile-group to be rendered
export default defineComponent({
	props: {
		layoutNode: {type: Object as PropType<LayoutNode>, required: true},
		options: {type: Object, required: true},
		// Layout settings from parent
		headerSz: {type: Number, required: true},
		tileSpacing: {type: Number, required: true},
	},
	data(){
		return {
			nonLeafHighlight: false,
			clickHoldTimer: 0, // Used to recognise a click-and-hold event
			zIdx: 0, // Used during transitions
			overflow: 'visible', // Used during transitions
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
			let colorArray = this.options.nonLeafBgColors;
			return colorArray[this.layoutNode.depth % colorArray.length];
		},
		tileStyles(): Record<string,string> {
			return {
				// Places div using layoutNode, with centering if root
				position: 'absolute',
				left: (this.layoutNode.hidden ? 0 : this.layoutNode.pos[0]) + 'px',
				top: (this.layoutNode.hidden ? 0 : this.layoutNode.pos[1]) + 'px',
				width: (this.layoutNode.hidden ? 0 : this.layoutNode.dims[0]) + 'px',
				height: (this.layoutNode.hidden ? 0 : this.layoutNode.dims[1]) + 'px',
				visibility: this.layoutNode.hidden ? 'hidden' : 'visible',
				// Other bindings
				transitionDuration: this.options.transitionDuration + 'ms',
				zIndex: String(this.zIdx),
				overflow: String(this.overflow),
				// Static styles
				transitionProperty: 'left, top, width, height, visibility',
				transitionTimingFunction: 'ease-out',
				// CSS variables
				'--nonLeafBgColor': this.nonLeafBgColor,
				'--tileSpacing': this.tileSpacing + 'px',
			};
		},
		nonLeafStyles(): Record<string,string> {
			let temp = {
				width: '100%',
				height: '100%',
				backgroundColor: this.nonLeafBgColor,
				borderRadius: this.options.borderRadius + 'px',
				boxShadow: this.nonLeafHighlight ? this.options.shadowHighlight :
					(this.layoutNode.searchResult ? this.options.shadowSearchResult : this.options.shadowNormal),
			};
			if (this.layoutNode.sepSweptArea != null){
				let r = this.options.borderRadius + 'px';
				temp = this.layoutNode.sepSweptArea.sweptLeft ?
					{...temp, borderRadius: `${r} ${r} ${r} 0`} :
					{...temp, borderRadius: `${r} 0 ${r} ${r}`};
			}
			return temp;
		},
		nonLeafHeaderStyles(): Record<string,string> {
			let r = this.options.borderRadius + 'px';
			return {
				height: this.headerSz + 'px',
				lineHeight: this.headerSz + 'px',
				fontSize: this.options.nonLeafHeaderFontSz + 'px',
				textAlign: 'center',
				color: this.options.nonLeafHeaderColor,
				backgroundColor: this.options.nonLeafHeaderBgColor,
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
				boxShadow: this.nonLeafHighlight ? this.options.shadowHighlight :
					(this.layoutNode.searchResult ? this.options.shadowSearchResult : this.options.shadowNormal),
				transitionDuration: this.options.transitionDuration + 'ms',
				transitionProperty: 'left, top, width, height',
				transitionTimingFunction: 'ease-out',
			};
			let area = this.layoutNode.sepSweptArea;
			if (this.layoutNode.hidden || area == null){
				return {
					...commonStyles,
					visibility: 'hidden',
					left: '0',
					top: this.headerSz + 'px',
					width: '0',
					height: '0',
				};
			} else {
				let r = this.options.borderRadius + 'px';
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
	},
	methods: {
		// Leaf click handling
		onLeafMouseDown(){
			clearTimeout(this.clickHoldTimer);
			this.clickHoldTimer = setTimeout(() => {
				this.clickHoldTimer = 0;
				this.onLeafClickHold();
			}, this.options.clickHoldDuration);
		},
		onLeafMouseUp(){
			if (this.clickHoldTimer > 0){
				clearTimeout(this.clickHoldTimer);
				this.clickHoldTimer = 0;
				this.onLeafClick();
			}
		},
		onLeafClick(){
			if (!this.isExpandable){
				console.log('Ignored click on non-expandable node');
				return;
			}
			this.$emit('leaf-clicked', {layoutNode: this.layoutNode, domNode: this.$el});
			this.leafPrepTransition();
		},
		onLeafClickHold(){
			if (!this.isExpandable){
				console.log('Ignored click-hold on non-expandable node');
				return;
			}
			this.$emit('leaf-click-held', this.layoutNode);
			this.leafPrepTransition();
		},
		leafPrepTransition(){ // Temporary style changes to prevent content overlap and overflow
			this.zIdx = 1;
			this.overflow = 'hidden';
			setTimeout(() => {this.zIdx = 0; this.overflow = 'visible';}, this.options.transitionDuration);
		},
		// Non-leaf click handling
		onHeaderMouseDown(){
			this.nonLeafHighlight = false;
			clearTimeout(this.clickHoldTimer);
			this.clickHoldTimer = setTimeout(() => {
				this.clickHoldTimer = 0;
				this.onHeaderClickHold();
			}, this.options.clickHoldDuration);
		},
		onHeaderMouseUp(){
			if (this.clickHoldTimer > 0){
				clearTimeout(this.clickHoldTimer);
				this.clickHoldTimer = 0;
				this.onHeaderClick();
			}
		},
		onHeaderClick(){
			this.$emit('header-clicked', {layoutNode: this.layoutNode, domNode: this.$el});
			this.nonLeafPrepForTransition();
		},
		onHeaderClickHold(){
			this.$emit('header-click-held', this.layoutNode);
			this.nonLeafPrepForTransition();
		},
		nonLeafPrepForTransition(){ // Temporary style changes to prevent content overlap and overflow
			this.zIdx = 1;
			setTimeout(() => {this.zIdx = 0}, this.options.transitionDuration);
		},
		// For coloured-outlines on hovered-over leaf-tiles or non-leaf-headers
		onNonLeafMouseEnter(evt: Event){
			this.nonLeafHighlight = true;
		},
		onNonLeafMouseLeave(evt: Event){
			this.nonLeafHighlight = false;
		},
		// Child event propagation
		onInnerLeafClicked(data: {layoutNode: LayoutNode, domNode: HTMLElement}){
			this.$emit('leaf-clicked', data);
		},
		onInnerHeaderClicked(data: {layoutNode: LayoutNode, domNode: HTMLElement}){
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
		}
	},
	name: 'tile', // Need this to use self in template
	components: {
		TileImg,
	},
	emits: ['leaf-clicked', 'header-clicked', 'leaf-click-held', 'header-click-held', 'info-icon-clicked'],
});
</script>

<template>
<div :style="tileStyles">
	<tile-img v-if="isLeaf" :layoutNode="layoutNode" :tileSz="layoutNode.dims[0]" :options="options"
		@mousedown="onLeafMouseDown" @mouseup="onLeafMouseUp" @info-icon-clicked="onInnerInfoIconClicked"/>
	<div v-else :style="nonLeafStyles" ref="nonLeaf">
		<h1 v-if="showHeader" :style="nonLeafHeaderStyles" class="hover:cursor-pointer"
			@mouseenter="onNonLeafMouseEnter" @mouseleave="onNonLeafMouseLeave"
			@mousedown="onHeaderMouseDown" @mouseup="onHeaderMouseUp">
			{{layoutNode.tolNode.name}}
		</h1>
		<div :style="sepSweptAreaStyles" ref="sepSweptArea"
			:class="layoutNode?.sepSweptArea?.sweptLeft ? 'hide-right-edge' : 'hide-top-edge'">
			<h1 v-if="layoutNode?.sepSweptArea?.sweptLeft === false"
				:style="nonLeafHeaderStyles" class="hover:cursor-pointer"
				@mouseenter="onNonLeafMouseEnter" @mouseleave="onNonLeafMouseLeave"
				@mousedown="onHeaderMouseDown" @mouseup="onHeaderMouseUp">
				{{layoutNode.tolNode.name}}
			</h1>
		</div>
		<tile v-for="child in layoutNode.children" :key="child.tolNode.name" :layoutNode="child"
			:headerSz="headerSz" :tileSpacing="tileSpacing" :options="options"
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
