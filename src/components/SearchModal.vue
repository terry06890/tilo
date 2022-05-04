<script lang="ts">
import {defineComponent, PropType} from 'vue';
import SearchIcon from './icon/SearchIcon.vue';
import {LayoutNode} from '../layout';
import type {TolMap} from '../tol';

type SearchSugg = {name: string, altName: string}; // Represents a search string suggestion
type SearchSuggResponse = [SearchSugg[], boolean]; // Holds search suggestions and an indication of if there was more

// Displays a search box, and sends search requests
export default defineComponent({
	data(){
		return {
			searchSuggs: [] as SearchSugg[],
			searchHasMoreSuggs: false,
			focusedSuggIdx: null as null | number, // Denotes a search-suggestion selected using the arrow keys
			pendingSearchSuggReq: 0, // Set via setTimeout() upon a search-suggestion request
				// Used to avoid sending many requests when search input is quickly changed multiple times
			lastSuggReqId: 0, // Used to prevent late search-suggestion server-responses from taking effect
		};
	},
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
		onEnter(){
			if (this.focusedSuggIdx == null){
				this.resolveSearch((this.$refs.searchInput as HTMLInputElement).value.toLowerCase())
			} else {
				this.resolveSearch(this.searchSuggs[this.focusedSuggIdx].name);
			}
		},
		resolveSearch(tolNodeName: string){
			// Asks server for nodes in parent-chain, updates tolMap, then emits search event
			let url = new URL(window.location.href);
			url.pathname = '/data/chain';
			url.search = '?name=' + encodeURIComponent(tolNodeName);
			fetch(url.toString())
				.then(response => response.json())
				.then(obj => {
					let keys = Object.getOwnPropertyNames(obj);
					if (keys.length > 0){
						keys.forEach(key => {
							if (!this.tolMap.has(key)){
								this.tolMap.set(key, obj[key])
							}
						});
						this.$emit('search-node', tolNodeName);
					} else {
						// Trigger failure animation
						let input = this.$refs.searchInput as HTMLInputElement;
						input.classList.remove('animate-red-then-fade');
						input.offsetWidth; // Triggers reflow
						input.classList.add('animate-red-then-fade');
					}
				})
				.catch(error => {
					console.log('ERROR loading tolnode chain', error);
				});
		},
		focusInput(){
			(this.$refs.searchInput as HTMLInputElement).focus();
		},
		onInput(){
			let input = this.$refs.searchInput as HTMLInputElement;
			// Check for empty input
			if (input.value.length == 0){
				this.searchSuggs = [];
				this.searchHasMoreSuggs = false;
				this.focusedSuggIdx = null;
				return;
			}
			// Ask server for search-suggestions
			let url = new URL(window.location.href);
			url.pathname = '/data/search';
			url.search = '?name=' + encodeURIComponent(input.value);
			this.lastSuggReqId += 1;
			let suggsId = this.lastSuggReqId;
			let reqDelay = 0;
			if (this.pendingSearchSuggReq != 0){
				clearTimeout(this.pendingSearchSuggReq);
				reqDelay = 300;
			}
			this.pendingSearchSuggReq = setTimeout(() =>
				fetch(url.toString())
					.then(response => response.json())
					.then((results: SearchSuggResponse) => {
						if (this.lastSuggReqId == suggsId){
							this.searchSuggs = results[0];
							this.searchHasMoreSuggs = results[1];
							this.focusedSuggIdx = null;
							this.pendingSearchSuggReq = 0;
						}
					}),
				reqDelay
			);
		},
		onDownKey(){
			// Select next search-suggestion, if any
			if (this.searchSuggs.length > 0){
				if (this.focusedSuggIdx == null){
					this.focusedSuggIdx = 0;
				} else {
					this.focusedSuggIdx = Math.min(this.focusedSuggIdx + 1, this.searchSuggs.length - 1);
				}
			}
		},
		onUpKey(){
			// Select previous search-suggestion, or cancel selection
			if (this.focusedSuggIdx != null){
				if (this.focusedSuggIdx == 0){
					this.focusedSuggIdx = null;
				} else {
					this.focusedSuggIdx -= 1;
				}
			}
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
	<div class="absolute left-1/2 -translate-x-1/2 top-1/2 -translate-y-1/2 p-2
		bg-stone-50 rounded-md shadow shadow-black flex gap-1">
		<div class="relative">
			<input type="text" class="block border p-1" ref="searchInput"
				@keyup.enter="onEnter" @keyup.esc="onCloseClick"
				@input="onInput" @keydown.down.prevent="onDownKey" @keydown.up.prevent="onUpKey"/>
			<div class="absolute top-[100%] w-full">
				<div v-for="(sugg, idx) of searchSuggs"
					:style="{backgroundColor: idx == focusedSuggIdx ? '#a3a3a3' : 'white'}"
					class="bg-white border p-1 hover:underline hover:cursor-pointer"
					@click="resolveSearch(sugg.name)">
					{{sugg.name == sugg.altName ? sugg.name : `${sugg.altName} (aka ${sugg.name})`}}
				</div>
				<div v-if="searchHasMoreSuggs" class="bg-white px-1 text-center border">...</div>
			</div>
		</div>
		<search-icon @click.stop="onEnter" ref="searchIcon"
			class="block w-8 h-8 ml-1 hover:cursor-pointer hover:bg-stone-200" />
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
