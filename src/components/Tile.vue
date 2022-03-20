<script lang="ts">
import {defineComponent, PropType} from 'vue';
import {LayoutNode} from '../lib';

// Configurable settings
const defaultOptions = {
	borderRadius: 5, //px
	shadowNormal: '0 0 2px black',
	shadowWithHover: '0 0 1px 2px greenyellow',
	// For leaf tiles
	leafHeaderX: 4, //px
	leafHeaderY: 4, //px
	leafHeaderFontSz: 15, //px
	leafHeaderColor: '#fafaf9',
	expandableLeafHeaderColor: 'greenyellow', //yellow, greenyellow, turquoise,
	// For non-leaf tile-groups
	nonLeafBgColors: ['#44403c', '#57534e'], //tiles at depth N use the Nth color, repeating from the start as needed
	nonLeafHeaderFontSz: 15, //px
	nonLeafHeaderColor: '#fafaf9',
	nonLeafHeaderBgColor: '#1c1917',
};

// Component holds a tree-node structure representing a tile or tile-group to be rendered
export default defineComponent({
	props: {
		layoutNode: {type: Object as PropType<LayoutNode>, required: true},
		isRoot: {type: Boolean, default: false},
		// Settings from parent component
		headerSz: {type: Number, required: true},
		tileSpacing: {type: Number, required: true},
		transitionDuration: {type: Number, required: true},
	},
	data(){
		return {
			options: defaultOptions,
			// Used during transitions and to emulate/show an apparently-joined div
			zIdx: 0,
			overflow: 'visible',
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
				left: this.isRoot ? '50%' : this.layoutNode.pos[0] + 'px',
				top: this.isRoot ? '50%' : this.layoutNode.pos[1] + 'px',
				transform: this.isRoot ? 'translate(-50%, -50%)' : 'none',
				width: this.layoutNode.dims[0] + 'px',
				height: this.layoutNode.dims[1] + 'px',
				// Other bindings
				transitionDuration: this.transitionDuration + 'ms',
				zIndex: String(this.zIdx),
				overflow: String(this.overflow),
				// Static styles
				transitionProperty: 'left, top, width, height',
				transitionTimingFunction: 'ease-out',
				// CSS variables
				'--nonLeafBgColor': this.nonLeafBgColor,
				'--tileSpacing': this.tileSpacing + 'px',
				'--shadowNormal': this.options.shadowNormal,
				'--shadowWithHover': this.options.shadowWithHover,
			};
		},
		leafStyles(): Record<string,string> {
			return {
				width: '100%',
				height: '100%',
				backgroundImage: 'url(\'/img/' + this.layoutNode.tolNode.name.replaceAll('\'', '\\\'') + '.png\')',
				backgroundSize: 'cover',
				borderRadius: this.options.borderRadius + 'px',
			};
		},
		leafHeaderStyles(): Record<string,string> {
			return {
				position: 'absolute',
				left: this.options.leafHeaderX + 'px',
				top: this.options.leafHeaderY + 'px',
				maxWidth: (this.layoutNode.dims[0] - this.options.leafHeaderX * 2) + 'px',
				height: this.options.leafHeaderFontSz + 'px',
				lineHeight: this.options.leafHeaderFontSz + 'px',
				fontSize: this.options.leafHeaderFontSz + 'px',
				color: this.isExpandable ? this.options.expandableLeafHeaderColor : this.options.leafHeaderColor,
				// For ellipsis
				overflow: 'hidden',
				textOverflow: 'ellipsis',
				whiteSpace: 'nowrap',
			};
		},
		nonLeafStyles(): Record<string,string> {
			let temp = {
				width: '100%',
				height: '100%',
				backgroundColor: this.nonLeafBgColor,
				borderRadius: this.options.borderRadius + 'px',
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
				transitionDuration: this.transitionDuration + 'ms',
				transitionProperty: 'left, top, width, height',
				transitionTimingFunction: 'ease-out',
			};
			let area = this.layoutNode.sepSweptArea;
			if (area == null){
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
		// For tile expansion and collapse
		onLeafClick(){
			this.$emit('leaf-clicked', {layoutNode: this.layoutNode, domNode: this.$el});
			(this.$refs.leaf as Element).classList.replace('shadow-highlight', 'shadow-normal');
			// Temporary changes during transition
			this.zIdx = 1;
			this.overflow = 'hidden';
			setTimeout(() => {
				this.zIdx = 0;
				this.overflow = 'visible';
			}, this.transitionDuration);
		},
		onInnerLeafClicked(data: {layoutNode: LayoutNode, domNode: HTMLElement}){
			this.$emit('leaf-clicked', data);
		},
		onHeaderClick(){
			this.$emit('header-clicked', {layoutNode: this.layoutNode, domNode: this.$el});
			(this.$refs.nonLeaf as Element).classList.replace('shadow-highlight', 'shadow-normal');
			// Temporary changes during transition
			this.zIdx = 1;
			this.overflow = 'hidden';
			setTimeout(() => {
				this.zIdx = 0;
				this.overflow = 'visible';
			}, this.transitionDuration);
		},
		onInnerHeaderClicked(data: {layoutNode: LayoutNode, domNode: HTMLElement}){
			this.$emit('header-clicked', data);
		},
		// For coloured-outlines on hovered-over leaf-tiles or non-leaf-headers
		onMouseEnter(evt: Event){
			if (!this.isLeaf){
				(this.$refs.nonLeaf as Element).classList.replace('shadow-normal', 'shadow-highlight');
				let sepSweptArea = (this.$refs.sepSweptArea as Element | null);
				if (sepSweptArea != null){
					sepSweptArea.classList.replace('shadow-normal', 'shadow-highlight');
				}
			} else if (this.isExpandable){
				(evt.target as Element).classList.replace('shadow-normal', 'shadow-highlight');
			}
		},
		onMouseLeave(evt: Event){
			if (!this.isLeaf){
				(this.$refs.nonLeaf as Element).classList.replace('shadow-highlight', 'shadow-normal');
				let sepSweptArea = this.$refs.sepSweptArea as Element | null;
				if (sepSweptArea != null){
					sepSweptArea.classList.replace('shadow-highlight', 'shadow-normal');
				}
			} else if (this.isExpandable){
				(evt.target as Element).classList.replace('shadow-highlight', 'shadow-normal');
			}
		},
	},
	name: 'tile', // Need this to use self in template
	emits: ['leaf-clicked', 'header-clicked'],
});
</script>

<template>
<div :style="tileStyles">
	<div v-if="isLeaf" :style="leafStyles" ref="leaf"
		:class="['shadow-normal'].concat(isExpandable ? ['hover:cursor-pointer'] : [])"
		@click="onLeafClick"  @mouseenter="onMouseEnter" @mouseleave="onMouseLeave">
		<div :style="{borderRadius: options.borderRadius + 'px'}" class="scrim-upper-half"/>
		<div :style="leafHeaderStyles">{{layoutNode.tolNode.name}}</div>
	</div>
	<div v-else :style="nonLeafStyles" class="shadow-normal" ref="nonLeaf">
		<h1 v-if="showHeader" :style="nonLeafHeaderStyles" class="hover:cursor-pointer"
			@click="onHeaderClick" @mouseenter="onMouseEnter" @mouseleave="onMouseLeave">
			{{layoutNode.tolNode.name}}
		</h1>
		<div :style="sepSweptAreaStyles" ref="sepSweptArea"
			:class="[layoutNode?.sepSweptArea?.sweptLeft ? 'hide-right-edge' : 'hide-top-edge', 'shadow-normal']">
			<h1 v-if="layoutNode?.sepSweptArea?.sweptLeft === false"
				:style="nonLeafHeaderStyles" class="hover:cursor-pointer"
				@click="onHeaderClick"  @mouseenter="onMouseEnter" @mouseleave="onMouseLeave">
				{{layoutNode.tolNode.name}}
			</h1>
		</div>
		<tile v-for="child in layoutNode.children" :key="child.tolNode.name" :layoutNode="child"
			:headerSz="headerSz" :tileSpacing="tileSpacing" :transitionDuration="transitionDuration"
			@leaf-clicked="onInnerLeafClicked" @header-clicked="onInnerHeaderClicked"/>
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
.scrim-upper-half {
	position: absolute;
	top: 0;
	height: 50%;
	width: 100%;
	background-image: linear-gradient(to top, rgba(0,0,0,0), rgba(0,0,0,0.4));
}
.shadow-highlight {
	box-shadow: var(--shadowWithHover);
}
.shadow-normal {
	box-shadow: var(--shadowNormal);
}
</style>
