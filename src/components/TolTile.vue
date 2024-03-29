<template>
<div :style="styles" @scroll="onScroll" ref="rootRef">
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
			<transition name="fadeout">
				<div v-if="inFlash" class="absolute w-full h-full top-0 left-0 rounded-[inherit] bg-amber-500/70 z-20"/>
			</transition>
		</div>

		<tol-tile v-for="child in visibleChildren" :key="child.name"
			:layoutNode="child" :tolMap="tolMap" :overflownDim="overflownDim"
			@leaf-click="onInnerLeafClick" @nonleaf-click="onInnerNonleafClick"
			@leaf-click-held="onInnerLeafClickHeld" @nonleaf-click-held="onInnerNonleafClickHeld"
			@info-click="onInnerInfoIconClick"/>
	</div>

	<transition name="fadeout">
		<div v-if="inFlash" :style="{top: scrollOffset + 'px'}"
			class="absolute w-full h-full left-0 rounded-[inherit] bg-amber-500/70"/>
	</transition>
</div>
</template>

<script setup lang="ts">
import {ref, computed, watch, PropType} from 'vue';

import InfoIcon from './icon/InfoIcon.vue';
import {TolMap} from '../tol';
import {LayoutNode} from '../layout';
import {getImagePath} from '../lib';
import {capitalizeWords} from '../util';
import {useStore} from '../store';

const SCRIM_GRADIENT = 'linear-gradient(to bottom, rgba(0,0,0,0.4), #0000 40%, #0000 60%, rgba(0,0,0,0.2) 100%)';

const rootRef = ref(null as HTMLDivElement | null);

const store = useStore();

const props = defineProps({
	layoutNode: {type: Object as PropType<LayoutNode>, required: true},
	tolMap: {type: Object as PropType<TolMap>, required: true},
	// Other
	skipTransition: {type: Boolean, default: false},
	nonAbsPos: {type: Boolean, default: false},
		// For a leaf node, prevents usage of absolute positioning (used by AncestryBar)
	overflownDim: {type: Number, default: 0},
		// For a non-leaf node, display with overflow within area of this height
});

const emit = defineEmits(['leaf-click', 'nonleaf-click', 'leaf-click-held', 'nonleaf-click-held', 'info-click']);

// ========== Data computed from props ==========

const tolNode = computed(() => props.tolMap.get(props.layoutNode.name)!);
const visibleChildren = computed((): LayoutNode[] => { // Used to reduce slowdown from rendering many nodes
	let children = props.layoutNode.children;
	// If not displaying with overflow, return 'visible' layoutNode children
	if (!isOverflownRoot.value){
		return children.filter(n => !n.hidden || n.hiddenWithVisibleTip);
	}
	// Otherwise, return children within/near non-overflowing region
	let firstIdx = children.length - 1;
	for (let i = 0; i < children.length; i++){
		if (children[i].pos[1] + children[i].dims[1] >= scrollOffset.value){
			firstIdx = i;
			break;
		}
	}
	let lastIdx = children.length;
	for (let i = firstIdx + 1; i < children.length; i++){
		if (children[i].pos[1] > scrollOffset.value + props.overflownDim){
			lastIdx = i;
			break;
		}
	}
	return children.slice(firstIdx, lastIdx);
});
const isLeaf = computed(() => props.layoutNode.children.length == 0);
const isExpandableLeaf = computed(() => isLeaf.value && tolNode.value.children.length > 0);
const showNonleafHeader = computed(() =>
	(props.layoutNode.showHeader && props.layoutNode.sepSweptArea == null) ||
		(props.layoutNode.sepSweptArea != null && props.layoutNode.sepSweptArea.sweptLeft)
);
const displayName = computed((): string => {
	let newName = capitalizeWords(tolNode.value.commonName || props.layoutNode.name);
	if (!tolNode.value.pSupport && tolNode.value.parent != null){
		newName += '*';
	}
	return newName;
});
const hasOneImage = computed(() => !Array.isArray(tolNode.value.imgName));
const isOverflownRoot = computed(() =>
	props.overflownDim > 0 && !props.layoutNode.hidden && props.layoutNode.children.length > 0
);
const hasFocusedChild = computed(() => props.layoutNode.children.some(n => n.hasFocus));
const infoIconDisabled = computed(() => !store.disabledActions.has('tileInfo'));

// ========== Click/hold handling ==========

const clickHoldTimer = ref(0); // Used to recognise click-and-hold events

function onMouseDown(): void {
	highlight.value = false;
	if (!store.touchDevice){
		// Wait for a mouseup or click-hold
		clearTimeout(clickHoldTimer.value);
		clickHoldTimer.value = setTimeout(() => {
			clickHoldTimer.value = 0;
			onClickHold();
		}, store.clickHoldDuration);
	} else {
		// Wait for or recognise a double-click
		if (clickHoldTimer.value == 0){
			clickHoldTimer.value = setTimeout(() => {
				clickHoldTimer.value = 0;
				onClick();
			}, store.clickHoldDuration);
		} else {
			clearTimeout(clickHoldTimer.value)
			clickHoldTimer.value = 0;
			onDblClick();
		}
	}
}

