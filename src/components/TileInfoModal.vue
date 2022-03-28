<script lang="ts">
import {defineComponent, PropType} from 'vue';
import CloseIcon from './icon/CloseIcon.vue';
import {TolNode} from '../tol';

export default defineComponent({
	props: {
		tolNode: {type: Object as PropType<TolNode>, required: true},
		uiOpts: {type: Object, required: true},
	},
	computed: {
		imgStyles(): Record<string,string> {
			return {
				backgroundImage: 'url(\'/img/' + this.tolNode.name.replaceAll('\'', '\\\'') + '.png\')',
				width: this.uiOpts.infoModalImgSz + 'px',
				height: this.uiOpts.infoModalImgSz + 'px',
				backgroundSize: 'cover',
				borderRadius: this.uiOpts.borderRadius + 'px',
			}
		},
	},
	methods: {
		closeClicked(evt: Event){
			if (evt.target == this.$el || (this.$refs.closeIcon.$el as HTMLElement).contains(evt.target as HTMLElement)){
				this.$emit('info-modal-close');
			}
		},
	},
	components: {CloseIcon, },
	emits: ['info-modal-close'],
});
</script>

<template>
<div class="fixed left-0 top-0 w-full h-full bg-black/40" @click="closeClicked">
	<div class="absolute left-1/2 -translate-x-1/2 w-4/5 top-1/2 -translate-y-1/2 p-4
		bg-stone-50 rounded-md shadow shadow-black">
		<close-icon @click.stop="closeClicked" ref="closeIcon"
			class="block absolute top-2 right-2 w-6 h-6 hover:cursor-pointer"/>
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
