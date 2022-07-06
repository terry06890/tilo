<template>
<div :style="styles" @transitionend="onTransitionEnd" @scroll="onScroll"> <!-- Need enclosing div for transitions -->
	<div v-if="isLeaf" :class="[hasOneImage ? 'flex' : 'grid', {'hover:cursor-pointer': isExpandableLeaf}]"
		class="w-full h-full flex-col grid-cols-1" :style="leafStyles"
		@mouseenter="onMouseEnter" @mouseleave="onMouseLeave" @mousedown="onMouseDown" @mouseup="onMouseUp">
		<template v-if="hasOneImage">
			<h1 :style="leafHeaderStyles">{{displayName}}</h1>
			<info-icon v-if="infoIconDisabled" :style="infoIconStyles" :class="infoIconClasses"
				@click.stop="onInfoIconClick" @mousedown.stop @mouseup.stop/>
		</template>
		<template v-else>
			<div :style="leafFirstImgStyles" class="col-start-1 row-start-1"></div>
			<div :style="leafSecondImgStyles" class="col-start-1 row-start-1"></div>
			<h1 :style="leafHeaderStyles" class="col-start-1 row-start-1 z-10">{{displayName}}</h1>
			<info-icon v-if="infoIconDisabled" class="col-start-1 row-start-1 z-10"
				:style="infoIconStyles" :class="infoIconClasses"
				@click.stop="onInfoIconClick" @mousedown.stop @mouseup.stop/>
		</template>
	</div>
	<div v-else :style="nonleafStyles">
		<div v-if="showNonleafHeader" :style="nonleafHeaderStyles" class="flex hover:cursor-pointer"
			@mouseenter="onMouseEnter" @mouseleave="onMouseLeave" @mousedown="onMouseDown" @mouseup="onMouseUp">
			<h1 :style="nonleafHeaderTextStyles" class="grow">{{displayName}}</h1>
			<info-icon v-if="infoIconDisabled" :style="infoIconStyles" :class="infoIconClasses"
				@click.stop="onInfoIconClick" @mousedown.stop @mouseup.stop/>
		</div>
		<div :style="sepSweptAreaStyles" :class="sepSweptAreaHideEdgeClass">
			<div v-if="layoutNode.sepSweptArea?.sweptLeft === false"
				:style="nonleafHeaderStyles" class="flex hover:cursor-pointer"
				@mouseenter="onMouseEnter" @mouseleave="onMouseLeave" @mousedown="onMouseDown" @mouseup="onMouseUp">
				<h1 :style="nonleafHeaderTextStyles" class="grow">{{displayName}}</h1>
				<info-icon v-if="infoIconDisabled" :style="infoIconStyles" :class="infoIconClasses"
					@click.stop="onInfoIconClick" @mousedown.stop @mouseup.stop/>
			</div>
			<transition name="fadein">
				<div v-if="inFlash" class="absolute w-full h-full top-0 left-0 rounded-[inherit] bg-amber-500/70 z-20"/>
			</transition>
		</div>
		<tile v-for="child in visibleChildren" :key="child.name"
			:layoutNode="child" :tolMap="tolMap" :lytOpts="lytOpts" :uiOpts="uiOpts" :overflownDim="overflownDim"
			@leaf-click="onInnerLeafClick" @nonleaf-click="onInnerNonleafClick"
			@leaf-click-held="onInnerLeafClickHeld" @nonleaf-click-held="onInnerNonleafClickHeld"
			@info-click="onInnerInfoIconClick"/>
	</div>
	<transition name="fadein">
		<div v-if="inFlash" class="absolute w-full h-full top-0 left-0 rounded-[inherit] bg-amber-500/70"/>
	</transition>
</div>
</template>

<script lang="ts">
import {defineComponent, PropType} from 'vue';
import InfoIcon from './icon/InfoIcon.vue';
import {TolNode, TolMap} from '../tol';
import {LayoutNode, LayoutOptions} from '../layout';
import {getImagePath, UiOptions} from '../lib';
import {capitalizeWords} from '../util';

const scrimGradient = 'linear-gradient(to bottom, rgba(0,0,0,0.4), #0000 40%, #0000 60%, rgba(0,0,0,0.2) 100%)';

