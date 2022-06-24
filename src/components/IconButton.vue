<script lang="ts">
import {defineComponent, PropType} from 'vue';

export default defineComponent({
	props: {
		disabled: {type: Boolean, default: false},
	},
});
</script>

<template>
<div class="w-9 h-9 p-2 rounded-full hover:cursor-pointer"
	:class="{'hover:brightness-125': !disabled, 'brightness-75': disabled}">
	<slot class="w-full h-full">?</slot>
</div>
</template>
