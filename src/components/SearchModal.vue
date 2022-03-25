<script lang="ts">
import {defineComponent, PropType} from 'vue';
import {TolNode, LayoutNode} from '../lib';

export default defineComponent({
	props: {
		layoutTree: {type: Object as PropType<LayoutNode>, required: true},
		options: {type: Object, required: true},
	},
	methods: {
		closeClicked(evt: Event){
			if (evt.target == this.$el || evt.target == this.$refs.closeIcon){
				this.$emit('search-close');
			}
		},
	},
	emits: ['search-node', 'search-close']
});
</script>

<template>
<div class="fixed left-0 top-0 w-full h-full bg-black/40" @click="closeClicked">
	<div class="absolute left-1/2 -translate-x-1/2 w-4/5 top-1/2 -translate-y-1/2 p-4
		bg-stone-50 rounded-md shadow shadow-black">
		<div class="absolute top-2 right-2 w-[24px] h-[24px] [font-size:24px] [line-height:24px] text-center
				font-bold hover:cursor-pointer"
			@click="closeClicked" ref="closeIcon">&times;</div>
		<div>
			Search
		</div>
	</div>
</div>
</template>
