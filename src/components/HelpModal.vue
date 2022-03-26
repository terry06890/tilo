<script lang="ts">
import {defineComponent, PropType} from 'vue';

export default defineComponent({
	props: {
		options: {type: Object, required: true},
	},
	methods: {
		closeClicked(evt: Event){
			if (evt.target == this.$el || evt.target == this.$refs.closeIcon){
				this.$emit('help-modal-close');
			}
		},
	},
	emits: ['help-modal-close'],
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
		<h1 class="text-center text-xl font-bold mb-2">Help Info</h1>
		<hr class="mb-4 border-stone-400"/>
		<div class="mb-4">
			Lorem ipsum dolor sit amet, consectetur adipiscing
			elit, sed do eiusmod tempor incididunt ut labore
			et dolore magna aliqua. Ut enim ad minim veniam,
			quis nostrud exercitation ullamco laboris nisi ut
			aliquip ex ea commodo consequat.
		</div>
		<div>
			Lorem ipsum dolor sit amet, consectetur adipiscing
			elit, sed do eiusmod tempor incididunt ut labore
			et dolore magna aliqua. Ut enim ad minim veniam,
			quis nostrud exercitation ullamco laboris nisi ut
			aliquip ex ea commodo consequat.  Duis aute irure
			dolor in reprehenderit in voluptate velit esse
			cillum dolore eu fugiat nulla pariatur. Excepteur
			sint occaecat cupidatat non proident, sunt
			in culpa qui officia deserunt mollit anim id
			est laborum.
		</div>
	</div>
</div>
</template>
