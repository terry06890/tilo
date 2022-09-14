<template>
<div class="fixed left-0 top-0 w-full h-full bg-black/40" @click="onClose" ref="rootRef">
	<div class="absolute left-1/2 -translate-x-1/2 top-1/2 -translate-y-1/2
		max-w-[80%] w-2/3 min-w-[8cm] md:w-[14cm] lg:w-[16cm] max-h-[80%]" :style="styles">
		<div class="pb-1 md:pb-2">
			<close-icon @click.stop="onClose" ref="closeRef"
				class="absolute top-1 right-1 md:top-2 md:right-2 w-8 h-8 hover:cursor-pointer"/>
			<div class="absolute top-1 left-1 md:top-2 md:left-2 flex items-center">
				<a :href="'/?node=' + encodeURIComponent(nodeName)" class="block w-8 h-8 p-[2px] hover:cursor-pointer"
					@click.prevent="onLinkIconClick" title="Copy link to this node">
					<link-icon/>
				</a>
				<transition name="fadeslow">
					<div v-if="linkCopied" class="text-sm p-1 ml-2" :style="linkCopyLabelStyles">Link Copied</div>
				</transition>
			</div>
			<h1 class="text-center text-xl font-bold pt-2 pb-1 mx-10 md:text-2xl md:pt-3 md:pb-1">
				{{getDisplayName(nodeName, tolNode)}}
			</h1>
			<div class="flex justify-evenly text-sm md:text-base">
				<div> Children: {{(tolNode.children.length).toLocaleString()}} </div>
				<div> Tips: {{(tolNode.tips).toLocaleString()}} </div>
				<div v-if="tolNode.iucn != null">
					<a href="https://en.wikipedia.org/wiki/Endangered_species_(IUCN_status)"
						target="_blank" title="IUCN Conservation Status">IUCN</a>:
					<span :style="iucnStyles(tolNode.iucn)">{{getDisplayIucn(tolNode.iucn)}}</span>
				</div>
				<div>
					<a :href="'https://tree.opentreeoflife.org/opentree/argus/opentree13.4@' + tolNode.otolId"
						target="_blank" title="Look up in Open Tree of Life">OTOL <external-link-icon class="inline-block w-3 h-3"/></a>
				</div>
			</div>
			<div v-if="nodes.length > 1" class="text-center text-sm px-2">
				<div> (This is a compound node. The details below describe two descendants) </div>
			</div>
		</div>
		<div v-for="(node, idx) in nodes" :key="node == null ? -1 : node.otolId!"
			class="border-t border-stone-400 p-2 md:p-3 clear-both">
			<h1 v-if="nodes.length > 1" class="text-center font-bold mb-1">
				{{getDisplayName(subNames![idx], node)}}
			</h1>
			<div v-if="node == null" class="text-center text-sm text-stone-500">
				(This node was trimmed away duing tree simplification)
			</div>
			<div v-else>
				<div v-if="imgInfos[idx] != null" class="mt-1 mr-2 md:mb-2 md:mr-4 md:float-left">
					<a :href="imgInfos[idx]!.url != '' ? imgInfos[idx]!.url : 'javascript:;'"
						:target="imgInfos[idx]!.url != '' ? '_blank' : ''" class="block w-fit mx-auto">
						<div :style="getImgStyles(node)"/>
					</a>
					<s-collapsible class="text-sm text-center w-fit max-w-full md:max-w-[200px] mx-auto">
						<template v-slot:summary="slotProps">
							<div class="py-1 hover:underline">
								<down-icon class="inline-block w-4 h-4 mr-1 transition-transform duration-300"
									:class="{'-rotate-90': slotProps.open}"/>
								Image Source
							</div>
						</template>
						<template v-slot:content>
							<ul class="rounded shadow overflow-x-auto p-1"
								:style="{backgroundColor: store.color.bg, color: store.color.text}">
								<li v-if="imgInfos[idx]!.url != ''">
									<span :style="{color: store.color.alt}">Source: </span>
									<a :href="imgInfos[idx]!.url" target="_blank">Link</a>
									<external-link-icon class="inline-block w-3 h-3 ml-1"/>
								</li>
								<li v-if="imgInfos[idx]!.artist != ''" class="whitespace-nowrap">
									<span :style="{color: store.color.alt}">Artist: </span>
									{{imgInfos[idx]!.artist}}
								</li>
								<li v-if="imgInfos[idx]!.credit != ''" class="whitespace-nowrap">
									<span :style="{color: store.color.alt}">Credits: </span>
									{{imgInfos[idx]!.credit}}
								</li>
								<li>
									<span :style="{color: store.color.alt}">License: </span>
									<a :href="licenseToUrl(imgInfos[idx]!.license)" target="_blank">
										{{imgInfos[idx]!.license}}
									</a>
									<external-link-icon class="inline-block w-3 h-3 ml-1"/>
								</li>
								<li v-if="imgInfos[idx]!.src != 'picked'">
									<span :style="{color: store.color.alt}">Obtained via: </span>
									<a v-if="imgInfos[idx]!.src == 'eol'" href="https://eol.org/">EoL</a>
									<a v-else href="https://www.wikipedia.org/">Wikipedia</a>
									<external-link-icon class="inline-block w-3 h-3 ml-1"/>
								</li>
								<li>
									<span :style="{color: store.color.alt}">Changes: </span>
									Cropped and resized
								</li>
							</ul>
						</template>
					</s-collapsible>
				</div>
				<div v-if="descInfos[idx]! != null">
					<div>{{descInfos[idx]!.text}}</div>
					<div class="text-sm text-right">
						<a :href="'https://en.wikipedia.org/?curid=' + descInfos[idx]!.wikiId"
							target="_blank">From Wikipedia</a>
						<external-link-icon class="inline-block w-3 h-3 ml-1"/>
						{{descInfos[idx]!.fromDbp ? '(via DBpedia)' : ''}}
					</div>
				</div>
				<div v-else class="text-center text-stone-500 text-sm">
					(No description found)
				</div>
			</div>
		</div>
	</div>
