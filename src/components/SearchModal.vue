<template>
<div class="fixed left-0 top-0 w-full h-full bg-black/40" @click="onClose">
	<div class="absolute left-1/2 -translate-x-1/2 top-1/4 -translate-y-1/2 min-w-3/4 md:min-w-[12cm] flex"
		:style="styles">
		<input type="text" class="block border p-1 px-2 rounded-l-[inherit] grow" ref="searchInput"
			@keyup.enter="onSearch" @keyup.esc="onClose"
			@input="onInput" @keydown.down.prevent="onDownKey" @keydown.up.prevent="onUpKey"/>
		<div class="p-1 hover:cursor-pointer">
			<search-icon @click.stop="onSearch" class="w-8 h-8"/>
		</div>
		<div class="absolute top-[100%] w-full overflow-hidden" :style="suggContainerStyles">
			<div v-for="(sugg, idx) of searchSuggs"
				:style="{backgroundColor: idx == focusedSuggIdx ? uiOpts.bgColorAltDark : uiOpts.bgColorAlt}"
				class="border-b p-1 px-2 hover:underline hover:cursor-pointer flex"
				@click="resolveSearch(sugg.canonicalName || sugg.name)">
				<div class="grow overflow-hidden whitespace-nowrap text-ellipsis">
					<span>{{suggDisplayStrings[idx][0]}}</span>
					<span class="font-bold">{{suggDisplayStrings[idx][1]}}</span>
					<span>{{suggDisplayStrings[idx][2]}}</span>
				</div>
				<info-icon class="hover:cursor-pointer my-auto w-5 h-5"
					@click.stop="onInfoIconClick(sugg.canonicalName || sugg.name)"/>
			</div>
			<div v-if="searchHadMoreSuggs" class="text-center">&#x2022; &#x2022; &#x2022;</div>
		</div>
		<label :style="animateLabelStyles" class="flex gap-1">
			<input type="checkbox" v-model="uiOpts.searchJumpMode" @change="$emit('setting-chg', 'searchJumpMode')"/>
			<div class="text-sm">Jump to result</div>
		</label>
	</div>
</div>
</template>

<script lang="ts">
import {defineComponent, PropType} from 'vue';
import SearchIcon from './icon/SearchIcon.vue';
import LogInIcon from './icon/LogInIcon.vue';
import InfoIcon from './icon/InfoIcon.vue';
import {TolNode, TolMap} from '../tol';
import {LayoutNode, LayoutMap, LayoutOptions} from '../layout';
import {queryServer, SearchSugg, SearchSuggResponse, UiOptions} from '../lib';

export default defineComponent({
	props: {
		lytMap: {type: Object as PropType<LayoutMap>, required: true}, // Used to check if a searched-for node exists
		activeRoot: {type: Object as PropType<LayoutNode>, required: true}, // Sent to server to reduce response size
		tolMap: {type: Object as PropType<TolMap>, required: true}, // Upon a search response, gets new nodes added
		lytOpts: {type: Object as PropType<LayoutOptions>, required: true},
		uiOpts: {type: Object as PropType<UiOptions>, required: true},
	},
	data(){
		return {
			// Search-suggestion data
			searchSuggs: [] as SearchSugg[],
			searchHadMoreSuggs: false,
			suggsInput: '', // The input that resulted in the current suggestions (used to highlight matching text)
			// For search-suggestion requests
			lastSuggReqTime: 0, // Set when a search-suggestions request is initiated
			pendingSuggReqParams: null as null | URLSearchParams,
				// Used by a search-suggestion requester to request with the latest user input
			pendingDelayedSuggReq: 0, // Set via setTimeout() for a non-initial search-suggestions request
			pendingSuggInput: '', // Used to remember what input triggered a suggestions request
			// Other
			focusedSuggIdx: null as null | number, // Denotes a search-suggestion selected using the arrow keys
		};
	},
	computed: {
		styles(): Record<string,string> {
			let br = this.uiOpts.borderRadius;
			return {
				backgroundColor: this.uiOpts.bgColorAlt,
				borderRadius: this.searchSuggs.length == 0 ? `${br}px` : `${br}px ${br}px 0 0`,
				boxShadow: this.uiOpts.shadowNormal,
			};
		},
		suggContainerStyles(): Record<string,string> {
			let br = this.uiOpts.borderRadius;
			return {
				backgroundColor: this.uiOpts.bgColorAlt,
				color: this.uiOpts.textColorAlt,
				borderRadius: `0 0 ${br}px ${br}px`,
			};
		},
		animateLabelStyles(): Record<string,string> {
			return {
				position: 'absolute',
				top: -this.lytOpts.headerSz - 2 + 'px',
				right: '0',
				height: this.lytOpts.headerSz + 'px',
				color: this.uiOpts.textColor,
			};
		},
		suggDisplayStrings(): [string, string, string][] {
			let result: [string, string, string][] = [];
			let input = this.suggsInput;
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
			// Get URL params to use for querying search-suggestions
			let urlParams = new URLSearchParams({
				type: 'sugg',
				name: input.value,
				limit: String(this.uiOpts.searchSuggLimit),
				tree: this.uiOpts.tree,
			});
			// Query server, delaying/skipping if a request was recently sent
			this.pendingSuggReqParams = urlParams;
			this.pendingSuggInput = input.value;
			let doReq = async () => {
				let suggInput = this.pendingSuggInput;
				let responseObj: SearchSuggResponse =
					await queryServer(this.pendingSuggReqParams!);
				if (responseObj == null){
					return;
				}
				this.searchSuggs = responseObj.suggs;
				this.searchHadMoreSuggs = responseObj.hasMore;
				this.suggsInput = suggInput;
				// Auto-select first result if present
				if (this.searchSuggs.length > 0){
					this.focusedSuggIdx = 0;
				} else {
					this.focusedSuggIdx = null;
				}
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
			if (this.focusedSuggIdx != null){
				this.focusedSuggIdx = (this.focusedSuggIdx + 1) % this.searchSuggs.length;
			}
		},
		onUpKey(){
			if (this.focusedSuggIdx != null){
				this.focusedSuggIdx = (this.focusedSuggIdx - 1 + this.searchSuggs.length) % this.searchSuggs.length;
					// The addition after '-1' is to avoid becoming negative
			}
		},
		// Search events
		onSearch(){
			if (this.focusedSuggIdx == null){
				let input = (this.$refs.searchInput as HTMLInputElement).value.toLowerCase();
				this.resolveSearch(input)
			} else {
				let sugg = this.searchSuggs[this.focusedSuggIdx]
				this.resolveSearch(sugg.canonicalName || sugg.name);
			}
		},
		async resolveSearch(tolNodeName: string){
			if (tolNodeName == ''){
				return;
			}
			// Check if the node has already been retrieved
			if (this.lytMap.has(tolNodeName)){
				this.$emit('search', tolNodeName);
				return;
			}
			// Ask server for nodes in parent-chain, updates tolMap, then emits search event
			let urlParams = new URLSearchParams({
				type: 'node',
				name: tolNodeName,
				toroot: '1',
				excl: this.activeRoot.name,
				tree: this.uiOpts.tree,
			});
			this.$emit('net-wait'); // Allows the parent component to show a loading-indicator
			let responseObj: {[x: string]: TolNode} = await queryServer(urlParams);
			this.$emit('net-get');
			if (responseObj == null){
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
	emits: ['search', 'close', 'info-click', 'setting-chg', 'net-wait', 'net-get', ],
});
</script>
