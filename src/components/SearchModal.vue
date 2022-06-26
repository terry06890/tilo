<script lang="ts">

import {defineComponent, PropType} from 'vue';
import SearchIcon from './icon/SearchIcon.vue';
import LogInIcon from './icon/LogInIcon.vue';
import InfoIcon from './icon/InfoIcon.vue';
import {TolNode, TolMap, UiOptions, SearchSugg, SearchSuggResponse} from '../lib';
import {LayoutNode, LayoutOptions} from '../layout';

export default defineComponent({
	props: {
		tolMap: {type: Object as PropType<TolMap>, required: true}, // Added to from a search response
		lytOpts: {type: Object as PropType<LayoutOptions>, required: true},
		uiOpts: {type: Object as PropType<UiOptions>, required: true},
	},
	data(){
		return {
			// For search-suggestion requests
			lastSuggReqTime: 0, // Set when a search-suggestions request is initiated
			pendingSuggReqUrl: '', // Used by a search-suggestion requester to use the latest user input
			pendingDelayedSuggReq: 0, // Set via setTimeout() for a non-initial search-suggestions request
			// Search-suggestion data
			searchSuggs: [] as SearchSugg[],
			searchHadMoreSuggs: false,
			// Other
			focusedSuggIdx: null as null | number, // Denotes a search-suggestion selected using the arrow keys
		};
	},
	computed: {
		styles(): Record<string,string> {
			return {
				backgroundColor: this.uiOpts.bgColorAlt,
				borderRadius: this.uiOpts.borderRadius + 'px',
				boxShadow: this.uiOpts.shadowNormal,
			};
		},
		suggDisplayStrings(): [string, string, string][] {
			let result: [string, string, string][] = [];
			let input = (this.$refs.searchInput as HTMLInputElement).value;
			// For each SearchSugg
			for (let sugg of this.searchSuggs){
				let idx = sugg.name.indexOf(input);
				// Split suggestion text into parts before/within/after an input match
				let strings: [string, string, string];
				if (idx != -1){
					strings = [sugg.name.substring(0, idx), input, sugg.name.substring(idx + input.length)];
				} else {
					strings = [input, '', ''];
				}
				// Indicate any distinct canonical-name
				if (sugg.canonicalName != null){
					strings[2] += ` (aka ${sugg.canonicalName})`;
				}
				//
				result.push(strings);
			}
			return result;
		},
	},
	methods: {
		// Search-suggestion events
		async onInput(){
			let input = this.$refs.searchInput as HTMLInputElement;
			// Check for empty input
			if (input.value.length == 0){
				this.searchSuggs = [];
				this.searchHadMoreSuggs = false;
				this.focusedSuggIdx = null;
				return;
			}
			// Get URL to use for querying search-suggestions
			let url = new URL(window.location.href);
			url.pathname = '/data/search';
			url.search = '?name=' + encodeURIComponent(input.value);
			url.search += this.uiOpts.useReducedTree ? '&tree=reduced' : '';
			url.search += '&limit=' + this.uiOpts.searchSuggLimit;
			// Query server, delaying/skipping if a request was recently sent
			this.pendingSuggReqUrl = url.toString();
			let doReq = async () => {
				let responseObj: SearchSuggResponse;
				try {
					let response = await fetch(this.pendingSuggReqUrl);
					responseObj = await response.json();
				} catch (error){
					console.log('Error with getting search suggestions from server: ' + error)
					return;
				}
				this.searchSuggs = responseObj.suggs;
				this.searchHadMoreSuggs = responseObj.hasMore;
				this.focusedSuggIdx = null;
			};
			let currentTime = new Date().getTime();
			if (this.lastSuggReqTime == 0){
				this.lastSuggReqTime = currentTime;
				await doReq();
				if (this.lastSuggReqTime == currentTime){
					this.lastSuggReqTime = 0;
				}
			} else if (this.pendingDelayedSuggReq == 0){
				this.lastSuggReqTime = currentTime;
				this.pendingDelayedSuggReq = setTimeout(async () => {
					this.pendingDelayedSuggReq = 0;
					await doReq();
					if (this.lastSuggReqTime == currentTime){
						this.lastSuggReqTime = 0;
					}
				}, 300);
			}
		},
		onInfoIconClick(nodeName: string){
			this.$emit('info-click', nodeName);
		},
		onDownKey(){
			// Select next search-suggestion, possibly cycling back to top
			if (this.searchSuggs.length > 0){
				if (this.focusedSuggIdx == null){
					this.focusedSuggIdx = 0;
				} else if (this.focusedSuggIdx == this.searchSuggs.length - 1){
					this.focusedSuggIdx = null;
				} else {
					this.focusedSuggIdx += 1;
				}
			}
		},
		onUpKey(){
			// Select previous search-suggestion, possibly cycling to bottom
			if (this.searchSuggs.length > 0){
				if (this.focusedSuggIdx == null){
					this.focusedSuggIdx = this.searchSuggs.length - 1;
				} else if (this.focusedSuggIdx == 0){
					this.focusedSuggIdx = null;
				} else {
					this.focusedSuggIdx -= 1;
				}
			}
		},
		// Search events
		onSearch(){
			if (this.focusedSuggIdx == null){
				this.resolveSearch((this.$refs.searchInput as HTMLInputElement).value.toLowerCase())
			} else {
				let sugg = this.searchSuggs[this.focusedSuggIdx]
				this.resolveSearch(sugg.canonicalName || sugg.name);
			}
		},
		async resolveSearch(tolNodeName: string){
			if (tolNodeName == ''){
				return;
			}
			// Ask server for nodes in parent-chain, updates tolMap, then emits search event
			let url = new URL(window.location.href);
			url.pathname = '/data/chain';
			url.search = '?name=' + encodeURIComponent(tolNodeName);
			url.search += (this.uiOpts.useReducedTree ? '&tree=reduced' : '');
			let responseObj: {[x: string]: TolNode};
			try {
				let response = await fetch(url.toString());
				responseObj = await response.json();
			} catch (error){
				console.log('Error with getting tolnode chain: ' + error);
				return;
			}
			let keys = Object.getOwnPropertyNames(responseObj);
			if (keys.length > 0){
				keys.forEach(key => {
					if (!this.tolMap.has(key)){
						this.tolMap.set(key, responseObj[key])
					}
				});
				this.$emit('search', tolNodeName);
			} else {
				// Trigger failure animation
				let input = this.$refs.searchInput as HTMLInputElement;
				input.classList.remove('animate-red-then-fade');
				input.offsetWidth; // Triggers reflow
				input.classList.add('animate-red-then-fade');
			}
		},
		// Other
		onSearchModeChg(){
			this.uiOpts.searchJumpMode = !this.uiOpts.searchJumpMode;
			this.$emit('setting-chg', 'searchJumpMode');
		},
		onClose(evt: Event){
			if (evt.target == this.$el){
				this.$emit('close');
			}
		},
		focusInput(){ // Used from external component
			(this.$refs.searchInput as HTMLInputElement).focus();
		},
	},
	mounted(){
		(this.$refs.searchInput as HTMLInputElement).focus();
	},
	components: {SearchIcon, InfoIcon, LogInIcon, },
	emits: ['search', 'close', 'info-click', 'setting-chg', ],
});
</script>

