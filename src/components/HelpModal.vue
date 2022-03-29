<script lang="ts">
import {defineComponent, PropType} from 'vue';
import CloseIcon from './icon/CloseIcon.vue';

// Displays help information
export default defineComponent({
	props: {
		uiOpts: {type: Object, required: true},
	},
	methods: {
		onCloseClick(evt: Event){
			if (evt.target == this.$el || (this.$refs.closeIcon as typeof CloseIcon).$el.contains(evt.target)){
				this.$emit('help-modal-close');
			}
		},
	},
	components: {CloseIcon, },
	emits: ['help-modal-close', ],
});
</script>

<template>
<div class="fixed left-0 top-0 w-full h-full bg-black/40" @click="onCloseClick">
	<div class="absolute left-1/2 -translate-x-1/2 w-4/5 top-1/2 -translate-y-1/2 p-4
		bg-stone-50 rounded-md shadow shadow-black">
		<close-icon @click.stop="onCloseClick" ref="closeIcon"
			class="block absolute top-2 right-2 w-6 h-6 hover:cursor-pointer"/>
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
