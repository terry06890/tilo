<template>
<div :style="styles">
	<div class="hover:cursor-pointer" @click="collapsed = !collapsed">
		<slot name="summary" :collapsed="collapsed">(Summary)</slot>
	</div>
	<transition @enter="onEnter" @after-enter="onAfterEnter" @leave="onLeave" @before-leave="onBeforeLeave">
		<div v-show="!collapsed" :style="contentStyles" class="max-h-0" ref="content">
			<slot name="content">(Content)</slot>
		</div>
	</transition>
</div>
</template>

<script lang="ts">
import {defineComponent, PropType} from 'vue';

export default defineComponent({
	data(){
		return {
			collapsed: true,
		};
	},
	computed: {
		styles(): Record<string,string> {
			return {
				overflow: this.collapsed ? 'hidden' : 'visible',
			};
		},
		contentStyles(): Record<string,string> {
			return {
				overflow: 'hidden',
				opacity: this.collapsed ? '0' : '1',
				transitionProperty: 'max-height, opacity',
				transitionDuration: '300ms',
				transitionTimingFunction: 'ease-in-out',
			};
		},
	},
	methods: {
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
});
</script>