function onMouseUp(): void {
	if (!store.touchDevice){
		if (clickHoldTimer.value > 0){
			clearTimeout(clickHoldTimer.value);
			clickHoldTimer.value = 0;
			onClick();
		}
	}
}

// ========== Click-action handling ==========

const wasClicked = ref(false); // Used to increase z-index during transition after this tile (or a child) is clicked

function onClick(): void {
	if (isLeaf.value && !isExpandableLeaf.value){
		console.log('Ignored click on non-expandable node');
		return;
	}
	wasClicked.value = true;
	if (isLeaf.value){
		emit('leaf-click', props.layoutNode, onExpandFail);
	} else {
		emit('nonleaf-click', props.layoutNode, onCollapseFail);
	}
}

function onClickHold(): void {
	if (isLeaf.value && !isExpandableLeaf.value){
		console.log('Ignored click-hold on non-expandable node');
		return;
	}
	if (isLeaf.value){
		emit('leaf-click-held', props.layoutNode, onExpandFail);
	} else {
		emit('nonleaf-click-held', props.layoutNode, onCollapseFail);
	}
}

function onDblClick(): void {
	onClickHold();
}

function onInfoIconClick(): void {
	emit('info-click', props.layoutNode.name);
}

// ========== Child click-action propagation ==========

function onInnerLeafClick(node: LayoutNode, onFail: () => void): void {
	wasClicked.value = true;
	emit('leaf-click', node, onFail);
}

function onInnerNonleafClick(node: LayoutNode, onFail: () => void): void {
	wasClicked.value = true;
	emit('nonleaf-click', node, onFail);
}

function onInnerLeafClickHeld(node: LayoutNode, onFail: () => void): void {
	emit('leaf-click-held', node, onFail);
}

function onInnerNonleafClickHeld(node: LayoutNode, onFail: () => void): void {
	emit('nonleaf-click-held', node, onFail);
}

function onInnerInfoIconClick(nodeName: string): void {
	emit('info-click', nodeName);
}

// ========== Mouse-hover handling ==========

const highlight = ref(false); // Used to draw a colored outline on mouse hover

function onMouseEnter(): void {
	if ((!isLeaf.value || isExpandableLeaf.value) && !inTransition.value){
		highlight.value = true;
	}
}

function onMouseLeave(): void {
	highlight.value = false;
}

// ========== Scrolling if overflownRoot ==========

const scrollOffset = ref(0); // Used to track scroll offset when displaying with overflow
const pendingScrollHdlr = ref(0); // Used for throttling updating of scrollOffset

function onScroll(): void {
	if (pendingScrollHdlr.value == 0){
		pendingScrollHdlr.value = setTimeout(() => {
			if (rootRef.value != null){
				scrollOffset.value = rootRef.value!.scrollTop;
			}
			pendingScrollHdlr.value = 0;
		}, store.animationDelay);
	}
}

// Without this, sometimes, if auto-mode enters an overflowing node, scrolls down, collapses, then stops,
// and the node is then manually expanded, the scroll will be 0, and some nodes will be hidden
watch(isLeaf, onScroll);

// Scroll to focused child if overflownRoot
watch(hasFocusedChild, (newVal: boolean) => {
	if (newVal && isOverflownRoot.value){
		let focusedChild = props.layoutNode.children.find(n => n.hasFocus)!
		let bottomY = focusedChild.pos[1] + focusedChild.dims[1] + store.lytOpts.tileSpacing;
		let scrollTop = Math.max(0, bottomY - (props.overflownDim / 2)); // No need to manually cap at max
		rootRef.value!.scrollTop = scrollTop;
	}
});

// ========== Transition related ==========

const inTransition = ref(false); // Used to avoid content overlap and overflow during 'user-perceivable' transitions
const hasExpanded = ref(false); // Set to true after an expansion transition ends, and false upon collapse
	// Used to hide overflow on tile expansion, but not hide a sepSweptArea on subsequent transitions

function onTransitionEnd(){
	if (inTransition.value){
		inTransition.value = false;
		wasClicked.value = false;
		hasExpanded.value = props.layoutNode.children.length > 0;
	}
}

