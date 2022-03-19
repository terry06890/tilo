<script lang="ts">
import {defineComponent, PropType} from 'vue';
import {LayoutNode} from '../lib';

// Component holds a tree-node structure representing a tile or tile-group to be rendered
export default defineComponent({
	name: 'tile', // Need this to use self in template
	props: {
		layoutNode: {type: Object as PropType<LayoutNode>, required: true},
		isRoot: {type: Boolean, default: false},
		// Settings passed in from parent component
		transitionDuration: {type: Number, required: true},
		headerSz: {type: Number, required: true},
		tileSpacing: {type: Number, required: true},
	},
	data(){
		return {
			borderRadius: '5px',
			leafHeaderHorzSpc: 4,
			leafHeaderVertSpc: 2,
			leafHeaderColor: '#fafaf9',
			expandableLeafHeaderColor: 'greenyellow', //yellow, greenyellow, turquoise,
			nonLeafBgColor: '#44403c',
			nonLeafHeaderColor: '#fafaf9',
			nonLeafHeaderBgColor: '#78716c',
			// Used during transitions and to emulate/show an apparently-joined div
			zIdx: 0,
			overflow: this.isRoot ? 'hidden' : 'visible',
		}
	},
	computed: {
		isLeaf(){
			return this.layoutNode.children.length == 0;
		},
		isExpandable(){
			return this.layoutNode.tolNode.children.length > this.layoutNode.children;
		},
		showHeader(){
			return (this.layoutNode.showHeader && !this.layoutNode.sepSweptArea) ||
				(this.layoutNode.sepSweptArea && this.layoutNode.sepSweptArea.sweptLeft);
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
				'--expandableLeafHeaderColor': this.expandableLeafHeaderColor,
			};
		},
		leafStyles(): Record<string,string> {
			return {
				width: '100%',
				height: '100%',
				backgroundImage: 'url(\'/img/' + this.layoutNode.tolNode.name.replaceAll('\'', '\\\'') + '.png\')',
				backgroundSize: 'cover',
				borderRadius: this.borderRadius,
			};
		},
		leafHeaderStyles(): Record<string,string> {
			return {
				position: 'absolute',
				left: this.leafHeaderHorzSpc + 'px',
				top: this.leafHeaderVertSpc + 'px',
				maxWidth: (this.layoutNode.dims[0] - this.leafHeaderHorzSpc*2) + 'px',
				height: this.headerSz + 'px',
				lineHeight: this.headerSz + 'px',
				color: this.isExpandable ? this.expandableLeafHeaderColor : this.leafHeaderColor,
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
				outline: this.isRoot ? '' : 'black solid 1px',
				borderRadius: this.borderRadius,
			};
			if (this.layoutNode.sepSweptArea != null){
				temp = this.layoutNode.sepSweptArea.sweptLeft ?
					{...temp, borderRadius: `${this.borderRadius} ${this.borderRadius} ${this.borderRadius} 0`} :
					{...temp, borderRadius: `${this.borderRadius} 0 ${this.borderRadius} ${this.borderRadius}`};
			}
			return temp;
		},
		nonLeafHeaderStyles(): Record<string,string> {
			return {
				height: this.headerSz + 'px',
				lineHeight: this.headerSz + 'px',
				textAlign: 'center',
				color: this.nonLeafHeaderColor,
				backgroundColor: this.nonLeafHeaderBgColor,
				borderRadius: `${this.borderRadius} ${this.borderRadius} 0 0`,
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
				outline: 'black solid 1px',
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
				return {
					...commonStyles,
					left: area.pos[0] + 'px',
					top: area.pos[1] + 'px',
					width: area.dims[0] + 'px',
					height: area.dims[1] + 'px',
					borderRadius: area.sweptLeft ?
						`${this.borderRadius} 0 0 ${this.borderRadius}` :
						`${this.borderRadius} ${this.borderRadius} 0 0`,
				};
			}
		},
	},
	methods: {
		onLeafClick(){
			this.$emit('leaf-clicked', this.layoutNode);
			// Increase z-index and hide overflow during transition
			this.zIdx = 1;
			this.overflow = 'hidden';
			setTimeout(() => {this.zIdx = 0; this.overflow = 'visible'}, this.transitionDuration);
		},
		onInnerLeafClicked(node: LayoutNode){
			this.$emit('leaf-clicked', node);
		},
		onHeaderClick(){
			this.$emit('header-clicked', this.layoutNode);
			// Increase z-index and hide overflow during transition
			this.zIdx = 1;
			this.overflow = 'hidden';
			setTimeout(() => {this.zIdx = 0; this.overflow = 'visible'}, this.transitionDuration);
		},
		onInnerHeaderClicked(node: LayoutNode){
			this.$emit('header-clicked', node);
		},
	},
});
</script>

<template>
<div :style="tileStyles">
	<div v-if="isLeaf" :style="leafStyles"
		:class="isExpandable ? ['hover:cursor-pointer', 'shadow-on-hover'] : ''" @click="onLeafClick">
		<div :style="{borderRadius: this.borderRadius}" class="upper-scrim"/>
		<div :style="leafHeaderStyles">{{layoutNode.tolNode.name}}</div>
	</div>
	<div v-else :style="nonLeafStyles">
		<div v-if="showHeader" :style="nonLeafHeaderStyles" class="hover:cursor-pointer" @click="onHeaderClick">
			{{layoutNode.tolNode.name}}
		</div>
		<div :style="sepSweptAreaStyles"
			:class="layoutNode?.sepSweptArea?.sweptLeft ? 'hide-right-edge' : 'hide-top-edge'">
			<div v-if="layoutNode?.sepSweptArea?.sweptLeft === false"
				:style="nonLeafHeaderStyles" class="hover:cursor-pointer" @click="onHeaderClick">
				{{layoutNode.tolNode.name}}
			</div>
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
	right: -1px;
	bottom: 0;
	width: 1px;
	height: 101%;
}
.hide-top-edge::before {
	content: '';
	position: absolute;
	background-color: var(--nonLeafBgColor);
	bottom: -1px;
	right: 0;
	width: 101%;
	height: 1px;
}
.upper-scrim {
	position: absolute;
	top: 0;
	height: 50%;
	width: 100%;
	background-image: linear-gradient(to top, rgba(0,0,0,0), rgba(0,0,0,0.4));
}
.shadow-on-hover:hover {
	box-shadow: 0 0 1px 2px var(--expandableLeafHeaderColor);
}
</style>
