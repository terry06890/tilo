<script lang="ts">
import {defineComponent, PropType} from 'vue';
import SearchIcon from './icon/SearchIcon.vue';
import {TolNode} from '../tol';
import {LayoutNode} from '../layout';

export default defineComponent({
	props: {
		layoutTree: {type: Object as PropType<LayoutNode>, required: true},
		tolMap: {type: Object as PropType<Map<string,TolNode>>, required: true},
		options: {type: Object, required: true},
	},
	methods: {
		closeClicked(evt: Event){
			if (evt.target == this.$el || (this.$refs.closeIcon.$el as HTMLElement).contains(evt.target as HTMLElement)){
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
	emits: ['search-node', 'search-close']
});
</script>

<template>
<div class="fixed left-0 top-0 w-full h-full bg-black/40" @click="closeClicked">
	<div class="absolute left-1/2 -translate-x-1/2 top-1/2 -translate-y-1/2 p-3
		bg-stone-50 rounded-md shadow shadow-black flex gap-1">
		<input type="text" class="block border"
			@keyup.enter="onSearchEnter" @keyup.esc="closeClicked" ref="searchInput"/>
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