// For setting transition state (allows external triggering, like via search and auto-mode)
watch(() => props.layoutNode.pos, (newVal: [number, number], oldVal: [number, number]) => {
	let valChanged = newVal[0] != oldVal[0] || newVal[1] != oldVal[1];
	if (valChanged && store.transitionDuration > 100 && !inTransition.value){
		inTransition.value = true;
		setTimeout(onTransitionEnd, store.transitionDuration);
	}
});
watch(() => props.layoutNode.dims, (newVal: [number, number], oldVal: [number, number]) => {
	let valChanged = newVal[0] != oldVal[0] || newVal[1] != oldVal[1];
	if (valChanged && store.transitionDuration > 100 && !inTransition.value){
		inTransition.value = true;
		setTimeout(onTransitionEnd, store.transitionDuration);
	}
});

// For externally triggering fail animations (used by search and auto-mode)
function triggerAnimation(animation: string){
	let el = rootRef.value!;
	el.classList.remove(animation);
	el.offsetWidth; // Triggers reflow
	el.classList.add(animation);
}

function onExpandFail(){
	triggerAnimation('animate-expand-shrink');
}

function onCollapseFail(){
	triggerAnimation('animate-shrink-expand');
}

// ========== For 'flashing' the tile when focused ==========

const inFlash = ref(false); // Used to 'flash' the tile when focused

watch(() => props.layoutNode.hasFocus, (newVal: boolean, oldVal: boolean) => {
	if (newVal != oldVal && newVal){
		inFlash.value = true;
		setTimeout(() => {inFlash.value = false;}, 300);
	}
});

// ========== For temporarily enabling overflow after being unhidden ==========

const justUnhidden = ref(false); // Used to allow overflow temporarily after being unhidden

watch(() => props.layoutNode.hidden, (newVal: boolean, oldVal: boolean) => {
	if (oldVal && !newVal){
		justUnhidden.value = true;
		setTimeout(() => {justUnhidden.value = false}, store.transitionDuration + 100);
	}
});

// ========== For styling ==========

const nonleafBgColor = computed(() => {
	let colorArray = store.nonleafBgColors;
	return colorArray[props.layoutNode.depth % colorArray.length];
});

const boxShadow = computed((): string => {
	if (highlight.value){
		return store.shadowHovered;
	} else if (props.layoutNode.hasFocus && !inTransition.value){
		return store.shadowFocused;
	} else {
		return store.shadowNormal;
	}
});

const fontSz = computed((): number => {
	// These values are a compromise between dynamic font size and code simplicity
	if (props.layoutNode.dims[0] >= 150){
		return store.lytOpts.headerSz * 0.8;
	} else if (props.layoutNode.dims[0] >= 80){
		return store.lytOpts.headerSz * 0.7;
	} else {
		return store.lytOpts.headerSz * 0.6;
	}
});

const styles = computed((): Record<string,string> => {
	let layoutStyles = {
		position: 'absolute',
		left: props.layoutNode.pos[0] + 'px',
		top: props.layoutNode.pos[1] + 'px',
		width: props.layoutNode.dims[0] + 'px',
		height: props.layoutNode.dims[1] + 'px',
		borderRadius: store.borderRadius + 'px',
		boxShadow: boxShadow.value,
		visibility: 'visible',
		// Transition related
		transitionDuration: (props.skipTransition ? 0 : store.transitionDuration) + 'ms',
		transitionProperty: 'left, top, width, height, visibility',
		transitionTimingFunction: 'ease-out',
		zIndex: inTransition.value && wasClicked.value ? '1' : '0',
		overflow: (inTransition.value && !isLeaf.value && !hasExpanded.value && !justUnhidden.value) ?
			'hidden' : 'visible',
		// CSS variables
		'--nonleafBgColor': nonleafBgColor.value,
		'--tileSpacing': store.lytOpts.tileSpacing + 'px',
	};
	if (!isLeaf.value){
		let borderR = store.borderRadius + 'px';
		if (props.layoutNode.sepSweptArea != null){
			borderR = props.layoutNode.sepSweptArea.sweptLeft ?
				`${borderR} ${borderR} ${borderR} 0` :
				`${borderR} 0 ${borderR} ${borderR}`;
		}
		layoutStyles.borderRadius = borderR;
	}
	if (isOverflownRoot.value){
		layoutStyles.width = (props.layoutNode.dims[0] + store.scrollGap) + 'px';
		layoutStyles.height = props.overflownDim + 'px';
		layoutStyles.overflow = 'hidden scroll';
	}
	if (props.layoutNode.hidden){
		layoutStyles.left = layoutStyles.top = layoutStyles.width = layoutStyles.height = '0';
		layoutStyles.visibility = 'hidden';
	}
	if (props.nonAbsPos){
		layoutStyles.position = 'static';
	}
	return layoutStyles;
});

const leafStyles = computed((): Record<string,string> => {
	let styles: Record<string,string> = {
		borderRadius: 'inherit',
	};
	if (hasOneImage.value){
		styles = {
			...styles,
			backgroundImage: tolNode.value.imgName != null ?
				`${SCRIM_GRADIENT},url('${getImagePath(tolNode.value.imgName as string)}')` :
				'none',
			backgroundColor: store.color.bgDark,
			backgroundSize: 'cover',
		};
	}
	return styles;
});

