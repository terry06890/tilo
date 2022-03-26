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
			let input = this.$refs.searchInput as HTMLInputElement;
			let tolNode = this.tolMap.get(input.value);
			if (tolNode == null){
				input.value = '';
				// Trigger failure animation
				input.classList.remove('animate-red-then-fade');
				input.offsetWidth; // Triggers reflow
				input.classList.add('animate-red-then-fade');
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
	<div class="absolute left-1/2 -translate-x-1/2 top-1/2 -translate-y-1/2 p-3
		bg-stone-50 rounded-md shadow shadow-black flex gap-1">
		<input type="text" class="block border"
			@keyup.enter="onSearchEnter" @keyup.esc="closeClicked" ref="searchInput"/>
		<svg class="block w-6 h-6 ml-1 hover:cursor-pointer hover:bg-stone-200" @click="onSearchEnter"
			xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
			stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
		  <circle cx="11" cy="11" r="8"/>
		  <line x1="21" y1="21" x2="16.65" y2="16.65"/>
		</svg>
	</div>
</div>
</template>

<style>
.animate-red-then-fade {
	animation-name: red-then-fade;
	animation-duration: 500ms;
	animation-timing-function: ease-in;
}
@keyframes red-then-fade {
	from {
		background-color: rgba(255,0,0,0.2);
	}
	to {
		background-color: transparent;
	}
}
</style>