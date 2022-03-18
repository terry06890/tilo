<script lang="ts">
import {defineComponent, PropType} from 'vue';
import {LayoutNode} from '../lib';

//component holds a tree-node structure representing a tile or tile-group to be rendered
export default defineComponent({
	name: 'tile', //need this to use self in template
	props: {
		layoutNode: {type: Object as PropType<LayoutNode>, required: true},
		isRoot: {type: Boolean, default: false},
		//settings passed in from parent component
		transitionDuration: {type: Number, required: true},
		headerSz: {type: Number, required: true},
		tileSpacing: {type: Number, required: true},
	},
	data(){
		return {
			//used during transitions and to emulate/show an apparently-joined div
			zIdx: 0,
			overflow: this.isRoot ? 'hidden' : 'visible',
		}
	},
	computed: {
		showHeader(){
			return (this.layoutNode.showHeader && !this.layoutNode.sepSweptArea) ||
				(this.layoutNode.sepSweptArea && this.layoutNode.sepSweptArea.sweptLeft);
		},
		tileStyles(): Record<string,string> {
			return {
				//place using layoutNode, with centering if root
				position: 'absolute',
				left: this.isRoot ? '50%' : this.layoutNode.pos[0] + 'px',
				top: this.isRoot ? '50%' : this.layoutNode.pos[1] + 'px',
				transform: this.isRoot ? 'translate(-50%, -50%)' : 'none',
				width: this.layoutNode.dims[0] + 'px',
				height: this.layoutNode.dims[1] + 'px',
				//other bindings
				transitionDuration: this.transitionDuration + 'ms',
				zIndex: String(this.zIdx),
				overflow: String(this.overflow),
				//static
				outline: 'black solid 1px',
				backgroundColor: 'white',
				transitionProperty: 'left, top, width, height',
				transitionTimingFunction: 'ease-out',
			};
		},
		leafStyles(): Record<string,string> {
			return {
				width: '100%',
				height: '100%',
				backgroundImage: 'url(\'/img/' + this.layoutNode.tolNode.name.replaceAll('\'', '\\\'') + '.jpg\')',
				backgroundSize: 'cover',
				opacity: (this.layoutNode.tolNode.children.length > 0) ? '1' : '0.7',
			};
		},
		headerStyles(): Record<string,string> {
			return {
				height: this.headerSz + 'px',
				backgroundColor: 'lightgray',
				textAlign: 'center',
				overflow: 'hidden',
				textOverflow: 'ellipsis',
				whiteSpace: 'nowrap',
			};
		},
		sepSweptAreaStyles(): Record<string,string> {
			let commonStyles = {
				position: 'absolute',
				backgroundColor: 'white',
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
					width: (area.dims[0] + (area.sweptLeft ? 1 : 0)) + 'px',
					height: (area.dims[1] + (area.sweptLeft ? 0 : 1)) + 'px',
				};
			}
		},
		sepSweptAreaOutlineClasses(){
			let area = this.layoutNode.sepSweptArea;
			return ['outline-top-left', (area && area.sweptLeft) ? 'outline-bottom-left' : 'outline-top-right'];
		},
	},
	methods: {
		onLeafClick(){
			this.$emit('leaf-clicked', this.layoutNode);
			//increase z-index and hide overflow during transition
			this.zIdx = 1;
			this.overflow = 'hidden';
			setTimeout(() => {this.zIdx = 0; this.overflow = 'visible'}, this.transitionDuration);
		},
		onInnerLeafClicked(node: LayoutNode){
			this.$emit('leaf-clicked', node);
		},
		onHeaderClick(){
			this.$emit('header-clicked', this.layoutNode);
			//increase z-index and hide overflow during transition
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
	<div v-if="layoutNode.children.length == 0"
		:style="leafStyles" class="hover:cursor-pointer" @click="onLeafClick"/>
	<div v-else>
		<div v-if="showHeader" :style="headerStyles" class="hover:cursor-pointer" @click="onHeaderClick">
			{{layoutNode.tolNode.name}}
		</div>
		<div :style="sepSweptAreaStyles" :class="sepSweptAreaOutlineClasses">
			<div v-if="layoutNode?.sepSweptArea?.sweptLeft === false"
				:style="headerStyles" class="hover:cursor-pointer" @click="onHeaderClick">
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
.outline-top-left::before {
	content: '';
	position: absolute;
	background-color: black;
	left: -1px;
	top: -1px;
	width: 100%;
	height: 100%;
	z-index: -10;
}
.outline-bottom-left::after {
	content: '';
	position: absolute;
	background-color: black;
	left: -1px;
	bottom: -1px;
	width: 100%;
	height: 100%;
	z-index: -10;
}
.outline-top-right::after {
	content: '';
	position: absolute;
	background-color: black;
	right: -1px;
	top: -1px;
	width: 100%;
	height: 100%;
	z-index: -10;
}
</style>