<template>
<div class="fixed left-0 top-0 w-full h-full bg-black/40" @click="onClose">
	<div class="absolute left-1/2 -translate-x-1/2 top-1/4 w-3/4 -translate-y-1/2 flex" :style="styles">
		<div class="relative grow m-2">
			<input type="text" class="block border p-1 w-full" ref="searchInput"
				@keyup.enter="onSearch" @keyup.esc="onClose"
				@input="onInput" @keydown.down.prevent="onDownKey" @keydown.up.prevent="onUpKey"/>
			<div class="absolute top-[100%] w-full"
				:style="{backgroundColor: uiOpts.bgColorAlt, color: uiOpts.textColorAlt}">
				<div v-for="(sugg, idx) of searchSuggs"
					:style="{backgroundColor: idx == focusedSuggIdx ? uiOpts.bgColorAltDark : uiOpts.bgColorAlt}"
					class="border p-1 hover:underline hover:cursor-pointer flex"
					@click="resolveSearch(sugg.canonicalName || sugg.name)">
					<div class="grow overflow-hidden whitespace-nowrap text-ellipsis">
						<span>{{suggDisplayStrings[idx][0]}}</span>
						<span class="font-bold">{{suggDisplayStrings[idx][1]}}</span>
						<span>{{suggDisplayStrings[idx][2]}}</span>
					</div>
					<info-icon class="hover:cursor-pointer my-auto w-5 h-5"
						@click.stop="onInfoIconClick(sugg.canonicalName || sugg.name)"/>
				</div>
				<div v-if="searchHadMoreSuggs" class="text-center border">...</div>
			</div>
		</div>
		<div class="my-auto hover:cursor-pointer hover:brightness-75  rounded border shadow">
			<search-icon @click.stop="onSearch" class="block w-8 h-8"/>
		</div>
		<div class="my-auto mx-2 hover:cursor-pointer hover:brightness-75 rounded">
			<log-in-icon @click.stop="onSearchModeChg" class="block w-8 h-8"
				:class="uiOpts.searchJumpMode ? 'opacity-100' : 'opacity-30'"/>
		</div>
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
