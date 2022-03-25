<script lang="ts">
import {defineComponent, PropType} from 'vue';
import {TolNode} from '../lib';

export default defineComponent({
	props: {
		tolNode: {type: Object as PropType<TolNode>, required: true},
		options: {type: Object, required: true},
	},
	computed: {
		imgStyles(): Record<string,string> {
			return {
				backgroundImage: 'url(\'/img/' + this.tolNode.name.replaceAll('\'', '\\\'') + '.png\')',
				width: this.options.infoModalImgSz + 'px',
				height: this.options.infoModalImgSz + 'px',
				backgroundSize: 'cover',
				borderRadius: this.options.borderRadius + 'px',
			}
		},
	},
	methods: {
		closeClicked(evt: Event){
			if (evt.target == this.$el || evt.target == this.$refs.closeIcon){
				this.$emit('info-modal-close');
			}
		},
	},
	emits: ['info-modal-close'],
});
</script>

<template>
<div class="fixed left-0 top-0 w-full h-full bg-black/40" @click="closeClicked">
	<div class="absolute left-1/2 -translate-x-1/2 w-4/5 top-1/2 -translate-y-1/2 p-4
		bg-stone-50 rounded-md shadow shadow-black">
		<svg class="block absolute top-2 right-2 w-6 h-6 hover:cursor-pointer"
			@click="closeClicked" ref="closeIcon"
			xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
			stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
		  <line x1="18" y1="6" x2="6" y2="18"/>
		  <line x1="6" y1="6" x2="18" y2="18"/>
		</svg>
		<h1 class="text-center text-xl font-bold mb-2">{{tolNode.name}}</h1>
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