export default defineComponent({
	props: {
		layoutNode: {type: Object as PropType<LayoutNode>, required: true},
		tolMap: {type: Object as PropType<TolMap>, required: true},
		// Options
		lytOpts: {type: Object as PropType<LayoutOptions>, required: true},
		uiOpts: {type: Object as PropType<UiOptions>, required: true},
		// Other
		skipTransition: {type: Boolean, default: false},
		nonAbsPos: {type: Boolean, default: false},
			// For a leaf node, prevents usage of absolute positioning (used by AncestryBar)
		overflownDim: {type: Number, default: 0},
			// For a non-leaf node, display with overflow within area of this height
	},
	data(){
		return {
			// Mouse-event related
			clickHoldTimer: 0, // Used to recognise click-and-hold events
			highlight: false, // Used to draw a colored outline on mouse hover
			// Scroll-during-overflow related
			scrollOffset: 0, // Used to track scroll offset when displaying with overflow
			pendingScrollHdlr: 0, // Used for throttling updating of scrollOffset
			// Transition related
			inTransition: false, // Used to avoid content overlap and overflow during 'user-perceivable' transitions
			wasClicked: false, // Used to increase z-index during transition after this tile (or a child) is clicked
			hasExpanded: false, // Set to true after an expansion transition ends, and false upon collapse
				// Used to hide overflow on tile expansion, but not hide a sepSweptArea on subsequent transitions
			justUnhidden: false, // Used to allow overflow temporarily after being unhidden
			// Other
			inFlash: false, // Used to 'flash' the tile when focused
		};
	},
	computed: {
		tolNode(): TolNode {
			return this.tolMap.get(this.layoutNode.name)!;
		},
		visibleChildren(): LayoutNode[] { // Used to reduce slowdown from rendering many nodes
			let children = this.layoutNode.children;
			// If not displaying with overflow, return 'visible' layoutNode children
			if (!this.isOverflownRoot){
				return children.filter(n => !n.hidden || n.hiddenWithVisibleTip);
			}
			// Otherwise, return children within/near non-overflowing region
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
		// Convenience abbreviations
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
			let newName = capitalizeWords(this.tolNode.commonName || this.layoutNode.name);
			if (!this.tolNode.pSupport && this.tolNode.parent != null){
				newName += '*';
			}
			return newName;
		},
		hasOneImage(): boolean {
			return !Array.isArray(this.tolNode.imgName);
		},
		isOverflownRoot(): boolean {
			return this.overflownDim > 0 && !this.layoutNode.hidden && this.layoutNode.children.length > 0;
		},
		hasFocusedChild(): boolean {
			return this.layoutNode.children.some(n => n.hasFocus);
		},
		infoIconDisabled(): boolean {
			return !this.uiOpts.disabledActions.has('tileInfo');
		},
		// For styling
		nonleafBgColor(): string {
			let colorArray = this.uiOpts.nonleafBgColors;
			return colorArray[this.layoutNode.depth % colorArray.length];
		},
		boxShadow(): string {
			if (this.highlight){
				return this.uiOpts.shadowHovered;
			} else if (this.layoutNode.hasFocus && !this.inTransition){
				return this.uiOpts.shadowFocused;
			} else {
				return this.uiOpts.shadowNormal;
			}
		},
		fontSz(): number {
			return 0.8 * this.lytOpts.headerSz;
		},
		styles(): Record<string,string> {
			let layoutStyles = {
				position: 'absolute',
				left: this.layoutNode.pos[0] + 'px',
				top: this.layoutNode.pos[1] + 'px',
				width: this.layoutNode.dims[0] + 'px',
				height: this.layoutNode.dims[1] + 'px',
				borderRadius: this.uiOpts.borderRadius + 'px',
				boxShadow: this.boxShadow,
				visibility: 'visible',
				// Transition related
				transitionDuration: (this.skipTransition ? 0 : this.uiOpts.transitionDuration) + 'ms',
				transitionProperty: 'left, top, width, height, visibility',
				transitionTimingFunction: 'ease-out',
				zIndex: this.inTransition && this.wasClicked ? '1' : '0',
				overflow: (this.inTransition && !this.isLeaf && !this.hasExpanded && !this.justUnhidden) ?
					'hidden' : 'visible',
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
			let styles: Record<string,string> = {
				borderRadius: 'inherit',
			};
			if (this.hasOneImage){
				styles = {
					...styles,
					backgroundImage: this.tolNode.imgName != null ?
						`${scrimGradient},url('${getImagePath(this.tolNode.imgName as string)}')` :
						'none',
					backgroundColor: this.uiOpts.bgColorDark,
					backgroundSize: 'cover',
				};
			}
			return styles;
		},
		leafHeaderStyles(): Record<string,string> {
			let numChildren = this.tolNode.children.length;
			let textColor = this.uiOpts.textColor;
			for (let [threshold, color] of this.uiOpts.childQtyColors){
				if (numChildren >= threshold){
					textColor = color;
				} else {
					break;
				}
			}
			let screenSz = this.uiOpts.breakpoint;
			return {
				height: this.lytOpts.headerSz + 'px',
				padding: `0 ${(this.lytOpts.headerSz - this.fontSz)}px`,
				lineHeight: this.lytOpts.headerSz + 'px',
				fontSize: this.fontSz + 'px',
				color: textColor,
				// For ellipsis
				overflow: 'hidden',
				textOverflow: 'ellipsis',
				whiteSpace: 'nowrap',
			};
		},
		leafFirstImgStyles(): Record<string,string> {
			return this.leafSubImgStyles(0);
		},
		leafSecondImgStyles(): Record<string,string> {
			return this.leafSubImgStyles(1);
		},
		nonleafStyles(): Record<string,string> {
			let styles = {
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
				backgroundColor: this.uiOpts.nonleafHeaderColor,
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
				fontSize: this.fontSz + 'px',
				textAlign: 'center',
				color: this.uiOpts.textColor,
				// For ellipsis
				overflow: 'hidden',
				textOverflow: 'ellipsis',
				whiteSpace: 'nowrap',
			};
		},
		sepSweptAreaStyles(): Record<string,string> {
			let borderR = this.uiOpts.borderRadius + 'px';
			let styles = {
				position: 'absolute',
				backgroundColor: this.nonleafBgColor,
				boxShadow: this.boxShadow,
				transitionDuration: this.uiOpts.transitionDuration + 'ms',
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
		sepSweptAreaHideEdgeClass(): string {
			if (this.layoutNode.sepSweptArea == null){
				return '';
			} else if (this.layoutNode.sepSweptArea.sweptLeft){
				return 'hide-right-edge';
			} else {
				return 'hide-top-edge';
			}
		},
		infoIconStyles(): Record<string,string> {
			let size = (this.lytOpts.headerSz * 0.85);
			let marginSz = (this.lytOpts.headerSz - size);
			return {
				width: size + 'px',
				height: size + 'px',
				minWidth: size + 'px',
				minHeight: size + 'px',
				margin: this.isLeaf ? `auto ${marginSz}px ${marginSz}px auto` : `auto ${marginSz}px`,
			};
		},
		infoIconClasses(): string {
			return 'text-white/30 hover:text-white hover:cursor-pointer';
		},
		// For watching layoutNode data
		pos(){
			return this.layoutNode.pos;
		},
		dims(){
			return this.layoutNode.dims;
		},
		hidden(){
			return this.layoutNode.hidden;
		},
		hasFocus(){
			return this.layoutNode.hasFocus;
		},
		failFlag(){
			return this.layoutNode.failFlag;
		},
	},
	watch: {
		// For setting transition state (allows external triggering, like via search and auto-mode)
		pos: {
			handler(newVal: [number, number], oldVal: [number, number]){
				let valChanged = newVal[0] != oldVal[0] || newVal[1] != oldVal[1];
				if (valChanged && this.uiOpts.transitionDuration > 100 && !this.inTransition){
					this.inTransition = true;
				}
			},
			deep: true,
		},
		dims: {
			handler(newVal: [number, number], oldVal: [number, number]){
				let valChanged = newVal[0] != oldVal[0] || newVal[1] != oldVal[1];
				if (valChanged && this.uiOpts.transitionDuration > 100 && !this.inTransition){
					this.inTransition = true;
				}
			},
			deep: true,
		},
		// For externally triggering fail animations (used by search and auto-mode)
		failFlag(){
			this.triggerAnimation(this.isLeaf ? 'animate-expand-shrink' : 'animate-shrink-expand');
		},
		// Scroll to focused child if overflownRoot
		hasFocusedChild(newVal: boolean, oldVal: boolean){
			if (newVal && this.isOverflownRoot){
				let focusedChild = this.layoutNode.children.find(n => n.hasFocus)!
				let bottomY = focusedChild.pos[1] + focusedChild.dims[1] + this.lytOpts.tileSpacing;
				let scrollTop = Math.max(0, bottomY - (this.overflownDim / 2)); // No need to manually cap at max
				this.$el.scrollTop = scrollTop;
			}
		},
		// Allow overflow temporarily after being unhidden
		hidden(newVal: boolean, oldVal: boolean){
			if (oldVal && !newVal){
				this.justUnhidden = true;
				setTimeout(() => {this.justUnhidden = false;}, this.uiOpts.transitionDuration + 100);
			}
		},
		// Used to 'flash' the tile when focused
		hasFocus(newVal: boolean, oldVal: boolean){
			if (newVal != oldVal && newVal){
				this.inFlash = true;
				setTimeout(() => {this.inFlash = false;}, this.uiOpts.transitionDuration);
			}
		},
	},
	methods: {
		// Click handling
		onMouseDown(): void {
			this.highlight = false;
			if (!this.uiOpts.touchDevice){
				// Wait for a mouseup or click-hold
				clearTimeout(this.clickHoldTimer);
				this.clickHoldTimer = setTimeout(() => {
					this.clickHoldTimer = 0;
					this.onClickHold();
				}, this.uiOpts.clickHoldDuration);
			} else {
				// Wait for or recognise a double-click
				if (this.clickHoldTimer == 0){
					this.clickHoldTimer = setTimeout(() => {
						this.clickHoldTimer = 0;
						this.onClick();
					}, this.uiOpts.clickHoldDuration);
				} else {
					clearTimeout(this.clickHoldTimer)
					this.clickHoldTimer = 0;
					this.onDblClick();
				}
			}
		},
		onMouseUp(): void {
			if (!this.uiOpts.touchDevice){
				if (this.clickHoldTimer > 0){
					clearTimeout(this.clickHoldTimer);
					this.clickHoldTimer = 0;
					this.onClick();
				}
			}
		},
		onClick(): void {
			if (this.isLeaf && !this.isExpandableLeaf){
				console.log('Ignored click on non-expandable node');
				return;
			}
			this.wasClicked = true;
			this.$emit(this.isLeaf ? 'leaf-click' : 'nonleaf-click', this.layoutNode);
		},
		onClickHold(): void {
			if (this.isLeaf && !this.isExpandableLeaf){
				console.log('Ignored click-hold on non-expandable node');
				return;
			}
			this.$emit(this.isLeaf ? 'leaf-click-held' : 'nonleaf-click-held', this.layoutNode);
		},
		onDblClick(): void {
			this.onClickHold();
		},
		onInfoIconClick(evt: Event): void {
			this.$emit('info-click', this.layoutNode.name);
		},
		// Mouse-hover handling
		onMouseEnter(evt: Event): void {
			if ((!this.isLeaf || this.isExpandableLeaf) && !this.inTransition){
				this.highlight = true;
			}
		},
		onMouseLeave(evt: Event): void {
			this.highlight = false;
		},
		// Child event propagation
		onInnerLeafClick(node: LayoutNode): void {
			this.wasClicked = true;
			this.$emit('leaf-click', node);
		},
		onInnerNonleafClick(node: LayoutNode): void {
			this.wasClicked = true;
			this.$emit('nonleaf-click', node);
		},
		onInnerLeafClickHeld(node: LayoutNode): void {
			this.$emit('leaf-click-held', node);
		},
		onInnerNonleafClickHeld(node: LayoutNode): void {
			this.$emit('nonleaf-click-held', node);
		},
		onInnerInfoIconClick(nodeName: string): void {
			this.$emit('info-click', nodeName);
		},
		onScroll(evt: Event): void {
			if (this.pendingScrollHdlr == 0){
				this.pendingScrollHdlr = setTimeout(() => {
					this.scrollOffset = this.$el.scrollTop;
					this.pendingScrollHdlr = 0;
				}, this.uiOpts.animationDelay);
			}
		},
		// Other
		leafSubImgStyles(idx: number): Record<string,string> {
			let [w, h] = this.layoutNode.dims;
			return {
				width: '100%',
				height: '100%',
				// Image (and scrims)
				backgroundImage: (this.tolNode.imgName![idx]! != null) ?
					`${scrimGradient},url('${getImagePath(this.tolNode.imgName![idx]! as string)}')` :
					'none',
				backgroundColor: this.uiOpts.bgColorDark,
				backgroundSize: '125%',
				borderRadius: 'inherit',
				clipPath: idx == 0 ? 'polygon(0 0, 100% 0, 0 100%)' : 'polygon(100% 0, 0 100%, 100% 100%)',
				backgroundPosition: idx == 0 ? `${-w/4}px ${-h/4}px` : '0px 0px',
			};
		},
		onTransitionEnd(evt: Event){
			if (this.inTransition){
				this.inTransition = false;
				this.wasClicked = false;
				this.hasExpanded = this.layoutNode.children.length > 0;
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
	emits: ['leaf-click', 'nonleaf-click', 'leaf-click-held', 'nonleaf-click-held', 'info-click', ],
});
</script>

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
</style>
