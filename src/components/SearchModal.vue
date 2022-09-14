<template>
<div class="fixed left-0 top-0 w-full h-full bg-black/40" @click="onClose" ref="rootRef">
	<div class="absolute left-1/2 -translate-x-1/2 top-1/4 -translate-y-1/2 min-w-3/4 md:min-w-[12cm] flex"
		:style="styles">
		<input type="text" class="block border p-1 px-2 rounded-l-[inherit] grow" ref="inputRef"
			@keyup.enter="onSearch" @keyup.esc="onClose"
			@input="onInput" @keydown.down.prevent="onDownKey" @keydown.up.prevent="onUpKey"/>
		<div class="p-1 hover:cursor-pointer">
			<search-icon @click.stop="onSearch" class="w-8 h-8"/>
		</div>
		<div class="absolute top-[100%] w-full overflow-hidden" :style="suggContainerStyles">
			<div v-for="(sugg, idx) of searchSuggs" :key="sugg.name + '|' + sugg.canonicalName"
				:style="{backgroundColor: idx == focusedSuggIdx ? store.color.bgAltDark : store.color.bgAlt}"
				class="border-b p-1 px-2 hover:underline hover:cursor-pointer flex"
				@click="resolveSearch(sugg.canonicalName || sugg.name)">
				<div class="grow overflow-hidden whitespace-nowrap text-ellipsis">
					<span>{{suggDisplayStrings[idx][0]}}</span>
					<span class="font-bold text-lime-600">{{suggDisplayStrings[idx][1]}}</span>
					<span>{{suggDisplayStrings[idx][2]}}</span>
					<span class="text-stone-500">{{suggDisplayStrings[idx][3]}}</span>
				</div>
				<info-icon class="hover:cursor-pointer my-auto w-5 h-5"
					@click.stop="onInfoIconClick(sugg.canonicalName || sugg.name)"/>
			</div>
			<div v-if="searchHadMoreSuggs" class="text-center">&#x2022; &#x2022; &#x2022;</div>
		</div>
		<label :style="animateLabelStyles" class="flex gap-1">
			<input type="checkbox" v-model="store.searchJumpMode" @change="emit('setting-chg', 'searchJumpMode')"/>
			<div class="text-sm">Jump to result</div>
		</label>
	</div>
</div>
</template>

<script setup lang="ts">
import {ref, computed, onMounted, onUnmounted, PropType} from 'vue';
import SearchIcon from './icon/SearchIcon.vue';
import InfoIcon from './icon/InfoIcon.vue';
import {TolNode, TolMap} from '../tol';
import {LayoutNode, LayoutMap} from '../layout';
import {queryServer, SearchSugg, SearchSuggResponse} from '../lib';
import {useStore} from '../store';

// Refs
const rootRef = ref(null as HTMLDivElement | null);
const inputRef = ref(null as HTMLInputElement | null);

// Global store
const store = useStore();

// Props + events
const props = defineProps({
	lytMap: {type: Object as PropType<LayoutMap>, required: true}, // Used to check if a searched-for node exists
	activeRoot: {type: Object as PropType<LayoutNode>, required: true}, // Sent to server to reduce response size
	tolMap: {type: Object as PropType<TolMap>, required: true}, // Upon a search response, gets new nodes added
});
const emit = defineEmits(['search', 'close', 'info-click', 'setting-chg', 'net-wait', 'net-get']);

// Search-suggestion data
const searchSuggs = ref([] as SearchSugg[]);
const searchHadMoreSuggs = ref(false);
const suggDisplayStrings = computed((): [string, string, string, string][] => {
	let result: [string, string, string, string][] = [];
	let input = suggsInput.value.toLowerCase();
	// For each SearchSugg
	for (let sugg of searchSuggs.value){
		let idx = sugg.name.indexOf(input);
		// Split suggestion text into parts before/within/after an input match
		let strings: [string, string, string, string];
		if (idx != -1){
			strings = [sugg.name.substring(0, idx), input, sugg.name.substring(idx + input.length), ''];
		} else {
			strings = [input, '', '', ''];
		}
		// Indicate any distinct canonical-name
		if (sugg.canonicalName != null){
			strings[3] = ` (aka ${sugg.canonicalName})`;
		}
		//
		result.push(strings);
	}
	return result;
});
const suggsInput = ref(''); // The input that resulted in the current suggestions (used to highlight matching text)
const focusedSuggIdx = ref(null as null | number); // Index of a search-suggestion selected using the arrow keys

// For search-suggestion requests
const lastSuggReqTime = ref(0); // Set when a search-suggestions request is initiated
const pendingSuggReqParams = ref(null as null | URLSearchParams);
	// Used by a search-suggestion requester to request with the latest user input
