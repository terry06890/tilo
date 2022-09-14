<template>
<div :style="styles" @wheel.stop="onWheelEvt" ref="rootRef">
	<tol-tile v-for="(node, idx) in dummyNodes" :key="node.name" class="shrink-0"
		:layoutNode="node" :tolMap="tolMap" :nonAbsPos="true"
		@leaf-click="onTileClick(nodes[idx])" @info-click="onInfoIconClick"/>
</div>
</template>

<script setup lang="ts">
import {ref, computed, watch, onMounted, nextTick, PropType} from 'vue';
import TolTile from './TolTile.vue';
import {TolMap} from '../tol';
import {LayoutNode} from '../layout';
import {useStore} from '../store';

// Refs
const rootRef = ref(null as HTMLDivElement | null);

// Global store
const store = useStore();

// Props + events
const props = defineProps({
	nodes: {type: Array as PropType<LayoutNode[]>, required: true},
	vert: {type: Boolean, default: false},
	breadth: {type: Number, required: true},
	tolMap: {type: Object as PropType<TolMap>, required: true},
});
const emit = defineEmits(['ancestor-click', 'info-click']);

// Computed prop data for display
const imgSz = computed(() =>
	props.breadth - store.lytOpts.tileSpacing - store.scrollGap
		// Intentionally omitting extra tileSpacing, to allow for scrollGap with less image shrinkage
);
const dummyNodes = computed(() => props.nodes.map(n => {
	let newNode = new LayoutNode(n.name, []);
	newNode.dims = [imgSz.value, imgSz.value];
	return newNode;
}));

// Click handling
function onTileClick(node: LayoutNode){
	emit('ancestor-click', node);
}
function onInfoIconClick(data: string){
	emit('info-click', data);
}

// Scroll handling
function onWheelEvt(evt: WheelEvent){ // For converting vertical scrolling to horizontal
	if (!props.vert && Math.abs(evt.deltaX) < Math.abs(evt.deltaY)){
		rootRef.value!.scrollLeft -= (evt.deltaY > 0 ? -30 : 30);
	}
}
function scrollToEnd(){
	let el = rootRef.value;
	if (el != null){
		if (props.vert){
			el.scrollTop = el.scrollHeight;
		} else {
			el.scrollLeft = el.scrollWidth;
		}
	}
}
watch(props.nodes, () => {
	nextTick(() => scrollToEnd());
});
watch(() => props.vert, () => {
	nextTick(() => scrollToEnd());
});
onMounted(() => scrollToEnd());

// Styles
const styles = computed(() => ({
	// For child layout
	display: 'flex',
	flexDirection: props.vert ? 'column' : 'row',
	alignItems: 'center',
	gap: store.lytOpts.tileSpacing + 'px',
	padding: store.lytOpts.tileSpacing + 'px',
	overflowX: props.vert ? 'hidden' : 'auto',
	overflowY: props.vert ? 'auto' : 'hidden',
	// Other
	backgroundColor: store.ancestryBarBgColor,
	boxShadow: store.shadowNormal,
}));
</script>
