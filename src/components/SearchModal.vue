<script lang="ts">
import {defineComponent, PropType} from 'vue';
import SearchIcon from './icon/SearchIcon.vue';
import {LayoutNode} from '../layout';
import type {TolMap} from '../tol';

// Displays a search box, and sends search requests
export default defineComponent({
	props: {
		tolMap: {type: Object as PropType<TolMap>, required: true},
		uiOpts: {type: Object, required: true},
	},
	methods: {
		onCloseClick(evt: Event){
			if (evt.target == this.$el || (this.$refs.searchIcon as typeof SearchIcon).$el.contains(evt.target)){
				this.$emit('search-close');
			}
		},
		onSearchEnter(){
			let input = this.$refs.searchInput as HTMLInputElement;
			// Query server
			let url = new URL(window.location.href);
			url.pathname = '/tolnode/' + input.value;
			fetch(url)
				.then(response => {
					// Search successful. Get nodes in parent-chain, add to tolMap, then emit event.
					url.search = '?type=chain';
					fetch(url)
						.then(response => response.json())
						.then(obj => {
							Object.getOwnPropertyNames(obj).forEach(key => {this.tolMap[key] = obj[key]});
							this.$emit('search-node', input.value);
						})
						.catch(error => {
							console.log('ERROR loading tolnode chain', error);
						});
				})
				.catch(error => {
					input.value = '';
					// Trigger failure animation
					input.classList.remove('animate-red-then-fade');
					input.offsetWidth; // Triggers reflow
					input.classList.add('animate-red-then-fade');
				});
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
		<search-icon @click.stop="onSearchEnter" ref="searchIcon"
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
