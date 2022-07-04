<template>
<div :style="styles" class="p-2 rounded-full hover:cursor-pointer"
	:class="{'hover:brightness-125': !disabled, 'brightness-50': disabled}">
	<slot class="w-full h-full">?</slot>
</div>
</template>

<script lang="ts">
import {defineComponent, PropType} from 'vue';

export default defineComponent({
	props: {
		size: {type: Number, default: 36},
		disabled: {type: Boolean, default: false},
	},
	computed: {
		styles(): Record<string,string> {
			return {
				minWidth: this.size + 'px',
				maxWidth: this.size + 'px',
				minHeight: this.size + 'px',
				maxHeight: this.size + 'px',
				padding: (this.size / 5) + 'px',
			};
		},
	},
});
</script>
