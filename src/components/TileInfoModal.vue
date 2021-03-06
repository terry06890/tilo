<template>
<div class="fixed left-0 top-0 w-full h-full bg-black/40" @click="onClose">
	<div class="absolute left-1/2 -translate-x-1/2 top-1/2 -translate-y-1/2
		max-w-[80%] min-w-[8cm] md:min-w-[14cm] max-h-[80%]" :style="styles">
		<div class="pb-1 md:pb-2">
			<close-icon @click.stop="onClose" ref="closeIcon"
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
				<div>
					<a :href="'https://tree.opentreeoflife.org/opentree/argus/opentree13.4@' + tolNode.otolId"
						target="_blank" title="Look up in Open Tree of Life">OTOL <external-link-icon class="inline-block w-3 h-3"/></a>
				</div>
			</div>
			<div v-if="nodes.length > 1" class="text-center text-sm px-2">
				<div> (This is a compound node. The details below describe two descendants) </div>
			</div>
		</div>
		<div v-for="idx in (nodes.length == 1 ? [0] : [0, 1])" :key="nodes[idx]!.otolId!"
			class="border-t border-stone-400 p-2 md:p-3 clear-both">
			<h1 v-if="nodes.length > 1" class="text-center font-bold mb-1">
				{{getDisplayName(subNames![idx], nodes[idx])}}
			</h1>
			<div v-if="nodes[idx] == null" class="text-center">
				(This node was trimmed away duing tree simplification)
			</div>
			<div v-else>
				<div v-if="imgInfos[idx] != null" class="mt-1 mr-2 md:mb-2 md:mr-4 md:float-left">
					<a :href="imgInfos[idx]!.url != '' ? imgInfos[idx]!.url : 'javascript:;'"
						:target="imgInfos[idx]!.url != '' ? '_blank' : ''" class="block w-fit mx-auto">
						<div :style="getImgStyles(nodes[idx])"/>
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
								:style="{backgroundColor: uiOpts.bgColor, color: uiOpts.textColor}">
								<li v-if="imgInfos[idx]!.url != ''">
									<span :style="{color: uiOpts.altColor}">Source: </span>
									<a :href="imgInfos[idx]!.url" target="_blank">Link</a>
									<external-link-icon class="inline-block w-3 h-3 ml-1"/>
								</li>
								<li v-if="imgInfos[idx]!.artist != ''" class="whitespace-nowrap">
									<span :style="{color: uiOpts.altColor}">Artist: </span>
									{{imgInfos[idx]!.artist}}
								</li>
								<li v-if="imgInfos[idx]!.credit != ''" class="whitespace-nowrap">
									<span :style="{color: uiOpts.altColor}">Credits: </span>
									{{imgInfos[idx]!.credit}}
								</li>
								<li>
									<span :style="{color: uiOpts.altColor}">License: </span>
									<a :href="licenseToUrl(imgInfos[idx]!.license)" target="_blank">
										{{imgInfos[idx]!.license}}
									</a>
									<external-link-icon class="inline-block w-3 h-3 ml-1"/>
								</li>
								<li v-if="imgInfos[idx]!.src != 'picked'">
									<span :style="{color: uiOpts.altColor}">Obtained via: </span>
									<a v-if="imgInfos[idx]!.src == 'eol'" href="https://eol.org/">EoL</a>
									<a v-else href="https://www.wikipedia.org/">Wikipedia</a>
									<external-link-icon class="inline-block w-3 h-3 ml-1"/>
								</li>
								<li>
									<span :style="{color: uiOpts.altColor}">Changes: </span>
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
				<div v-else class="text-center">
					(No description found)
				</div>
			</div>
		</div>
	</div>
</div>
</template>

