<script lang="ts">
import {defineComponent, PropType} from 'vue';
import CloseIcon from './icon/CloseIcon.vue';
import Tile from './Tile.vue'
import {LayoutNode} from '../layout';
import type {LayoutOptions} from '../layout';
import type {TolMap} from '../tol';
import {TolNode} from '../tol';
import {capitalizeWords} from '../lib';

type DescInfo = {text: string, fromRedirect: boolean, wikiId: number, fromDbp: boolean};
type ImgInfo = {imgId: number, imgSrc: 'eol' | 'enwiki', url: string, license: string, artist: string, credit: string}
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
			descInfo: null as null | DescInfo,
			descInfo1: null as null | DescInfo,
			descInfo2: null as null | DescInfo,
			imgInfo: null as null | ImgInfo,
			imgInfo1: null as null | ImgInfo,
			imgInfo2: null as null | ImgInfo,
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
		imgStyles(): Record<string,string> {
			return this.getImgStyles(this.tolNode == null ? null : this.tolNode.imgName as string);
		},
		firstImgStyles(): Record<string,string> {
			return this.getImgStyles(this.tolNode!.imgName![0]);
		},
		secondImgStyles(): Record<string,string> {
			return this.getImgStyles(this.tolNode!.imgName![1]);
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
		getImgStyles(imgName: string | null){
			return {
				boxShadow: this.uiOpts.shadowNormal,
				borderRadius: this.uiOpts.borderRadius + 'px',
				backgroundImage: imgName != null ?
					'linear-gradient(to bottom, rgba(0,0,0,0.4), #0000 40%, #0000 60%, rgba(0,0,0,0.4) 100%),' +
						'url(\'/img/' + imgName.replaceAll('\'', '\\\'') + '\')' :
					'none',
				backgroundColor: '#1c1917',
				backgroundSize: 'cover',
				width: this.uiOpts.infoModalImgSz + 'px',
				height: this.uiOpts.infoModalImgSz + 'px',
			};
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
					if (!Array.isArray(obj.descData)){
						this.descInfo = obj.descData;
					} else {
						[this.descInfo1, this.descInfo2] = obj.descData;
					}
					if (!Array.isArray(obj.imgData)){
						this.imgInfo = obj.imgData;
					} else {
						[this.imgInfo1, this.imgInfo2] = obj.imgData;
					}
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
				({{tolNode.children.length}} children, {{tolNode.tips}} tips,
					<a :href="'https://tree.opentreeoflife.org/opentree/argus/opentree13.4@' + tolNode.otolId">
						{{tolNode.otolId}}</a>)
			</div>
		</h1>
		<hr class="mb-4 border-stone-400"/>
		<div class="flex">
			<div class="mr-4">
				<div v-if="tolNode == null"/>
				<div v-else-if="!Array.isArray(tolNode.imgName)">
					<div :style="imgStyles"/>
					<ul v-if="imgInfo != null">
						<li>Obtained via: {{imgInfo.imgSrc}}</li>
						<li>License: {{imgInfo.license}}</li>
						<li><a :href="imgInfo.url" class="underline">Source URL</a></li>
						<li>Artist: {{imgInfo.artist}}</li>
						<li v-if="imgInfo.credit != ''">Credit: {{imgInfo.credit}}</li>
					</ul>
				</div>
				<div v-else>
					<div v-if="tolNode.imgName[0] != null" :style="firstImgStyles"/>
					<ul v-if="imgInfo1 != null">
						<li>Obtained via: {{imgInfo1.imgSrc}}</li>
						<li>License: {{imgInfo1.license}}</li>
						<li><a :href="imgInfo1.url" class="underline">Source URL</a></li>
						<li>Artist: {{imgInfo1.artist}}</li>
						<li v-if="imgInfo1.credit != ''">Credit: {{imgInfo1.credit}}</li>
					</ul>
					<div v-if="tolNode.imgName[1] != null" :style="secondImgStyles"/>
					<ul v-if="imgInfo2 != null">
						<li>Obtained via: {{imgInfo2.imgSrc}}</li>
						<li>License: {{imgInfo2.license}}</li>
						<li><a :href="imgInfo2.url" class="underline">Source URL</a></li>
						<li>Artist: {{imgInfo2.artist}}</li>
						<li v-if="imgInfo2.credit != ''">Credit: {{imgInfo2.credit}}</li>
					</ul>
				</div>
			</div>
			<div v-if="descInfo == null && descInfo1 == null && descInfo2 == null">
				(No description found)
			</div>
			<div v-else-if="descInfo != null">
				<div>
					Redirected: {{descInfo.fromRedirect}} <br/>
					Short-description from {{descInfo.fromDbp ? 'DBpedia' : 'Wikipedia'}} <br/>
					<a :href="'https://en.wikipedia.org/?curid=' + descInfo.wikiId" class="underline">
						Wikipedia Link
					</a>
				</div>
				<hr/>
				<div>{{descInfo.text}}</div>
			</div>
			<div v-else>
				<div>
					<h2 class="font-bold">{{subName1}}</h2>
					<div v-if="descInfo1 != null">{{descInfo1.text}}</div>
					<div v-else>(No description found)</div>
				</div>
				<div>
					<h2 class="font-bold">{{subName2}}</h2>
					<div v-if="descInfo2 != null">{{descInfo2.text}}</div>
					<div v-else>(No description found)</div>
				</div>
			</div>
		</div>
		
	</div>
</div>
</template>
