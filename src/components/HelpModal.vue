<template>
<div class="fixed left-0 top-0 w-full h-full bg-black/40" @click="onClose">
	<div class="absolute left-1/2 -translate-x-1/2 top-1/2 -translate-y-1/2 w-4/5 p-4" :style="styles">
		<close-icon @click.stop="onClose" ref="closeIcon"
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
		<s-button :style="{color: uiOpts.textColor, backgroundColor: uiOpts.bgColor}" @click.stop="onStartTutorial">
			Start Tutorial
		</s-button>
	</div>
</div>
</template>

<script lang="ts">
import {defineComponent, PropType} from 'vue';
import SButton from './SButton.vue';
import CloseIcon from './icon/CloseIcon.vue';
import {UiOptions} from '../lib';

export default defineComponent({
	props: {
		uiOpts: {type: Object as PropType<UiOptions>, required: true},
	},
	computed: {
		styles(): Record<string,string> {
			return {
				backgroundColor: this.uiOpts.bgColorAlt,
				borderRadius: this.uiOpts.borderRadius + 'px',
				boxShadow: this.uiOpts.shadowNormal,
			};
		},
	},
	methods: {
		onClose(evt: Event){
			if (evt.target == this.$el || (this.$refs.closeIcon as typeof CloseIcon).$el.contains(evt.target)){
				this.$emit('close');
			}
		},
		onStartTutorial(){
			this.$emit('start-tutorial');
			this.$emit('close');
		},
	},
	components: {SButton, CloseIcon, },
	emits: ['close', 'start-tutorial', ],
});
</script>