<script lang="ts">
import {defineComponent, PropType} from 'vue';
import SCollapsible from './SCollapsible.vue';
import CloseIcon from './icon/CloseIcon.vue';
import ExternalLinkIcon from './icon/ExternalLinkIcon.vue';
import DownIcon from './icon/DownIcon.vue';
import LinkIcon from './icon/LinkIcon.vue';
import {TolNode, TolMap} from '../tol';
import {LayoutNode, LayoutOptions} from '../layout';
import {getImagePath, DescInfo, ImgInfo, NodeInfo, InfoResponse, UiOptions} from '../lib';
import {capitalizeWords} from '../util';

export default defineComponent({
	props: {
		// Node data to display
		nodeName: {type: String, required: true},
		infoResponse: {type: Object as PropType<InfoResponse>, required: true},
		// Options
		lytOpts: {type: Object as PropType<LayoutOptions>, required: true},
		uiOpts: {type: Object as PropType<UiOptions>, required: true},
	},
	data(){
		return {
			linkCopied: false, // Used to temporarily show a 'link copied' label
		};
	},
	computed: {
		tolNode(): TolNode {
			return this.infoResponse.nodeInfo.tolNode;
		},
		nodes(): (TolNode | null)[] {
			if (this.infoResponse.subNodesInfo.length == 0){
				return [this.tolNode];
			} else {
				return this.infoResponse.subNodesInfo.map(nodeInfo => nodeInfo != null ? nodeInfo.tolNode : null);
			}
		},
		imgInfos(): (ImgInfo | null)[] {
			if (this.infoResponse.subNodesInfo.length == 0){
				return [this.infoResponse.nodeInfo.imgInfo];
			} else {
				return this.infoResponse.subNodesInfo.map(nodeInfo => nodeInfo != null ? nodeInfo.imgInfo : null);
			}
		},
		descInfos(): (DescInfo | null)[] {
			if (this.infoResponse.subNodesInfo.length == 0){
				return [this.infoResponse.nodeInfo.descInfo];
			} else {
				return this.infoResponse.subNodesInfo.map(nodeInfo => nodeInfo != null ? nodeInfo.descInfo : null);
			}
		},
		subNames(): [string, string] | null {
			const regex = /\[(.+) \+ (.+)\]/;
			let results = regex.exec(this.nodeName);
			return results == null ? null : [results[1], results[2]];
		},
		styles(): Record<string,string> {
			return {
				backgroundColor: this.uiOpts.bgColorAlt,
				borderRadius: this.uiOpts.borderRadius + 'px',
				boxShadow: this.uiOpts.shadowNormal,
				overflow: 'visible auto',
			};
		},
		linkCopyLabelStyles(): Record<string,string> {
			return {
				color: this.uiOpts.textColor,
				backgroundColor: this.uiOpts.bgColor,
				borderRadius: this.uiOpts.borderRadius + 'px',
			};
		},
	},
	methods: {
		getDisplayName(name: string, tolNode: TolNode | null): string {
			if (tolNode == null || tolNode.commonName == null){
				return capitalizeWords(name);
			} else {
				return `${capitalizeWords(tolNode.commonName)} (aka ${capitalizeWords(name)})`;
			}
		},
		getImgStyles(tolNode: TolNode | null): Record<string,string> {
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
				backgroundColor: this.uiOpts.bgColorDark,
				backgroundSize: 'cover',
				borderRadius: this.uiOpts.borderRadius + 'px',
				boxShadow: this.uiOpts.shadowNormal,
			};
		},
		licenseToUrl(license: string){
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
		},
		onClose(evt: Event){
			if (evt.target == this.$el || (this.$refs.closeIcon as typeof CloseIcon).$el.contains(evt.target)){
				this.$emit('close');
			}
		},
		onLinkIconClick(evt: Event){
			// Copy link to clipboard
			let url = new URL(window.location.href);
			url.search = (new URLSearchParams({node: this.nodeName})).toString();
			navigator.clipboard.writeText(url.toString());
			// Show visual indicator
			this.linkCopied = true;
			setTimeout(() => {this.linkCopied = false}, 1500);
		},
	},
	components: {SCollapsible, CloseIcon, ExternalLinkIcon, DownIcon, LinkIcon, },
	emits: ['close', ],
});
</script>
