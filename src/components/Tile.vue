<script lang="ts">
import {defineComponent, PropType} from 'vue';
import InfoIcon from './icon/InfoIcon.vue';
import {LayoutNode} from '../layout';
import type {LayoutOptions} from '../layout';
import type {TolMap} from '../tol';
import {TolNode} from '../tol';
import {capitalizeWords} from '../util';

// Displays one, or a hierarchy of, tree-of-life nodes, as a 'tile'
export default defineComponent({
	props: {
		layoutNode: {type: Object as PropType<LayoutNode>, required: true},
		tolMap: {type: Object as PropType<TolMap>, required: true},
		// Options
		lytOpts: {type: Object as PropType<LayoutOptions>, required: true},
		uiOpts: {type: Object, required: true},
		// For a leaf node, prevents usage of absolute positioning (used by AncestryBar)
		nonAbsPos: {type: Boolean, default: false},
	},
	data(){
		return {
			highlight: false, // Used to draw a colored outline on mouse hover
			inTransition: false, // Used to prevent content overlap and overflow during transitions
			wasClicked: false, // Used to increase z-index during transition after this tile (or a child) is clicked
			hasExpanded: false, // Set to true after an expansion transition ends, and false upon collapse
				// Used to hide overflow on tile expansion, but not hide a sepSweptArea on subsequent transitions
			clickHoldTimer: 0, // Used to recognise click-and-hold events
		};
	},
	computed: {
		tolNode(): TolNode {
			return this.tolMap.get(this.layoutNode.name)!;
		},
		// Basic abbreviations
		isLeaf(): boolean {
			return this.layoutNode.children.length == 0;
		},
		isExpandableLeaf(): boolean {
			return this.isLeaf && this.tolNode.children.length > 0;
		},
		showNonleafHeader(): boolean {
			return (this.layoutNode.showHeader && this.layoutNode.sepSweptArea == null) ||
				(this.layoutNode.sepSweptArea != null && this.layoutNode.sepSweptArea.sweptLeft);
		},
		displayName(): string {
			return capitalizeWords(this.tolNode.commonName || this.layoutNode.name);
		},
		// Style related
		nonleafBgColor(): string {
			let colorArray = this.uiOpts.nonleafBgColors;
			return colorArray[this.layoutNode.depth % colorArray.length];
		},
		boxShadow(): string {
			if (this.highlight){
				return this.uiOpts.shadowHighlight;
			} else if (this.layoutNode.hasFocus && !this.inTransition){
				return this.uiOpts.shadowFocused;
			} else {
				return this.uiOpts.shadowNormal;
			}
		},
		styles(): Record<string,string> {
			let layoutStyles = {
				position: 'absolute',
				left: this.layoutNode.pos[0] + 'px',
				top: this.layoutNode.pos[1] + 'px',
				width: this.layoutNode.dims[0] + 'px',
				height: this.layoutNode.dims[1] + 'px',
				visibility: 'visible',
			};
			if (this.layoutNode.hidden){
				layoutStyles.left = layoutStyles.top = layoutStyles.width = layoutStyles.height = '0';
				layoutStyles.visibility = 'hidden';
			}
			if (this.nonAbsPos){
				layoutStyles.position = 'static';
			}
			return {
				...layoutStyles,
				// Transition related
				transitionDuration: this.uiOpts.tileChgDuration + 'ms',
				transitionProperty: 'left, top, width, height, visibility',
				transitionTimingFunction: 'ease-out',
				zIndex: this.inTransition && this.wasClicked ? '1' : '0',
				overflow: this.inTransition && !this.isLeaf && !this.hasExpanded ? 'hidden' : 'visible',
				// CSS variables
				'--nonleafBgColor': this.nonleafBgColor,
				'--tileSpacing': this.lytOpts.tileSpacing + 'px',
			};
		},
		leafStyles(): Record<string,string> {
			return {
				// Image (and scrims)
				backgroundImage: this.tolNode.imgName != null ?
					'linear-gradient(to bottom, rgba(0,0,0,0.4), #0000 40%, #0000 60%, rgba(0,0,0,0.4) 100%),' +
						'url(\'/img/' + this.tolNode.imgName.replaceAll('\'', '\\\'') + '\')' :
					'none',
				backgroundColor: '#1c1917',
				backgroundSize: 'cover',
				// Other
				borderRadius: this.uiOpts.borderRadius + 'px',
				boxShadow: this.boxShadow,
			};
		},
		leafHeaderStyles(): Record<string,string> {
			return {
				height: (this.uiOpts.leafHeaderFontSz + this.uiOpts.leafTilePadding * 2) + 'px',
				padding: this.uiOpts.leafTilePadding + 'px',
				lineHeight: this.uiOpts.leafHeaderFontSz + 'px',
				fontSize: this.uiOpts.leafHeaderFontSz + 'px',
				fontStyle: this.tolNode.pSupport ? 'normal' : 'italic',
				color: this.tolNode.children.length == 0 ?
					this.uiOpts.headerColor :
					this.tolNode.children.length < this.uiOpts.highTipsVal ?
						this.uiOpts.headerColor2 :
						this.uiOpts.headerColor3,
				// For ellipsis
				overflow: 'hidden',
				textOverflow: 'ellipsis',
				whiteSpace: 'nowrap',
			};
		},
		nonleafStyles(): Record<string,string> {
			let borderR = this.uiOpts.borderRadius + 'px';
			if (this.layoutNode.sepSweptArea != null){
				borderR = this.layoutNode.sepSweptArea.sweptLeft ?
					`${borderR} ${borderR} ${borderR} 0` :
					`${borderR} 0 ${borderR} ${borderR}`;
			}
			return {
				backgroundColor: this.nonleafBgColor,
				borderRadius: borderR,
				boxShadow: this.boxShadow,
			};
		},
		nonleafHeaderStyles(): Record<string,string> {
			let borderR = this.uiOpts.borderRadius + 'px';
			borderR = `${borderR} ${borderR} 0 0`;
			return {
				height: this.lytOpts.headerSz + 'px',
				borderRadius: borderR,
				backgroundColor: this.uiOpts.nonleafHeaderBgColor,
				fontStyle: this.tolNode.pSupport ? 'normal' : 'italic',
			};
		},
		nonleafHeaderTextStyles(): Record<string,string> {
			return {
				lineHeight: this.lytOpts.headerSz + 'px',
				fontSize: this.uiOpts.nonleafHeaderFontSz + 'px',
				textAlign: 'center',
				color: this.uiOpts.nonleafHeaderColor,
				// For ellipsis
				overflow: 'hidden',
				textOverflow: 'ellipsis',
				whiteSpace: 'nowrap',
			};
		},
		infoIconStyles(): Record<string,string> {
			let size = this.uiOpts.infoIconSz + 'px';
			return {
				width: size,
				height: size,
				minWidth: size,
				minHeight: size,
				margin: this.uiOpts.infoIconMargin + 'px',
			};
		},
		sepSweptAreaStyles(): Record<string,string> {
			let borderR = this.uiOpts.borderRadius + 'px';
			let styles = {
				position: 'absolute',
				backgroundColor: this.nonleafBgColor,
				boxShadow: this.boxShadow,
				transitionDuration: this.uiOpts.tileChgDuration + 'ms',
				transitionProperty: 'left, top, width, height, visibility',
				transitionTimingFunction: 'ease-out',
			};
			let area = this.layoutNode.sepSweptArea;
			if (!this.layoutNode.hidden && area != null){
				return {
					...styles,
					visibility: 'visible',
					left: area.pos[0] + 'px',
					top: area.pos[1] + 'px',
					width: area.dims[0] + 'px',
					height: area.dims[1] + 'px',
					borderRadius: area.sweptLeft ?
						`${borderR} 0 0 ${borderR}` :
						`${borderR} ${borderR} 0 0`,
				};
			} else {
				return {
					...styles,
					visibility: 'hidden',
					left: '0',
					top: this.lytOpts.headerSz + 'px',
					width: '0',
					height: '0',
					borderRadius: borderR,
				};
			}
		},
		// For watching layoutNode data
		pos(){
			return this.layoutNode.pos;
		},
		dims(){
			return this.layoutNode.dims;
		},
		failFlag(){
			return this.layoutNode.failFlag;
		},
	},
	watch: {
		// For setting transition state (can be triggered externally, like via search and auto-mode)
		pos: {
			handler(newVal, oldVal){
				if ((newVal[0] != oldVal[0] || newVal[1] != oldVal[1]) && !this.inTransition){
					this.inTransition = true;
				}
			},
			deep: true,
		},
		dims: {
			handler(newVal, oldVal){
				if ((newVal[0] != oldVal[0] || newVal[1] != oldVal[1]) && !this.inTransition){
					this.inTransition = true;
				}
			},
			deep: true,
		},
		// For externally triggering fail animations (used by search and auto-mode)
		failFlag(){
			this.triggerAnimation(this.isLeaf ? 'animate-expand-shrink' : 'animate-shrink-expand');
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
		onMouseUp(){
			if (this.clickHoldTimer > 0){
				clearTimeout(this.clickHoldTimer);
				this.clickHoldTimer = 0;
				this.onClick();
			}
		},
		onClick(){
			if (this.isLeaf && !this.isExpandableLeaf){
				console.log('Ignored click on non-expandable node');
				return;
			}
			this.wasClicked = true;
			this.$emit(this.isLeaf ? 'leaf-click' : 'nonleaf-click', this.layoutNode);
		},
		onClickHold(){
			if (this.isLeaf && !this.isExpandableLeaf){
				console.log('Ignored click-hold on non-expandable node');
				return;
			}
			this.$emit(this.isLeaf ? 'leaf-click-held' : 'nonleaf-click-held', this.layoutNode);
		},
		onInfoIconClick(evt: Event){
			this.$emit('info-icon-click', this.layoutNode);
		},
		// Mouse hover handling
		onMouseEnter(evt: Event){
			if ((!this.isLeaf || this.isExpandableLeaf) && !this.inTransition){
				this.highlight = true;
			}
		},
		onMouseLeave(evt: Event){
			this.highlight = false;
		},
		// Child event propagation
		onInnerLeafClick(node: LayoutNode){
			this.wasClicked = true;
			this.$emit('leaf-click', node);
		},
		onInnerNonleafClick(node: LayoutNode){
			this.wasClicked = true;
			this.$emit('nonleaf-click', node);
		},
		onInnerLeafClickHeld(node: LayoutNode){
			this.$emit('leaf-click-held', node);
		},
		onInnerNonleafClickHeld(node: LayoutNode){
			this.$emit('nonleaf-click-held', node);
		},
		onInnerInfoIconClick(node: LayoutNode){
			this.$emit('info-icon-click', node);
		},
		// Other
		onTransitionEnd(){
			this.inTransition = false;
			this.wasClicked = false;
			this.hasExpanded = this.layoutNode.children.length > 0;
		},
		triggerAnimation(animation: string){
			this.$el.classList.remove(animation);
			this.$el.offsetWidth; // Triggers reflow
			this.$el.classList.add(animation);
		},
	},
	name: 'tile', // Note: Need this to use self in template
	components: {InfoIcon, },
	emits: ['leaf-click', 'nonleaf-click', 'leaf-click-held', 'nonleaf-click-held', 'info-icon-click', ],
});
</script>

<template>
<div :style="styles" @transitionend="onTransitionEnd"> <!-- Enclosing div needed for size transitions -->
	<div v-if="isLeaf" :style="leafStyles"
		class="w-full h-full flex flex-col overflow-hidden" :class="{'hover:cursor-pointer': isExpandableLeaf}"
		@mouseenter="onMouseEnter" @mouseleave="onMouseLeave" @mousedown="onMouseDown" @mouseup="onMouseUp">
		<h1 :style="leafHeaderStyles">{{displayName}}</h1>
		<info-icon :style="[infoIconStyles, {marginTop: 'auto'}]"
			class="self-end text-white/10 hover:text-white hover:cursor-pointer"
			@click.stop="onInfoIconClick" @mousedown.stop @mouseup.stop/>
	</div>
	<div v-else :style="nonleafStyles" class="w-full h-full" ref="nonleaf">
		<div v-if="showNonleafHeader" :style="nonleafHeaderStyles" class="flex hover:cursor-pointer"
			@mouseenter="onMouseEnter" @mouseleave="onMouseLeave" @mousedown="onMouseDown" @mouseup="onMouseUp">
			<h1 :style="nonleafHeaderTextStyles" class="grow">{{displayName}}</h1>
			<info-icon :style="infoIconStyles" class="text-white/10 hover:text-white hover:cursor-pointer"
				@click.stop="onInfoIconClick" @mousedown.stop @mouseup.stop/>
		</div>
		<div :style="sepSweptAreaStyles" ref="sepSweptArea"
			:class="layoutNode?.sepSweptArea?.sweptLeft ? 'hide-right-edge' : 'hide-top-edge'">
			<div v-if="layoutNode?.sepSweptArea?.sweptLeft === false"
				:style="nonleafHeaderStyles" class="flex hover:cursor-pointer"
				@mouseenter="onMouseEnter" @mouseleave="onMouseLeave" @mousedown="onMouseDown" @mouseup="onMouseUp">
				<h1 :style="nonleafHeaderTextStyles" class="grow">{{displayName}}</h1>
				<info-icon :style="infoIconStyles" class="text-white/10 hover:text-white hover:cursor-pointer"
					@click.stop="onInfoIconClick" @mousedown.stop @mouseup.stop/>
			</div>
		</div>
		<tile v-for="child in layoutNode.children" :key="child.name"
			:layoutNode="child" :tolMap="tolMap" :lytOpts="lytOpts" :uiOpts="uiOpts"
			@leaf-click="onInnerLeafClick" @nonleaf-click="onInnerNonleafClick"
			@leaf-click-held="onInnerLeafClickHeld" @nonleaf-click-held="onInnerNonleafClickHeld"
			@info-icon-click="onInnerInfoIconClick"/>
	</div>
</div>
</template>

<style>
.hide-right-edge::before {
	content: '';
	position: absolute;
	background-color: var(--nonleafBgColor);
	right: calc(0px - var(--tileSpacing));
	bottom: 0;
	width: var(--tileSpacing);
	height: calc(100% + var(--tileSpacing));
}
.hide-top-edge::before {
	content: '';
	position: absolute;
	background-color: var(--nonleafBgColor);
	bottom: calc(0px - var(--tileSpacing));
	right: 0;
	width: calc(100% + var(--tileSpacing));
	height: var(--tileSpacing);
}
.animate-expand-shrink {
	animation-name: expand-shrink;
	animation-duration: 300ms;
	animation-iteration-count: 1;
	animation-timing-function: ease-in-out;
}
@keyframes expand-shrink {
	from {
		transform: scale(1, 1);
	}
	50% {
		transform: scale(1.1, 1.1);
	}
	to {
		transform: scale(1, 1);
	}
}
.animate-shrink-expand {
	animation-name: shrink-expand;
	animation-duration: 300ms;
	animation-iteration-count: 1;
	animation-timing-function: ease-in-out;
}
@keyframes shrink-expand {
	from {
		transform: translate3d(0,0,0) scale(1, 1);
	}
	50% {
		transform: translate3d(0,0,0) scale(0.9, 0.9);
	}
	to {
		transform: translate3d(0,0,0) scale(1, 1);
	}
}
</style>
