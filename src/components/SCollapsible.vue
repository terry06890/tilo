<template>
<div :style="styles">
	<div class="hover:cursor-pointer" @click="collapsed = !collapsed">
		<slot name="summary" :collapsed="collapsed">(Summary)</slot>
	</div>
	<div :style="contentStyles" ref="content">
		<slot name="content">(Content)</slot>
	</div>
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
				maxHeight: this.collapsed ? '0' : (this.$refs.content as HTMLDivElement).scrollHeight + 'px',
				opacity: this.collapsed ? '0' : '1',
				transitionProperty: 'max-height, opacity',
				transitionDuration: '300ms',
				transitionTimingFunction: 'ease-in-out',
			};
		},
	},
});
</script>
