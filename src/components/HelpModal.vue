<template>
<div class="fixed left-0 top-0 w-full h-full bg-black/40" @click="onClose">
	<div class="absolute left-1/2 -translate-x-1/2 top-1/2 -translate-y-1/2
		w-4/5 max-w-[20cm] max-h-[80%] overflow-auto" :style="styles">
		<close-icon @click.stop="onClose" ref="closeIcon"
			class="block absolute top-1 right-1 md:top-2 md:right-2 w-8 h-8 hover:cursor-pointer"/>
		<h1 class="text-center text-xl font-bold py-2 border-b border-stone-400">Help</h1>
		<div class="p-2 border-b border-stone-400">
			<div>
				Lorem ipsum dolor sit amet, consectetur adipiscing
				elit, sed do eiusmod tempor incididunt ut labore
				et dolore magna aliqua.
			</div>
			<ul class="list-disc ml-3">
				<li>What is the Tree of Life? ('tips', )</li>
				<li>Representing the Tree
					(OneZoom, iTol)
					(tile layout, overflown-root, )
					(leaf header colors, asterisk, compound nodes/names/images, )
				</li>
				<li>Data sources (OTOL, EOL, Wikipedia) (imprecision: tree, names, images, descs, )</li>
				<li>Using tilo
					(tutorial)
					(settings: layout methods, reduced trees, click-label-to-reset)
					(keyboard shortcuts)
				</li>
				<li>Project page, error contact, other credits (feathericons, ionicons), </li>
			</ul>
		</div>
		<s-button :disabled="tutOpen" class="mx-auto my-2"
			:style="{color: uiOpts.textColor, backgroundColor: uiOpts.bgColor}" @click.stop="onStartTutorial">
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
		tutOpen: {type: Boolean, default: false},
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