</div>
</template>

<script setup lang="ts">
import {ref, computed, PropType} from 'vue';
import SCollapsible from './SCollapsible.vue';
import CloseIcon from './icon/CloseIcon.vue';
import ExternalLinkIcon from './icon/ExternalLinkIcon.vue';
import DownIcon from './icon/DownIcon.vue';
import LinkIcon from './icon/LinkIcon.vue';
import {TolNode} from '../tol';
import {getImagePath, DescInfo, ImgInfo, InfoResponse} from '../lib';
import {capitalizeWords} from '../util';
import {useStore} from '../store';

// Refs
const rootRef = ref(null as HTMLDivElement | null);
const closeRef = ref(null as typeof CloseIcon | null);

// Global store
const store = useStore();

// Props + events
const props = defineProps({
	nodeName: {type: String, required: true},
	infoResponse: {type: Object as PropType<InfoResponse>, required: true},
});
const emit = defineEmits(['close']);

// InfoResponse computed data
const tolNode = computed(() => props.infoResponse.nodeInfo.tolNode);
const nodes = computed((): (TolNode | null)[] => {
	if (props.infoResponse.subNodesInfo.length == 0){
		return [tolNode.value];
	} else {
		return props.infoResponse.subNodesInfo.map(nodeInfo => nodeInfo != null ? nodeInfo.tolNode : null);
	}
});
const imgInfos = computed((): (ImgInfo | null)[] => {
	if (props.infoResponse.subNodesInfo.length == 0){
		return [props.infoResponse.nodeInfo.imgInfo];
	} else {
		return props.infoResponse.subNodesInfo.map(nodeInfo => nodeInfo != null ? nodeInfo.imgInfo : null);
	}
});
const descInfos = computed((): (DescInfo | null)[] => {
	if (props.infoResponse.subNodesInfo.length == 0){
		return [props.infoResponse.nodeInfo.descInfo];
	} else {
		return props.infoResponse.subNodesInfo.map(nodeInfo => nodeInfo != null ? nodeInfo.descInfo : null);
	}
});
const subNames = computed((): [string, string] | null => {
	const regex = /\[(.+) \+ (.+)\]/;
	let results = regex.exec(props.nodeName);
	return results == null ? null : [results[1], results[2]];
});

