<template>
<div class="fixed left-0 top-0 w-full h-full bg-black/40" @click="onClose">
	<div class="absolute left-1/2 -translate-x-1/2 top-1/2 -translate-y-1/2
		w-4/5 max-w-[20cm] max-h-[80%] overflow-auto" :style="styles">
		<close-icon @click.stop="onClose" ref="closeIcon"
			class="block absolute top-1 right-1 md:top-2 md:right-2 w-8 h-8 hover:cursor-pointer"/>
		<h1 class="text-center text-xl font-bold py-2 border-b border-stone-400">Help</h1>
		<div class="p-2 border-b border-stone-400">
			<s-collapsible class="border border-stone-400 rounded">
				<template v-slot:summary="slotProps">
					<div class="p-1 text-center"
						:style="{backgroundColor: !slotProps.collapsed ? 'gray' : 'transparent'}">
						<down-icon class="inline-block w-5 h-5 transition-transform duration-300"
							:class="{'-rotate-90': slotProps.collapsed}"/>
						Summary text
					</div>
				</template>
				<template v-slot:content>
					<div class="p-1">
						Lorem ipsum dolor sit amet, consectetur adipiscing
						elit, sed do eiusmod tempor incididunt ut labore
						et dolore magna aliqua. Ut enim ad minim veniam,
						quis nostrud exercitation ullamco laboris nisi ut
						aliquip ex ea commodo consequat. 
					</div>
				</template>
			</s-collapsible>
			<ul class="list-disc ml-3">
				<li>What is the Tree of Life? ('tips', )</li>
				<li>Visualising the Tree (OneZoom, iTol) (tile layout, )</li>
				<li>Using Tilo
					(tutorial)
					(leaf header colors, asterisk, compound nodes/names/images, overflown-root, )
					(settings: layout methods, reduced trees, click-label-to-reset)
					(keyboard shortcuts)
				</li>
				<li>Data sources (OTOL, EOL, Wikipedia) (imprecision: tree, names, images, descs, )</li>
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
import SCollapsible from './SCollapsible.vue';
import CloseIcon from './icon/CloseIcon.vue';
import DownIcon from './icon/DownIcon.vue';
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
	components: {SButton, SCollapsible, CloseIcon, DownIcon, },
	emits: ['close', 'start-tutorial', ],
});
</script>
