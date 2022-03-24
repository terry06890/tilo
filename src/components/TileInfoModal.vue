<script lang="ts">
import {defineComponent, PropType} from 'vue';
import {TolNode} from '../lib';

export default defineComponent({
	props: {
		tolNode: {type: Object as PropType<TolNode | null>}, // The node to display, or null to hide
		options: {type: Object, required: true},
	},
	data(){
		return {
			lastNode: null as TolNode | null, // Caches tolNode to prevent content-change during fade-out
		};
	},
	watch: {
		tolNode(newNode){
			if (newNode != null){
				this.lastNode = newNode;
			}
		},
	},
	computed: {
		transitionStyles(): Record<string,string> {
			return {
				visibility: this.tolNode != null ? 'visible' : 'hidden',
				opacity: this.tolNode != null ? '1' : '0',
				transition: 'visibility, opacity',
				transitionDuration: this.options.transitionDuration + 'ms',
			};
		},
		imgStyles(): Record<string,string> {
			return {
				backgroundImage: this.lastNode == null ? 'none' :
					'url(\'/img/' + this.lastNode.name.replaceAll('\'', '\\\'') + '.png\')',
				width: this.options.infoModalImgSz + 'px',
				height: this.options.infoModalImgSz + 'px',
				backgroundSize: 'cover',
				borderRadius: this.options.borderRadius + 'px',
			}
		},
	},
	methods: {
		closeIconClicked(evt: Event){
			if (evt.target == this.$el || evt.target == this.$refs.closeIcon){
				this.$emit('info-modal-close');
			}
		},
	},
	emits: ['info-modal-close']
});
</script>

<template>
<div :style="transitionStyles" class="fixed left-0 top-0 w-full h-full bg-black/40" @click="closeIconClicked">
	<div class="absolute left-1/2 -translate-x-1/2 w-4/5 top-1/2 -translate-y-1/2 p-4 bg-stone-50 rounded-md">
		<div class="absolute top-2 right-2 w-[24px] h-[24px] [font-size:24px] [line-height:24px] text-center
				font-bold hover:cursor-pointer"
			@click="closeIconClicked" ref="closeIcon">&times;</div>
		<h1 class="text-center text-xl font-bold mb-2">{{lastNode != null ? lastNode.name : 'NULL'}}</h1>
		<hr class="mb-4 border-stone-400"/>
		<div :style="imgStyles" class="float-left mr-4" alt="an image"></div>
		<div>
			Lorem ipsum dolor sit amet, consectetur adipiscing
			elit, sed do eiusmod tempor incididunt ut labore
			et dolore magna aliqua. Ut enim ad minim veniam,
			quis nostrud exercitation ullamco laboris nisi ut
			aliquip ex ea commodo consequat.
		</div>
	</div>
</div>
</template>
