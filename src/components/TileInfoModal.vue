<script lang="ts">
import {defineComponent, PropType} from 'vue';
import CloseIcon from './icon/CloseIcon.vue';
import {LayoutNode} from '../layout';
import type {TolMap} from '../tol';
import {TolNode} from '../tol';
import {capitalizeWords} from '../util';

// Displays information about a tree-of-life node
export default defineComponent({
	data(){
		return {
			tolNode: null as null | TolNode,
			descObj: null as null | {text: string, fromRedirect: boolean, wikiId: number, fromDbp: boolean},
			imgInfo: null as null | {eolId: string, sourceUrl: string, license: string, copyrightOwner: string},
		};
	},
	props: {
		nodeName: {type: String, required: true},
		tolMap: {type: Object as PropType<TolMap>, required: true},
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
		imgStyles(): Record<string,string> {
			return {
				backgroundImage: this.tolNode != null && this.tolNode.imgName != null ?
					'linear-gradient(to bottom, rgba(0,0,0,0.4), #0000 40%, #0000 60%, rgba(0,0,0,0.4) 100%),' +
						'url(\'/img/' + this.tolNode.imgName.replaceAll('\'', '\\\'') + '\')' :
					'none',
				backgroundColor: '#1c1917',
				width: this.uiOpts.infoModalImgSz + 'px',
				height: this.uiOpts.infoModalImgSz + 'px',
				backgroundSize: 'cover',
				borderRadius: this.uiOpts.borderRadius + 'px',
			};
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
					this.descObj = obj.descObj;
					this.imgInfo = obj.imgInfo;
				}
			});
	},
	components: {CloseIcon, },
	emits: ['info-modal-close', ],
});
</script>

<template>
<div class="fixed left-0 top-0 w-full h-full bg-black/40" @click="onCloseClick">
	<div class="absolute left-1/2 -translate-x-1/2 w-4/5 top-1/2 -translate-y-1/2 p-4
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
				<div :style="imgStyles" class="mr-4" alt="an image"></div>
				<div v-if="imgInfo != null">
					<ul>
						<li>License: {{imgInfo.license}}</li>
						<li><a :href="imgInfo.sourceUrl" class="underline">Source URL</a></li>
						<li>Copyright Owner: {{imgInfo.copyrightOwner}}</li>
					</ul>
				</div>
			</div>
			<div v-if="descObj != null">
				<div>
					Redirected: {{descObj.fromRedirect}} <br/>
					Short-description from {{descObj.fromDbp ? 'DBpedia' : 'Wikipedia'}} <br/>
					<a :href="'https://en.wikipedia.org/?curid=' + descObj.wikiId" class="underline">
						Wikipedia Link
					</a>
				</div>
				<hr/>
				<div>
					{{descObj.text}}
				</div>
			</div>
			<div v-else>
				(No description found)
			</div>
		</div>
		
	</div>
</div>
</template>
