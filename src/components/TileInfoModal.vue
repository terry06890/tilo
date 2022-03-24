<script lang="ts">
import {defineComponent, PropType} from 'vue';
import {TolNode} from '../lib';

export default defineComponent({
	props: {
		tolNode: {type: Object as PropType<TolNode | null>},
	},
	computed: {
		hidden(){
			return this.tolNode == null;
		},
		styles(): Record<string,string> {
			return {
				display: this.hidden ? 'none' : 'block',
				opacity: this.hidden ? '0' : '1',
				transition: 'opacity 0.3s',
			};
		},
	},
	methods: {
		closeIconClicked(){
			this.$emit('info-modal-close');
		},
	},
	emits: ['info-modal-close']
});
</script>

<template>
<div :style="styles" class="fixed left-0 top-0 w-full h-full bg-black/40" @click="closeIconClicked">
	<div class="absolute left-1/2 -translate-x-1/2 min-w-3/5 top-1/3 p-2 bg-white rounded-md">
		<div class="absolute top-1 right-1 text-lg font-bold hover:cursor-pointer"
			@click="closeIconClicked">&times;</div>
		<img class="float-left mr-2 mb-2" width="200" height="200" alt="an image"/>
		<h1>{{hidden ? 'If you can see this, something\'s wrong' : tolNode!.name}}</h1>
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
