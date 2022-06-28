<template>
<div class="fixed left-0 top-0 w-full h-full bg-black/40" @click="onClose">
	<div class="absolute left-1/2 -translate-x-1/2 top-1/2 -translate-y-1/2 w-4/5 max-h-[80%] p-4" :style="styles">
		<close-icon @click.stop="onClose" ref="closeIcon"
			class="block absolute top-2 right-2 w-6 h-6 hover:cursor-pointer"/>
		<h1 class="text-center text-xl font-bold mb-2">
			{{getDisplayName(nodeName, tolNode)}}
			<div v-if="tolNode != null">
				({{tolNode.children.length}} children, {{tolNode.tips}} tips,
					<a :href="'https://tree.opentreeoflife.org/opentree/argus/opentree13.4@' + tolNode.otolId">
						{{tolNode.otolId}}</a>)
			</div>
		</h1>
		<hr class="mb-4 border-stone-400"/>
		<div v-if="nodes.length > 1">This is a compound node</div>
		<div v-for="idx in (nodes.length == 1 ? [0] : [0, 1])">
			<h1 v-if="nodes.length > 1" class="text-center font-bold">
				{{getDisplayName(subNames![idx], nodes[idx])}}
			</h1>
			<div class="flex gap-1">
				<div class="w-1/2">
					<div v-if="imgInfos[idx] == null" :style="getImgStyles(nodes[idx])"/>
					<a v-else :href="imgInfos[idx].url">
						<div :style="getImgStyles(nodes[idx])"/>
					</a>
					<ul v-if="imgInfos[idx]! != null">
						<li>Obtained via: {{imgInfos[idx]!.src}}</li>
						<li>License:
							<a :href="licenseToUrl(imgInfos[idx]!.license)">{{imgInfos[idx]!.license}}</a>
						</li>
						<li><a :href="imgInfos[idx]!.url" class="underline">Source URL</a></li>
						<li>Artist: {{imgInfos[idx]!.artist}}</li>
						<li v-if="imgInfos[idx]!.credit != ''" class="overflow-auto">
							Credit: {{imgInfos[idx]!.credit}}
						</li>
					</ul>
				</div>
				<div v-if="descInfos[idx]! != null">
					<div>
						Redirected: {{descInfos[idx]!.fromRedirect}} <br/>
						Short-description from {{descInfos[idx]!.fromDbp ? 'DBpedia' : 'Wikipedia'}} <br/>
						<a :href="'https://en.wikipedia.org/?curid=' + descInfos[idx]!.wikiId" class="underline">
							Wikipedia Link
						</a>
					</div>
					<hr/>
					<div>{{descInfos[idx]!.text}}</div>
				</div>
				<div v-else>
					(No description found)
				</div>
			</div>
		</div>
	</div>
</div>
</template>

<script lang="ts">
import {defineComponent, PropType} from 'vue';
import CloseIcon from './icon/CloseIcon.vue';
import {LayoutNode, LayoutOptions} from '../layout';
import {TolNode, TolMap, getServerResponse, getImagePath,
	DescInfo, ImgInfo, NodeInfo, InfoResponse, UiOptions} from '../lib';
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
	computed: {
		tolNode(): TolNode {
			return this.infoResponse.nodeInfo.tolNode;
		},
		nodes(): TolNode[] {
			if (this.infoResponse.subNodesInfo.length == 0){
				return [this.tolNode];
			} else {
				return this.infoResponse.subNodesInfo.map(nodeInfo => nodeInfo.tolNode);
			}
		},
		imgInfos(): (ImgInfo | null)[] {
			if (this.infoResponse.subNodesInfo.length == 0){
				return [this.infoResponse.nodeInfo.imgInfo];
			} else {
				return this.infoResponse.subNodesInfo.map(nodeInfo => nodeInfo.imgInfo);
			}
		},
		descInfos(): (DescInfo | null)[] {
			if (this.infoResponse.subNodesInfo.length == 0){
				return [this.infoResponse.nodeInfo.descInfo];
			} else {
				return this.infoResponse.subNodesInfo.map(nodeInfo => nodeInfo.descInfo);
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
	},
	methods: {
		getDisplayName(name: string, tolNode: TolNode | null): string {
			if (tolNode == null || tolNode.commonName == null){
				return capitalizeWords(name);
			} else {
				return `${capitalizeWords(tolNode.commonName)} (aka ${capitalizeWords(name)})`;
			}
		},
		getImgStyles(tolNode: TolNode): Record<string,string> {
			let imgName = null;
			if (typeof(tolNode.imgName) === 'string'){ // Exclude string-array case
				imgName = tolNode.imgName;
			}
			return {
				width: this.lytOpts.maxTileSz + 'px',
				height: this.lytOpts.maxTileSz + 'px',
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
	},
	components: {CloseIcon, },
	emits: ['close', ],
});
</script>
