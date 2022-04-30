<script lang="ts">
import {defineComponent, PropType} from 'vue';
import CloseIcon from './icon/CloseIcon.vue';
import {LayoutNode} from '../layout';

// Displays information about a tree-of-life node
export default defineComponent({
	props: {
		node: {type: Object as PropType<LayoutNode>, required: true},
		tolMap: {type: Object as PropType<TolMap>, required: true},
		uiOpts: {type: Object, required: true},
	},
	computed: {
		tolNode(): TolNode {
			return this.tolMap.get(this.node.name)!;
		},
		imgStyles(): Record<string,string> {
			return {
				backgroundImage: this.tolNode.imgFile != null ?
					'linear-gradient(to bottom, rgba(0,0,0,0.4), #0000 40%, #0000 60%, rgba(0,0,0,0.4) 100%),' +
						'url(\'/img/' + this.tolNode.imgFile.replaceAll('\'', '\\\'') + '\')' :
					'none',
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
		<h1 class="text-center text-xl font-bold mb-2">{{node.name}}</h1>
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
