<script lang="ts">
import {defineComponent, PropType} from 'vue';
import CloseIcon from './icon/CloseIcon.vue';
import Tile from './Tile.vue'
import {LayoutNode} from '../layout';
import type {LayoutOptions} from '../layout';
import type {TolMap} from '../tol';
import {TolNode} from '../tol';
import {capitalizeWords} from '../util';

type DescInfo = {text: string, fromRedirect: boolean, wikiId: number, fromDbp: boolean};
type ImgInfo = {eolId: string, sourceUrl: string, license: string, copyrightOwner: string}
type TileInfoResponse = {
	tolNode: null | TolNode,
	descData: null | DescInfo | [DescInfo, DescInfo],
	imgData: null | ImgInfo | [ImgInfo, ImgInfo],
};

// Displays information about a tree-of-life node
export default defineComponent({
	data(){
		return {
			tolNode: null as null | TolNode,
			descData: null as null | DescInfo | [DescInfo, DescInfo],
			imgData: null as null | ImgInfo | [ImgInfo, ImgInfo],
		};
	},
	props: {
		nodeName: {type: String, required: true},
		tolMap: {type: Object as PropType<TolMap>, required: true},
		lytOpts: {type: Object as PropType<LayoutOptions>, required: true},
		uiOpts: {type: Object, required: true},
	},
	computed: {
		displayName(): string {
			if (this.tolNode == null || this.tolNode.commonName == null){
				return capitalizeWords(this.nodeName);
			} else {
				return `${capitalizeWords(this.tolNode.commonName)} (aka ${capitalizeWords(this.nodeName)})`;
			}
		},
		subName1(): string {
			return this.displayName.substring(1, this.displayName.indexOf(' + '));
		},
		subName2(): string {
			return this.displayName.substring(this.displayName.indexOf(' + ') + 3, this.displayName.length - 1);
		},
		dummyNode(): LayoutNode {
			let newNode = new LayoutNode(this.nodeName, []);
			newNode.dims = [this.uiOpts.infoModalImgSz, this.uiOpts.infoModalImgSz];
			return newNode;
		},
	},
	methods: {
		onCloseClick(evt: Event){
			if (evt.target == this.$el || (this.$refs.closeIcon as typeof CloseIcon).$el.contains(evt.target)){
				this.$emit('info-modal-close');
			}
		},
	},
	created(){
		let url = new URL(window.location.href);
		url.pathname = '/data/info';
		url.search = '?name=' + encodeURIComponent(this.nodeName);
		url.search += this.uiOpts.useReducedTree ? '&tree=reduced' : '';
		fetch(url.toString())
			.then(response => response.json())
			.then(obj => {
				if (obj != null){
					this.tolNode = obj.nodeObj;
					this.descData = obj.descData;
					this.imgData = obj.imgData;
				}
			});
	},
	components: {CloseIcon, Tile, },
	emits: ['info-modal-close', ],
});
</script>

<template>
<div class="fixed left-0 top-0 w-full h-full bg-black/40" @click="onCloseClick">
	<div class="absolute left-1/2 -translate-x-1/2 w-4/5 max-h-[80%] overflow-y-auto top-1/2 -translate-y-1/2 p-4
		bg-stone-50 rounded-md shadow shadow-black">
		<close-icon @click.stop="onCloseClick" ref="closeIcon"
			class="block absolute top-2 right-2 w-6 h-6 hover:cursor-pointer"/>
		<h1 class="text-center text-xl font-bold mb-2">
			{{displayName}}
			<div v-if="tolNode != null">
				({{tolNode.children.length}} children, {{tolNode.tips}} tips)
			</div>
		</h1>
		<hr class="mb-4 border-stone-400"/>
		<div class="flex">
			<div>
				<tile :layoutNode="dummyNode" :tolMap="tolMap" :nonAbsPos="true" :lytOpts="lytOpts" :uiOpts="uiOpts"
					class="mr-4"/>
				<div v-if="imgData == null">
					(No image found)
				</div>
				<div v-else-if="!Array.isArray(imgData)">
					<ul>
						<li>License: {{imgData.license}}</li>
						<li><a :href="imgData.sourceUrl" class="underline">Source URL</a></li>
						<li>Copyright Owner: {{imgData.copyrightOwner}}</li>
					</ul>
				</div>
				<div v-else>
					<div v-if="imgData[0] != null">
						<h2 class="font-bold">Top-left Image</h2>
						<ul>
							<li>License: {{imgData[0].license}}</li>
							<li><a :href="imgData[0].sourceUrl" class="underline">Source URL</a></li>
							<li>Copyright Owner: {{imgData[0].copyrightOwner}}</li>
						</ul>
					</div>
					<div v-if="imgData[1] != null">
						<h2 class="font-bold">Bottom-right Image</h2>
						<ul>
							<li>License: {{imgData[1].license}}</li>
							<li><a :href="imgData[1].sourceUrl" class="underline">Source URL</a></li>
							<li>Copyright Owner: {{imgData[1].copyrightOwner}}</li>
						</ul>
					</div>
				</div>
			</div>
			<div v-if="descData == null">
				(No description found)
			</div>
			<div v-else-if="!Array.isArray(descData)">
				<div>
					Redirected: {{descData.fromRedirect}} <br/>
					Short-description from {{descData.fromDbp ? 'DBpedia' : 'Wikipedia'}} <br/>
					<a :href="'https://en.wikipedia.org/?curid=' + descData.wikiId" class="underline">
						Wikipedia Link
					</a>
				</div>
				<hr/>
				<div>{{descData.text}}</div>
			</div>
			<div v-else>
				<div>
					<h2 class="font-bold">{{subName1}}</h2>
					<div>{{descData[0].text}}</div>
				</div>
				<div>
					<h2 class="font-bold">{{subName2}}</h2>
					<div>{{descData[1].text}}</div>
				</div>
			</div>
		</div>
		
	</div>
</div>
</template>
