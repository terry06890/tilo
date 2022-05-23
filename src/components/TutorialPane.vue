<script lang="ts">
import {defineComponent, PropType} from 'vue';
import CloseIcon from './icon/CloseIcon.vue';

export default defineComponent({
	props: {
		pos: {type: Array as unknown as PropType<[number,number]>, required: true},
		dims: {type: Array as unknown as PropType<[number,number]>, required: true},
		uiOpts: {type: Object, required: true},
	},
	data(){
		return {
			stage: 0,
		};
	},
	computed: {
		 styles(): Record<string,string> {
			return {
				position: 'absolute',
				left: this.pos[0] + 'px',
				top: this.pos[1] + 'px',
				width: this.dims[0] + 'px',
				height: this.dims[1] + 'px',
				backgroundColor: this.uiOpts.tutorialPaneBgColor,
				color: this.uiOpts.tutorialPaneTextColor,
			};
		 },
	},
	methods: {
		onCloseClick(evt: Event){
			this.$emit('tutorial-close');
		},
		onTutorialStart(){
			console.log("Start tutorial");
		},
	},
	components: {CloseIcon, },
	emits: ['tutorial-close', ],
});
</script>

<template>
<div :style="styles">
	<close-icon @click.stop="onCloseClick" ref="closeIcon"
		class="block absolute top-2 right-2 w-6 h-6 hover:cursor-pointer"/>
	<div v-if="stage == 0" class="h-full flex flex-col justify-evenly">
		<h1 class="px-4 text-center text-xl font-bold">Welcome</h1>
		<div class="px-4 max-w-[15cm] mx-auto text-sm">
			Lorem ipsum dolor sit amet, consectetur adipiscing
			elit, sed do eiusmod tempor incididunt ut labore
			et dolore magna aliqua. Ut enim ad minim veniam,
			quis nostrud exercitation ullamco.
		</div>
		<div class="w-full flex justify-evenly">
			<div>
				<button class="w-full h-full px-4 py-2 rounded bg-stone-800 hover:bg-stone-700"
					@click="onTutorialStart">
					Start Tutorial
				</button>
			</div>
			<div>
				<button class="w-full h-full px-4 py-2 rounded bg-stone-800 hover:bg-stone-700"
					@click="onCloseClick">
					Continue
				</button>
			</div>
		</div>
	</div>
</div>
</template>
