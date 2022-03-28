<script lang="ts">
import {defineComponent, PropType} from 'vue';
import CloseIcon from './icon/CloseIcon.vue';
import type {LayoutOptions} from '../layout';

export default defineComponent({
	props: {
		lytOpts: {type: Object as PropType<LayoutOptions>, required: true},
		uiOpts: {type: Object, required: true},
	},
	methods: {
		closeClicked(evt: Event){
			if (evt.target == this.$el || (this.$refs.closeIcon.$el as HTMLElement).contains(evt.target as HTMLElement)){
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
				this.lytOpts.maxTileSz = this.lytOpts.minTileSz;
			}
			this.onLayoutOptChg();
		},
		onMaxTileSzChg(){
			let minInput = this.$refs.minTileSzInput as HTMLInputElement;
			let maxInput = this.$refs.maxTileSzInput as HTMLInputElement;
			if (Number(maxInput.value) < Number(minInput.value)){
				this.lytOpts.minTileSz = this.lytOpts.maxTileSz;
			}
			this.onLayoutOptChg();
		},
	},
	components: {CloseIcon, },
	emits: ['settings-close', 'layout-option-change', ],
});
</script>

<template>
<div class="absolute bottom-4 right-4 min-w-[5cm] p-3 bg-stone-50 visible rounded-md shadow shadow-black">
	<close-icon @click="closeClicked" ref="closeIcon"
		class="block absolute top-2 right-2 w-6 h-6 hover:cursor-pointer" />
	<h1 class="text-xl font-bold mb-2">Settings</h1>
	<hr class="border-stone-400"/>
	<div>
		<label>Tile Spacing <input type="range" min="0" max="20" class="mx-2 w-[3cm]"
			v-model.number="lytOpts.tileSpacing" @input="onLayoutOptChg"/></label>
	</div>
	<hr class="border-stone-400"/>
	<div>
		<label>
			<span class="inline-block w-[3cm]">Min Tile Size</span>
			<input type="range" min="0" max="400" v-model.number="lytOpts.minTileSz" class="w-[3cm]"
				@input="onMinTileSzChg" ref="minTileSzInput"/>
		</label>
	</div>
	<div>
		<label>
			<span class="inline-block w-[3cm]">Max Tile Size</span>
			<input type="range" min="0" max="400" v-model.number="lytOpts.maxTileSz" class="w-[3cm]"
				@input="onMaxTileSzChg" ref="maxTileSzInput"/>
		</label>
	</div>
	<hr class="border-stone-400"/>
	<div>
		Layout Method
		<ul>
			<li>
				<label> <input type="radio" v-model="lytOpts.layoutType" value="sqr"
					@change="onLayoutOptChg"/> Squares </label>
			</li>
			<li>
				<label> <input type="radio" v-model="lytOpts.layoutType" value="rect"
					@change="onLayoutOptChg"/> Rectangles </label>
			</li>
			<li>
				<label> <input type="radio" v-model="lytOpts.layoutType" value="sweep"
					@change="onLayoutOptChg"/> Sweep to side </label>
			</li>
		</ul>
	</div>
	<hr class="border-stone-400"/>
	<div>
		<label> <input type="checkbox" v-model="lytOpts.sweepingToParent"
			@change="onLayoutOptChg"/> Sweep to parent</label>
	</div>
	<hr class="border-stone-400"/>
	<div>
		Sweep Mode
		<ul>
			<li>
				<label> <input type="radio" v-model="lytOpts.sweepMode" value="left"
					@change="onLayoutOptChg"/> To left </label>
			</li>
			<li>
				<label> <input type="radio" v-model="lytOpts.sweepMode" value="top"
					@change="onLayoutOptChg"/> To top </label>
			</li>
			<li>
				<label> <input type="radio" v-model="lytOpts.sweepMode" value="shorter"
					@change="onLayoutOptChg"/> To shorter </label>
			</li>
			<li>
				<label> <input type="radio" v-model="lytOpts.sweepMode" value="auto"
					@change="onLayoutOptChg"/> Auto </label>
			</li>
		</ul>
	</div>
	<hr class="border-stone-400"/>
	<div>
		<label>Animation Speed <input type="range" min="0" max="1000" class="mx-2 w-[3cm]"
			v-model.number="uiOpts.transitionDuration"/></label>
	</div>
</div>
</template>
