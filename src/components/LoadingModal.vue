<template>
<div class="fixed left-0 top-0 w-full h-full bg-black/40">
	<div class="absolute left-1/2 -translate-x-1/2 top-1/2 -translate-y-1/2
		flex items-center py-3 px-3 gap-2" :style="styles">
		<loader-icon class="w-12 h-12 animate-[spin_6s_linear_infinite]"/>
		<div class="whitespace-nowrap">{{msg}}</div>
	</div>
</div>
</template>

<script setup lang="ts">
import {computed, PropType} from 'vue';
import LoaderIcon from './icon/LoaderIcon.vue';
import {UiOptions} from '../lib';

const props = defineProps({
	msg: {type: String, required: true},
	uiOpts: {type: Object as PropType<UiOptions>, required: true},
});

const styles = computed(() => ({
	color: props.uiOpts.textColor,
	backgroundColor: props.uiOpts.bgColorDark2,
	borderRadius: props.uiOpts.borderRadius + 'px',
	boxShadow: props.uiOpts.shadowNormal,
}));
</script>
