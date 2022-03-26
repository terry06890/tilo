<script lang="ts">
import {defineComponent, PropType} from 'vue';
import type {LayoutOptions} from '../lib';

export default defineComponent({
	props: {
		layoutOptions: {type: Object as PropType<LayoutOptions>, required: true},
		componentOptions: {type: Object, required: true},
	},
	methods: {
		closeClicked(evt: Event){
			if (evt.target == this.$el || evt.target == this.$refs.closeIcon){
				this.$emit('settings-close');
			}
		},
		onLayoutOptChg(){
			this.$emit('layout-option-change');
		},
		onMinTileSzChg(){
			let minInput = this.$refs.minTileSzInput as HTMLInputElement;
			let maxInput = this.$refs.maxTileSzInput as HTMLInputElement;
			if (Number(minInput.value) > Number(maxInput.value)){
				this.layoutOptions.maxTileSz = this.layoutOptions.minTileSz;
			}
			this.onLayoutOptChg();
		},
		onMaxTileSzChg(){
			let minInput = this.$refs.minTileSzInput as HTMLInputElement;
			let maxInput = this.$refs.maxTileSzInput as HTMLInputElement;
			if (Number(maxInput.value) < Number(minInput.value)){
				this.layoutOptions.minTileSz = this.layoutOptions.maxTileSz;
			}
			this.onLayoutOptChg();
		},
	},
	emits: ['settings-close', 'layout-option-change', ],
});
</script>

<template>
<div class="absolute bottom-4 right-4 min-w-[5cm] p-3 bg-stone-50 visible rounded-md shadow shadow-black">
	<svg class="block absolute top-2 right-2 w-6 h-6 hover:cursor-pointer"
		@click="closeClicked" ref="closeIcon"
		xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
		stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
		<line x1="18" y1="6" x2="6" y2="18"/>
		<line x1="6" y1="6" x2="18" y2="18"/>
	</svg>
	<h1 class="text-xl font-bold mb-2">Settings</h1>
	<hr class="border-stone-400"/>
	<div>
		<label>Tile Spacing <input type="range" min="0" max="20" class="mx-2 w-[3cm]"
			v-model.number="layoutOptions.tileSpacing" @input="onLayoutOptChg"/></label>
	</div>
	<hr class="border-stone-400"/>
	<div>
		<label>
			<span class="inline-block w-[3cm]">Min Tile Size</span>
			<input type="range" min="0" max="400" v-model.number="layoutOptions.minTileSz" class="w-[3cm]"
				@input="onMinTileSzChg" ref="minTileSzInput"/>
		</label>
	</div>
	<div>
		<label>
			<span class="inline-block w-[3cm]">Max Tile Size</span>
			<input type="range" min="0" max="400" v-model.number="layoutOptions.maxTileSz" class="w-[3cm]"
				@input="onMaxTileSzChg" ref="maxTileSzInput"/>
		</label>
	</div>
	<hr class="border-stone-400"/>
	<div>
		Layout Method
		<ul>
			<li>
				<label> <input type="radio" v-model="layoutOptions.layoutType" value="sqr"
					@change="onLayoutOptChg"/> Squares </label>
			</li>
			<li>
				<label> <input type="radio" v-model="layoutOptions.layoutType" value="rect"
					@change="onLayoutOptChg"/> Rectangles </label>
			</li>
			<li>
				<label> <input type="radio" v-model="layoutOptions.layoutType" value="sweep"
					@change="onLayoutOptChg"/> Sweep to side </label>
			</li>
		</ul>
	</div>
	<hr class="border-stone-400"/>
	<div>
		Sweep Mode
		<ul>
			<li>
				<label> <input type="radio" v-model="layoutOptions.sweepMode" value="left"
					@change="onLayoutOptChg"/> To left </label>
			</li>
			<li>
				<label> <input type="radio" v-model="layoutOptions.sweepMode" value="top"
					@change="onLayoutOptChg"/> To top </label>
			</li>
			<li>
				<label> <input type="radio" v-model="layoutOptions.sweepMode" value="shorter"
					@change="onLayoutOptChg"/> To shorter </label>
			</li>
			<li>
				<label> <input type="radio" v-model="layoutOptions.sweepMode" value="auto"
					@change="onLayoutOptChg"/> Auto </label>
			</li>
		</ul>
	</div>
	<hr class="border-stone-400"/>
	<div>
		<label>Animation Speed <input type="range" min="0" max="1000" class="mx-2 w-[3cm]"
			v-model.number="componentOptions.transitionDuration"/></label>
	</div>
</div>
</template>
