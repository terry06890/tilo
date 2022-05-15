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
		// Other
		nonAbsPos: {type: Boolean, default: false},
			// For a leaf node, prevents usage of absolute positioning (used by AncestryBar)
		overflownDim: {type: Number, default: 0},
			// For a non-leaf node, display with overflow within area of this height
	},
	data(){
		return {
			highlight: false, // Used to draw a colored outline on mouse hover
			inTransition: false, // Used to prevent content overlap and overflow during user-perceivable transitions
			wasClicked: false, // Used to increase z-index during transition after this tile (or a child) is clicked
			hasExpanded: false, // Set to true after an expansion transition ends, and false upon collapse
				// Used to hide overflow on tile expansion, but not hide a sepSweptArea on subsequent transitions
			clickHoldTimer: 0, // Used to recognise click-and-hold events
			scrollOffset: 0, // Used to track scroll offset when displaying with overflow
			scrollThrottled: false,
		};
	},
	computed: {
		tolNode(): TolNode {
			return this.tolMap.get(this.layoutNode.name)!;
		},
		visibleChildren(): LayoutNode[] {
			// If not displaying with overflow, return layout node children
			let children = this.layoutNode.children;
			if (!this.isOverflownRoot){
				return children;
			}
			// Return visible children
			let firstIdx = children.length - 1;
			for (let i = 0; i < children.length; i++){
				if (children[i].pos[1] + children[i].dims[1] >= this.scrollOffset){
					firstIdx = i;
					break;
				}
			}
			let lastIdx = children.length;
			for (let i = firstIdx + 1; i < children.length; i++){
				if (children[i].pos[1] > this.scrollOffset + this.overflownDim){
					lastIdx = i;
					break;
				}
			}
			return children.slice(firstIdx, lastIdx);
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
			if (this.tolNode.commonName != null){
				let newName = capitalizeWords(this.tolNode.commonName)
				if (/^['"].*['"]$/.test(newName) == false){
					newName = "'" + newName + "'";
				}
				return newName;
			} else {
				return capitalizeWords(this.layoutNode.name);
			}
			return capitalizeWords(this.tolNode.commonName || this.layoutNode.name);
		},
		isOverflownRoot(): boolean {
			return this.overflownDim > 0 && !this.layoutNode.hidden && this.layoutNode.children.length > 0;
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
				boxShadow: this.boxShadow,
				borderRadius: this.uiOpts.borderRadius + 'px',
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
			if (!this.isLeaf){
				let borderR = this.uiOpts.borderRadius + 'px';
				if (this.layoutNode.sepSweptArea != null){
					borderR = this.layoutNode.sepSweptArea.sweptLeft ?
						`${borderR} ${borderR} ${borderR} 0` :
						`${borderR} 0 ${borderR} ${borderR}`;
				}
				layoutStyles.borderRadius = borderR;
			}
			if (this.isOverflownRoot){
				layoutStyles.width = (this.layoutNode.dims[0] + this.uiOpts.scrollGap) + 'px';
				layoutStyles.height = this.overflownDim + 'px';
				layoutStyles.overflow = 'hidden scroll';
			}
			if (this.layoutNode.hidden){
				layoutStyles.left = layoutStyles.top = layoutStyles.width = layoutStyles.height = '0';
				layoutStyles.visibility = 'hidden';
			}
			if (this.nonAbsPos){
				layoutStyles.position = 'static';
			}
			return layoutStyles;
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
				borderRadius: 'inherit',
			};
		},
		leafHeaderStyles(): Record<string,string> {
			let numChildren = this.tolNode.children.length;
			let headerColor = this.uiOpts.headerColor;
			for (let [threshold, color] of this.uiOpts.tipThresholds){
				if (numChildren >= threshold){
					headerColor = color;
				} else {
					break;
				}
			}
			return {
				height: (this.uiOpts.leafHeaderFontSz + this.uiOpts.leafTilePadding * 2) + 'px',
				padding: this.uiOpts.leafTilePadding + 'px',
				lineHeight: this.uiOpts.leafHeaderFontSz + 'px',
				fontSize: this.uiOpts.leafHeaderFontSz + 'px',
				fontStyle: this.tolNode.pSupport ? 'normal' : 'italic',
				color: headerColor,
				// For ellipsis
				overflow: 'hidden',
				textOverflow: 'ellipsis',
				whiteSpace: 'nowrap',
			};
		},
		nonleafStyles(): Record<string,string> {
			let styles = {
				position: 'static',
				width: '100%',
				height: '100%',
				backgroundColor: this.nonleafBgColor,
				borderRadius: 'inherit',
			};
			if (this.isOverflownRoot){
				styles.width = this.layoutNode.dims[0] + 'px';
				styles.height = this.layoutNode.dims[1] + 'px';
			}
			return styles;
		},
		nonleafHeaderStyles(): Record<string,string> {
			let styles: Record<string,string> = {
				position: 'static',
				height: this.lytOpts.headerSz + 'px',
				borderTopLeftRadius: 'inherit',
				borderTopRightRadius: 'inherit',
				backgroundColor: this.uiOpts.nonleafHeaderBgColor,
				fontStyle: this.tolNode.pSupport ? 'normal' : 'italic',
			};
			if (this.isOverflownRoot){
				styles = {
					...styles,
					position: 'sticky',
					top: '0',
					left: '0',
					borderTopRightRadius: '0',
					zIndex: '1',
					boxShadow: this.uiOpts.shadowNormal,
				};
			}
			return styles;
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
				let valChanged = newVal[0] != oldVal[0] || newVal[1] != oldVal[1];
				if (valChanged && this.uiOpts.tileChgDuration > 100 && !this.inTransition){
					this.inTransition = true;
				}
			},
			deep: true,
		},
		dims: {
			handler(newVal, oldVal){
				let valChanged = newVal[0] != oldVal[0] || newVal[1] != oldVal[1];
				if (valChanged && this.uiOpts.tileChgDuration > 100 && !this.inTransition){
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
			this.$emit('info-icon-click', this.layoutNode.name);
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
		onInnerInfoIconClick(nodeName: string){
			this.$emit('info-icon-click', nodeName);
		},
		onScroll(evt: Event){
			if (!this.scrollThrottled){
				this.scrollOffset = this.$el.scrollTop;
				setTimeout(() => {this.scrollThrottled = false;}, 300);
			}
		},
		// Other
		onTransitionEnd(evt: Event){
			if (this.inTransition){
				this.inTransition = false;
				this.wasClicked = false;
				this.hasExpanded = this.layoutNode.children.length > 0;
				// Scroll to any focused node
				if (this.isOverflownRoot){
					let focusedChild = this.layoutNode.children.find(n => n.hasFocus);
					if (focusedChild != null){
						let bottomY = focusedChild.pos[1] + focusedChild.dims[1] + this.lytOpts.tileSpacing;
						let scrollTop = Math.max(0, bottomY - this.overflownDim);
						this.$el.scrollTop = scrollTop;
					}
				}
			}
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
<div :style="styles" @transitionend="onTransitionEnd" @scroll="onScroll"> <!-- Need enclosing div for transitions -->
	<div v-if="isLeaf" :style="leafStyles"
		class="w-full h-full flex flex-col overflow-hidden" :class="{'hover:cursor-pointer': isExpandableLeaf}"
		@mouseenter="onMouseEnter" @mouseleave="onMouseLeave" @mousedown="onMouseDown" @mouseup="onMouseUp">
		<h1 :style="leafHeaderStyles">{{displayName}}</h1>
		<info-icon :style="[infoIconStyles, {marginTop: 'auto'}]"
			class="self-end text-white/10 hover:text-white hover:cursor-pointer"
			@click.stop="onInfoIconClick" @mousedown.stop @mouseup.stop/>
	</div>
	<div v-else :style="nonleafStyles" ref="nonleaf">
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
		<tile v-for="child in visibleChildren" :key="child.name"
			:layoutNode="child" :tolMap="tolMap" :lytOpts="lytOpts" :uiOpts="uiOpts" :overflownDim="overflownDim"
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
