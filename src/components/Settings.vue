<script lang="ts">
import {defineComponent, PropType} from 'vue';

export default defineComponent({
	props: {
		isOpen: {type: Boolean, required: true},
	},
	methods: {
		openClicked(){
			this.$emit('settings-open');
		},
		closeClicked(evt: Event){
			this.$emit('settings-close');
		},
	},
	emits: ['settings-open', 'settings-close'],
});
</script>

<template>
<!-- outer div prevents overflow from transitioning to/from off-screen -->
<div class="absolute left-0 top-0 w-full h-full invisible overflow-hidden">
	<Transition name="slide-bottom-right">
		<div v-if="isOpen"
			class="absolute bottom-4 right-4 min-w-[5cm] p-3 bg-stone-50 visible rounded-md shadow-md bg-stone-50">
			<div class="absolute top-2 right-2 w-[24px] h-[24px] [font-size:24px] [line-height:24px] text-center
					font-bold hover:cursor-pointer"
				@click="closeClicked">&times;</div>
			<h1 class="text-xl font-bold mb-2">Settings</h1>
			<hr class="border-stone-400"/>
			<div class="border border-black my-2">Setting 1</div>
			<div class="border border-black my-2">Setting 2</div>
			<div class="border border-black my-2">Setting 3</div>
			<div class="border border-black my-2">Setting 4</div>
			<div class="border border-black my-2">Setting 5</div>
			<div class="border border-black mt-2">Setting 6</div>
		</div>
	</Transition>
	<Transition name="slide-bottom-right">
		<!-- outer div prevents transition interference with inner rotate -->
		<div v-if="!isOpen" class="absolute bottom-0 right-0 w-[100px] h-[100px]">
			<div class="absolute bottom-[-50px] right-[-50px] w-[100px] h-[100px] visible -rotate-45
				bg-black text-white hover:cursor-pointer" @click="openClicked">
				<svg class="w-[24px] h-[24px] mx-auto mt-[9px]"
					xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
					stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
					<circle cx="12" cy="12" r="3"/>
					<path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0
						0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2
						2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0
						0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65
						1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1
						2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2
						0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65
						1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0
						1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0
						2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2
						2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
				</svg>
			</div>
		</div>
	</Transition>
</div>
</template>

<style>
.slide-bottom-right-enter-from, .slide-bottom-right-leave-to {
	transform: translate(100%, 100%);
	opacity: 0;
}
.slide-bottom-right-enter-active, .slide-bottom-right-leave-active {
	transition-property: transform, opacity;
	transition-duration: 300ms;
	transition-timing-function: ease-in-out;
}
</style>