const leafHeaderStyles = computed((): Record<string,string> => {
	let numChildren = tolNode.value.children.length;
	let textColor = store.color.text;
	for (let [threshold, color] of store.childQtyColors){
		if (numChildren >= threshold){
			textColor = color;
		} else {
			break;
		}
	}
	return {
		lineHeight: (fontSz.value * 1.3) + 'px',
		fontSize: fontSz.value + 'px',
		paddingLeft: (fontSz.value * 0.2) + 'px',
		color: textColor,
		// For ellipsis
		overflow: 'hidden',
		textOverflow: 'ellipsis',
		whiteSpace: 'nowrap',
	};
});

function leafSubImgStyles(idx: number): Record<string,string> {
	let [w, h] = props.layoutNode.dims;
	return {
		width: '100%',
		height: '100%',
		// Image (and scrims)
		backgroundImage: (tolNode.value.imgName![idx]! != null) ?
			`${SCRIM_GRADIENT},url('${getImagePath(tolNode.value.imgName![idx]! as string)}')` :
			'none',
		backgroundColor: store.color.bgDark,
		backgroundSize: '125%',
		borderRadius: 'inherit',
		clipPath: (idx == 0) ? 'polygon(0 0, 100% 0, 0 100%)' : 'polygon(100% 0, 0 100%, 100% 100%)',
		backgroundPosition: (idx == 0) ? `${-w/4}px ${-h/4}px` : '0px 0px',
	};
}

const leafFirstImgStyles = computed(() => leafSubImgStyles(0));
const leafSecondImgStyles = computed(() => leafSubImgStyles(1));

const nonleafStyles = computed((): Record<string,string> => {
	let styles = {
		width: '100%',
		height: '100%',
		backgroundColor: nonleafBgColor.value,
		borderRadius: 'inherit',
	};
	if (isOverflownRoot.value){
		styles.width = props.layoutNode.dims[0] + 'px';
		styles.height = props.layoutNode.dims[1] + 'px';
	}
	return styles;
});

const nonleafHeaderStyles = computed((): Record<string,string> => {
	let styles: Record<string,string> = {
		position: 'static',
		height: store.lytOpts.headerSz + 'px',
		borderTopLeftRadius: 'inherit',
		borderTopRightRadius: 'inherit',
		backgroundColor: store.nonleafHeaderColor,
	};
	if (isOverflownRoot.value){
		styles = {
			...styles,
			position: 'sticky',
			top: '0',
			left: '0',
			borderTopRightRadius: '0',
			zIndex: '1',
			boxShadow: store.shadowNormal,
		};
	}
	return styles;
});

const nonleafHeaderTextStyles = computed(() => ({
	lineHeight: (fontSz.value * 1.3) + 'px',
	fontSize: fontSz.value + 'px',
	paddingLeft: (fontSz.value * 0.2) + 'px',
	textAlign: 'center',
	color: store.color.text,
	// For ellipsis
	overflow: 'hidden',
	textOverflow: 'ellipsis',
	whiteSpace: 'nowrap',
}));

const sepSweptAreaStyles = computed((): Record<string,string> => {
	let borderR = store.borderRadius + 'px';
	let styles = {
		position: 'absolute',
		backgroundColor: nonleafBgColor.value,
		boxShadow: boxShadow.value,
		transitionDuration: store.transitionDuration + 'ms',
		transitionProperty: 'left, top, width, height, visibility',
		transitionTimingFunction: 'ease-out',
	};
	let area = props.layoutNode.sepSweptArea;
	if (!props.layoutNode.hidden && area != null){
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
			top: store.lytOpts.headerSz + 'px',
			width: '0',
			height: '0',
			borderRadius: borderR,
		};
	}
});

const sepSweptAreaHideEdgeClass = computed((): string => {
	if (props.layoutNode.sepSweptArea == null){
		return '';
	} else if (props.layoutNode.sepSweptArea.sweptLeft){
		return 'hide-right-edge';
	} else {
		return 'hide-top-edge';
	}
});

const infoIconStyles = computed((): Record<string,string> => {
	let size = (store.lytOpts.headerSz * 0.85);
	let marginSz = (store.lytOpts.headerSz - size);
	return {
		width: size + 'px',
		height: size + 'px',
		minWidth: size + 'px',
		minHeight: size + 'px',
		margin: isLeaf.value ? `auto ${marginSz}px ${marginSz}px auto` : `auto ${marginSz}px auto 0`,
	};
});

const infoIconClasses = 'text-white/30 hover:text-white hover:cursor-pointer';
</script>

<style scoped>
/* For making a parent-swept-area div look continuous with the tile div */
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
