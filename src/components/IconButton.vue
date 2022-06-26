<template>
<div class="p-2 rounded-full hover:cursor-pointer"
	:class="{'hover:brightness-125': !disabled, 'brightness-75': disabled}"
	:style="{width: size + 'px', height: size + 'px', padding: (size / 5) + 'px'}">
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
});
</script>
