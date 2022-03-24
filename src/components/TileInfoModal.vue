<script lang="ts">
import {defineComponent, PropType} from 'vue';
import {TolNode} from '../lib';

export default defineComponent({
	props: {
		tolNode: {type: Object as PropType<TolNode | null>}, // The node to display, or null to hide
	},
	data(){
		return {
			lastNode: null as TolNode | null, // Used to prevent content-change during fade-out
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
				transitionDuration: '300ms',
			};
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
	<div class="absolute left-1/2 -translate-x-1/2 min-w-3/5 top-1/3 p-2 bg-white rounded-md">
		<div class="absolute top-1 right-1 text-lg font-bold hover:cursor-pointer"
			@click="closeIconClicked" ref="closeIcon">&times;</div>
		<img class="float-left mr-2 mb-2" width="200" height="200" alt="an image"/>
		<h1>{{lastNode != null ? lastNode.name : 'If you can read this, something\'s wrong'}}</h1>
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
