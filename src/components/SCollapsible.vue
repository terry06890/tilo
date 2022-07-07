<template>
<div :style="styles">
	<div class="hover:cursor-pointer" @click="onClick">
		<slot name="summary" :open="open">(Summary)</slot>
	</div>
	<transition @enter="onEnter" @after-enter="onAfterEnter" @leave="onLeave" @before-leave="onBeforeLeave">
		<div v-show="open" :style="contentStyles" class="max-h-0" ref="content">
			<slot name="content">(Content)</slot>
		</div>
	</transition>
</div>
</template>

<script lang="ts">
import {defineComponent, PropType} from 'vue';

export default defineComponent({
	props: {
		modelValue: {type: Boolean, default: false}, // For using v-model on the component
	},
	data(){
		return {
			open: false,
		};
	},
	computed: {
		styles(): Record<string,string> {
			return {
				overflow: this.open ? 'visible' : 'hidden',
			};
		},
		contentStyles(): Record<string,string> {
			return {
				overflow: 'hidden',
				opacity: this.open ? '1' : '0',
				transitionProperty: 'max-height, opacity',
				transitionDuration: '300ms',
				transitionTimingFunction: 'ease-in-out',
			};
		},
	},
	methods: {
		onClick(evt: Event){
			this.open = !this.open;
			this.$emit('update:modelValue', this.open);
			if (this.open){
				this.$emit('open');
			}
		},
		onEnter(el: HTMLDivElement){
			el.style.maxHeight = el.scrollHeight + 'px';
		},
		onAfterEnter(el: HTMLDivElement){
			el.style.maxHeight = 'none';
				// Allows the content to grow after the transition ends, as the scrollHeight sometimes is too short
		},
		onBeforeLeave(el: HTMLDivElement){
			el.style.maxHeight = el.scrollHeight + 'px';
			el.offsetWidth; // Triggers reflow
		},
		onLeave(el: HTMLDivElement){
			el.style.maxHeight = '0';
		},
	},
	watch: {
		modelValue(newVal, oldVal){
			this.open = newVal;
		},
	},
	emits: ['update:modelValue', 'open', ],
});
</script>
