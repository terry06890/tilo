<script lang="ts">
import {defineComponent, PropType} from 'vue';
import {TolNode, LayoutNode} from '../lib';

export default defineComponent({
	props: {
		layoutTree: {type: Object as PropType<LayoutNode>, required: true},
		tolMap: {type: Object as PropType<Map<string,TolNode>>, required: true},
		options: {type: Object, required: true},
	},
	methods: {
		closeClicked(evt: Event){
			if (evt.target == this.$el || evt.target == this.$refs.closeIcon){
				this.$emit('search-close');
			}
		},
		onSearchEnter(){
			let searchString = (this.$refs.searchInput as HTMLInputElement).value;
			let tolNode = this.tolMap.get(searchString);
			if (tolNode == null){
				console.log('No result found');
			} else {
				this.$emit('search-node', tolNode);
			}
		},
	},
	mounted(){
		(this.$refs.searchInput as HTMLInputElement).focus();
	},
	emits: ['search-node', 'search-close']
});
</script>

<template>
<div class="fixed left-0 top-0 w-full h-full bg-black/40" @click="closeClicked">
	<div class="absolute left-1/2 -translate-x-1/2 top-1/2 -translate-y-1/2 p-4
		bg-stone-50 rounded-md shadow shadow-black flex gap-1">
		<input type="text" @keyup.enter="onSearchEnter" @keyup.esc="closeClicked" class="block border" ref="searchInput"/>
		<svg class="block w-7 h-7 border rounded hover:cursor-pointer hover:bg-stone-200" @click="onSearchEnter"
			xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
			stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
		  <circle cx="11" cy="11" r="8"/>
		  <line x1="21" y1="21" x2="16.65" y2="16.65"/>
		</svg>
		<svg class="block w-7 h-7 border rounded hover:cursor-pointer hover:bg-stone-200"
			@click="closeClicked" ref="closeIcon"
			xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
			stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
		  <line x1="18" y1="6" x2="6" y2="18"/>
		  <line x1="6" y1="6" x2="18" y2="18"/>
		</svg>
	</div>
</div>
</template>