const pendingDelayedSuggReq = ref(0); // Set via setTimeout() for a non-initial search-suggestions request
const pendingSuggInput = ref(''); // Used to remember what input triggered a suggestions request
async function onInput(){
	let input = inputRef.value!;
	// Check for empty input
	if (input.value.length == 0){
		searchSuggs.value = [];
		searchHadMoreSuggs.value = false;
		focusedSuggIdx.value = null;
		return;
	}
	// Get URL params to use for querying search-suggestions
	let urlParams = new URLSearchParams({
		type: 'sugg',
		name: input.value,
		limit: String(store.searchSuggLimit),
		tree: store.tree,
	});
	// Query server, delaying/skipping if a request was recently sent
	pendingSuggReqParams.value = urlParams;
	pendingSuggInput.value = input.value;
	let doReq = async () => {
		let suggInput = pendingSuggInput.value;
		let responseObj: SearchSuggResponse =
			await queryServer(pendingSuggReqParams.value!);
		if (responseObj == null){
			return;
		}
		searchSuggs.value = responseObj.suggs;
		searchHadMoreSuggs.value = responseObj.hasMore;
		suggsInput.value = suggInput;
		// Auto-select first result if present
		if (searchSuggs.value.length > 0){
			focusedSuggIdx.value = 0;
		} else {
			focusedSuggIdx.value = null;
		}
	};
	let currentTime = new Date().getTime();
	if (lastSuggReqTime.value == 0){
		lastSuggReqTime.value = currentTime;
		await doReq();
		if (lastSuggReqTime.value == currentTime){
			lastSuggReqTime.value = 0;
		}
	} else if (pendingDelayedSuggReq.value == 0){
		lastSuggReqTime.value = currentTime;
		pendingDelayedSuggReq.value = setTimeout(async () => {
			pendingDelayedSuggReq.value = 0;
			await doReq();
			if (lastSuggReqTime.value == currentTime){
				lastSuggReqTime.value = 0;
			}
		}, 300);
	}
}

// For search events
function onSearch(){
	if (focusedSuggIdx.value == null){
		let input = inputRef.value!.value.toLowerCase();
		resolveSearch(input)
	} else {
		let sugg = searchSuggs.value[focusedSuggIdx.value]
		resolveSearch(sugg.canonicalName || sugg.name);
	}
}
async function resolveSearch(tolNodeName: string){
	if (tolNodeName == ''){
		return;
	}
	// Check if the node data is already here
	if (props.lytMap.has(tolNodeName)){
		emit('search', tolNodeName);
		return;
	}
	// Ask server for nodes in parent-chain, updates tolMap, then emits search event
	let urlParams = new URLSearchParams({
		type: 'node',
		name: tolNodeName,
		toroot: '1',
		excl: props.activeRoot.name,
		tree: store.tree,
	});
	emit('net-wait'); // Allows the parent component to show a loading-indicator
	let responseObj: {[x: string]: TolNode} = await queryServer(urlParams);
	emit('net-get');
	if (responseObj == null){
		return;
	}
	let keys = Object.getOwnPropertyNames(responseObj);
	if (keys.length > 0){
		keys.forEach(key => {
			if (!props.tolMap.has(key)){
				props.tolMap.set(key, responseObj[key])
			}
		});
		emit('search', tolNodeName);
	} else {
		// Trigger failure animation
		let input = inputRef.value!;
		input.classList.remove('animate-red-then-fade');
		input.offsetWidth; // Triggers reflow
		input.classList.add('animate-red-then-fade');
	}
}

// More event handling
function onClose(evt: Event){
	if (evt.target == rootRef.value){
		emit('close');
	}
}
function onDownKey(){
	if (focusedSuggIdx.value != null){
		focusedSuggIdx.value = (focusedSuggIdx.value + 1) % searchSuggs.value.length;
	}
}
function onUpKey(){
	if (focusedSuggIdx.value != null){
		focusedSuggIdx.value = (focusedSuggIdx.value - 1 + searchSuggs.value.length) % searchSuggs.value.length;
			// The addition after '-1' is to avoid becoming negative
	}
}
function onInfoIconClick(nodeName: string){
	emit('info-click', nodeName);
}

// For keyboard shortcuts
function onKeyDown(evt: KeyboardEvent){
	if (store.disableShortcuts){
		return;
	}
	if (evt.key == 'f' && evt.ctrlKey){
		evt.preventDefault();
		inputRef.value!.focus();
	}
}
onMounted(() => window.addEventListener('keydown', onKeyDown))
onUnmounted(() => window.removeEventListener('keydown', onKeyDown))

// Focus input on mount
onMounted(() => inputRef.value!.focus())

// Styles
const styles = computed((): Record<string,string> => {
	let br = store.borderRadius;
	return {
		backgroundColor: store.color.bgAlt,
		borderRadius: (searchSuggs.value.length == 0) ? `${br}px` : `${br}px ${br}px 0 0`,
		boxShadow: store.shadowNormal,
	};
});
const suggContainerStyles = computed((): Record<string,string> => {
	let br = store.borderRadius;
	return {
		backgroundColor: store.color.bgAlt,
		color: store.color.textAlt,
		borderRadius: `0 0 ${br}px ${br}px`,
	};
});
const animateLabelStyles = computed(() => ({
	position: 'absolute',
	top: -store.lytOpts.headerSz - 2 + 'px',
	right: '0',
	height: store.lytOpts.headerSz + 'px',
	color: store.color.text,
}));
</script>
