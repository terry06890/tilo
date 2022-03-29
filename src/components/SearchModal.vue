<script lang="ts">
import {defineComponent, PropType} from 'vue';
import SearchIcon from './icon/SearchIcon.vue';
import {TolNode} from '../tol';
import {LayoutNode} from '../layout';

// Displays a search box, and sends search requests
export default defineComponent({
	props: {
		// Map from tree-of-life node names to TolNode objects
		tolMap: {type: Object as PropType<Map<string,TolNode>>, required: true},
		// Options
		uiOpts: {type: Object, required: true},
	},
	methods: {
		onCloseClick(evt: Event){
			if (evt.target == this.$el || (this.$refs.searchInput as typeof SearchIcon).$el.contains(evt.target)){
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
		focusInput(){
			(this.$refs.searchInput as HTMLInputElement).focus();
		},
	},
	mounted(){
		(this.$refs.searchInput as HTMLInputElement).focus();
	},
	components: {SearchIcon, },
	emits: ['search-node', 'search-close', ],
});
</script>

<template>
<div class="fixed left-0 top-0 w-full h-full bg-black/40" @click="onCloseClick">
	<div class="absolute left-1/2 -translate-x-1/2 top-1/2 -translate-y-1/2 p-3
		bg-stone-50 rounded-md shadow shadow-black flex gap-1">
		<input type="text" class="block border"
			@keyup.enter="onSearchEnter" @keyup.esc="onCloseClick" ref="searchInput"/>
		<search-icon @click.stop="onSearchEnter"
			class="block w-6 h-6 ml-1 hover:cursor-pointer hover:bg-stone-200" />
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
