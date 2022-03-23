<script lang="ts">
import {defineComponent, PropType} from 'vue';
import Tile from './Tile.vue';
import ParentBar from './ParentBar.vue';
import {TolNode, LayoutNode, initLayoutTree, tryLayout} from '../lib';
import type {LayoutOptions} from '../lib';
// Import paths lack a .ts or .js extension because .ts makes vue-tsc complain, and .js makes vite complain

// Obtain tree-of-life data
import tolRaw from '../tol.json';
function preprocessTol(node: any): any {
	// Add 'children' fields if missing
	if (node.children == null){
		node.children = [];
	} else {
		node.children.forEach(preprocessTol);
	}
	return node;
}
const tol: TolNode = preprocessTol(tolRaw);

// Configurable settings
const defaultLayoutOptions: LayoutOptions = {
	tileSpacing: 8, //px
	headerSz: 20, //px
	minTileSz: 50, //px
	maxTileSz: 200, //px
	layoutType: 'sweep', //'sqr' | 'rect' | 'sweep'
	rectMode: 'auto', //'horz' | 'vert' | 'linear' | 'auto'
	sweepMode: 'left', //'left' | 'top' | 'shorter' | 'auto'
	sweptNodesPrio: 'pow-2/3', //'linear' | 'sqrt' | 'pow-2/3'
	sweepingToParent: true,
};
const defaultOtherOptions = {
	transitionDuration: 300, //ms
	tileAreaOffset: 5, //px (space between root tile and display boundary)
	parentBarSz: defaultLayoutOptions.minTileSz * 2, //px (breadth of separated-parents area)
};

// Component holds a tree structure representing a subtree of 'tol' to be rendered
// Collects events about tile expansion/collapse and window-resize, and initiates relayout of tiles
export default defineComponent({
	props: {
		pos: {type: Array as unknown as PropType<[number,number]>, required: true},
		dims: {type: Array as unknown as PropType<[number,number]>, required: true},
	},
	data(){
		let layoutTree = initLayoutTree(tol, 0);
		return {
			layoutTree: layoutTree,
			activeRoot: layoutTree,
			layoutOptions: {...defaultLayoutOptions},
			...defaultOtherOptions,
		}
	},
	computed: {
		wideArea(){
			return this.dims[0] >= this.dims[1];
		},
		separatedParents(): LayoutNode[] | null {
			if (this.activeRoot == this.layoutTree){
				return null;
			}
			let parents = [];
			let node = this.activeRoot.parent;
			while (node != null){
				parents.push(node);
				node = node.parent;
			}
			return parents.reverse();
		},
		tileAreaPos(){
			let pos = [this.tileAreaOffset, this.tileAreaOffset] as [number, number];
			if (this.separatedParents != null){
				if (this.wideArea){
					pos[0] += this.parentBarSz;
				} else {
					pos[1] += this.parentBarSz;
				}
			}
			return pos;
		},
		tileAreaDims(){
			let dims = [
				this.dims[0] - this.tileAreaOffset*2,
				this.dims[1] - this.tileAreaOffset*2
			] as [number, number];
			if (this.separatedParents != null){
				if (this.wideArea){
					dims[0] -= this.parentBarSz;
				} else {
					dims[1] -= this.parentBarSz;
				}
			}
			return dims;
		},
		parentBarDims(){
			if (this.wideArea){
				return [this.parentBarSz, this.dims[1]] as [number, number];
			} else {
				return [this.dims[0], this.parentBarSz] as [number, number];
			}
		},
		styles(): Record<string,string> {
			return {
				position: 'absolute',
				left: this.pos[0] + 'px',
				top: this.pos[1] + 'px',
				width: this.dims[0] + 'px',
				height: this.dims[1] + 'px',
				backgroundColor: '#292524',
			};
		},
	},
	watch: {
		dims(newDims){
			tryLayout(this.activeRoot, this.tileAreaPos, this.tileAreaDims, this.layoutOptions, true);
		},
	},
	methods: {
		onInnerLeafClicked({layoutNode, domNode}: {layoutNode: LayoutNode, domNode: HTMLElement}){
			let success = tryLayout(this.activeRoot, this.tileAreaPos, this.tileAreaDims, this.layoutOptions, false,
				{type: 'expand', node: layoutNode});
			if (!success){
				// Trigger failure animation
				domNode.classList.remove('animate-expand-shrink');
				domNode.offsetWidth; // Triggers reflow
				domNode.classList.add('animate-expand-shrink');
			}
		},
		onInnerHeaderClicked({layoutNode, domNode}: {layoutNode: LayoutNode, domNode: HTMLElement}){
			let success = tryLayout(this.activeRoot, this.tileAreaPos, this.tileAreaDims, this.layoutOptions, false,
				{type: 'collapse', node: layoutNode});
			if (!success){
				// Trigger failure animation
				domNode.classList.remove('animate-shrink-expand');
				domNode.offsetWidth; // Triggers reflow
				domNode.classList.add('animate-shrink-expand');
			}
		},
		onInnerLeafDblClicked(layoutNode: LayoutNode){
			if (layoutNode == this.activeRoot){
				console.log('Ignored expand-to-view on root node');
				return;
			}
			LayoutNode.hideUpward(layoutNode);
			this.activeRoot = layoutNode;
			tryLayout(layoutNode, this.tileAreaPos, this.tileAreaDims, this.layoutOptions, true,
				{type: 'expand', node: layoutNode});
		},
		onInnerHeaderDblClicked(layoutNode: LayoutNode){
			if (layoutNode.parent == null){
				console.log('Ignored expand-to-view on root node');
				return;
			}
			LayoutNode.hideUpward(layoutNode);
			this.activeRoot = layoutNode;
			tryLayout(layoutNode, this.tileAreaPos, this.tileAreaDims, this.layoutOptions, true);
		},
	},
	created(){
		tryLayout(this.activeRoot, this.tileAreaPos, this.tileAreaDims, this.layoutOptions, true);
	},
	components: {
		Tile,
		ParentBar,
	},
});
</script>

<template>
<div :style="styles">
	<tile :layoutNode="layoutTree"
		:headerSz="layoutOptions.headerSz" :tileSpacing="layoutOptions.tileSpacing"
		:transitionDuration="transitionDuration"
		@leaf-clicked="onInnerLeafClicked" @header-clicked="onInnerHeaderClicked"
		@leaf-dbl-clicked="onInnerLeafDblClicked" @header-dbl-clicked="onInnerHeaderDblClicked"/>
	<parent-bar v-if="separatedParents != null" :pos="[0,0]" :dims="parentBarDims" :nodes="separatedParents"/>
</div>
</template>

<style>
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