// InfoResponse data converters
function getDisplayName(name: string, tolNode: TolNode | null): string {
	if (tolNode == null || tolNode.commonName == null){
		return capitalizeWords(name);
	} else {
		return `${capitalizeWords(tolNode.commonName)} (aka ${capitalizeWords(name)})`;
	}
}
function getDisplayIucn(iucn: string){
	switch (iucn){
		case 'least concern': return 'LC';
		case 'near threatened': return 'NT';
		case 'vulnerable': return 'VN';
		case 'endangered': return 'EN';
		case 'critically endangered': return 'CR';
		case 'extinct in the wild': return 'EX';
		case 'extinct species': return 'ES';
		case 'data deficient': return 'DD';
	}
}
function licenseToUrl(license: string){
	license = license.toLowerCase().replaceAll('-', ' ');
	if (license == 'cc0'){
		return 'https://creativecommons.org/publicdomain/zero/1.0/';
	} else if (license == 'cc publicdomain'){
		return 'https://creativecommons.org/licenses/publicdomain/';
	} else {
		const regex = /cc by( nc)?( sa)?( ([0-9.]+)( [a-z]+)?)?/;
		let results = regex.exec(license);
		if (results != null){
			let url = 'https://creativecommons.org/licenses/by';
			if (results[1] != null){
				url += '-nc';
			}
			if (results[2] != null){
				url += '-sa';
			}
			if (results[4] != null){
				url += '/' + results[4];
			} else {
				url += '/4.0';
			}
			if (results[5] != null){
				url += '/' + results[5].substring(1);
			}
			return url;
		}
		return "[INVALID LICENSE]";
	}
}

// Close handling
function onClose(evt: Event){
	if (evt.target == rootRef.value || closeRef.value!.$el.contains(evt.target)){
		emit('close');
	}
}

// Copy-link handling
const linkCopied = ref(false); // Used to temporarily show a 'link copied' label
function onLinkIconClick(){
	// Copy link to clipboard
	let url = new URL(window.location.href);
	url.search = (new URLSearchParams({node: props.nodeName})).toString();
	navigator.clipboard.writeText(url.toString());
	// Show visual indicator
	linkCopied.value = true;
	setTimeout(() => {linkCopied.value = false}, 1500);
}

// Styles
const styles = computed(() => ({
	backgroundColor: store.color.bgAlt,
	borderRadius: store.borderRadius + 'px',
	boxShadow: store.shadowNormal,
	overflow: 'visible auto',
}));
function getImgStyles(tolNode: TolNode | null): Record<string,string> {
	let imgName = null;
	if (tolNode != null && typeof(tolNode.imgName) === 'string'){ // Exclude string-array case
		imgName = tolNode.imgName;
	}
	return {
		width: '200px',
		height: '200px',
		backgroundImage: imgName != null ?
			`url('${getImagePath(imgName as string)}')` :
			'none',
		backgroundColor: store.color.bgDark,
		backgroundSize: 'cover',
		borderRadius: store.borderRadius + 'px',
		boxShadow: store.shadowNormal,
	};
}
function iucnStyles(iucn: string): Record<string,string>{
	let col = 'currentcolor';
	switch (iucn){
		case 'least concern': col = 'green'; break;
		case 'near threatened': col = 'limegreen'; break;
		case 'vulnerable': col = 'goldenrod'; break;
		case 'endangered': col = 'darkorange'; break;
		case 'critically endangered': col = 'red'; break;
		case 'extinct in the wild':
		case 'extinct species': col = 'gray'; break;
	}
	return {
		color: col,
	};
}
const linkCopyLabelStyles = computed(() => ({
	color: store.color.text,
	backgroundColor: store.color.bg,
	borderRadius: store.borderRadius + 'px',
}));
</script>
