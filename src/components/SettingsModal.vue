<script lang="ts">
import {defineComponent, PropType} from 'vue';
import CloseIcon from './icon/CloseIcon.vue';
import RButton from './RButton.vue';
import type {LayoutOptions} from '../layout';

// Displays configurable options, and sends option-change requests
export default defineComponent({
	props: {
		lytOpts: {type: Object as PropType<LayoutOptions>, required: true},
		uiOpts: {type: Object, required: true},
	},
	methods: {
		onCloseClick(evt: Event){
			if (evt.target == this.$el || (this.$refs.closeIcon as typeof CloseIcon).$el.contains(evt.target)){
				this.saveSettings();
				this.$emit('settings-close');
			}
		},
		onLytOptChg(){
			this.$emit('layout-option-change');
		},
		onMinTileSzChg(){
			let minInput = this.$refs.minTileSzInput as HTMLInputElement;
			let maxInput = this.$refs.maxTileSzInput as HTMLInputElement;
			if (Number(minInput.value) > Number(maxInput.value)){
				this.lytOpts.maxTileSz = this.lytOpts.minTileSz;
			}
			this.onLytOptChg();
		},
		onMaxTileSzChg(){
			let minInput = this.$refs.minTileSzInput as HTMLInputElement;
			let maxInput = this.$refs.maxTileSzInput as HTMLInputElement;
			if (Number(maxInput.value) < Number(minInput.value)){
				this.lytOpts.minTileSz = this.lytOpts.maxTileSz;
			}
			this.onLytOptChg();
		},
		onTreeChg(){
			this.$emit('tree-change');
		},
		saveSettings(){
			const savedLytOpts = ['tileSpacing', 'minTileSz', 'maxTileSz', 'layoutType', 'sweepMode', 'sweepToParent', ];
			for (let prop of savedLytOpts){
				localStorage.setItem('lyt ' + prop, String(this.lytOpts[prop as keyof LayoutOptions]));
			}
			const savedUiOpts = ['tileChgDuration', 'jumpToSearchedNode', 'useReducedTree', ];
			for (let prop of savedUiOpts){
				localStorage.setItem('ui ' + prop, String(this.uiOpts[prop]));
			}
			console.log('Settings saved');
		},
		onReset(){
			localStorage.clear();
			this.$emit('reset-settings');
			console.log('Settings reset');
		},
	},
	components: {CloseIcon, RButton, },
	emits: ['settings-close', 'layout-option-change', 'tree-change', 'reset-settings', ],
});
</script>

<template>
<div class="fixed left-0 top-0 w-full h-full bg-black/40" @click="onCloseClick">
	<div class="absolute left-1/2 -translate-x-1/2 w-4/5 top-1/2 -translate-y-1/2 max-h-[80%]
		p-3 bg-stone-50 visible rounded-md shadow shadow-black">
		<close-icon @click.stop="onCloseClick" ref="closeIcon"
			class="block absolute top-2 right-2 w-6 h-6 hover:cursor-pointer" />
		<h1 class="text-xl font-bold mb-2">Settings</h1>
		<hr class="border-stone-400"/>
		<div>
			<label>Tile Spacing <input type="range" min="0" max="20" class="mx-2 w-[3cm]"
				v-model.number="lytOpts.tileSpacing" @input="onLytOptChg"/></label>
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
						@change="onLytOptChg"/> Squares </label>
				</li>
				<li>
					<label> <input type="radio" v-model="lytOpts.layoutType" value="rect"
						@change="onLytOptChg"/> Rectangles </label>
				</li>
				<li>
					<label> <input type="radio" v-model="lytOpts.layoutType" value="sweep"
						@change="onLytOptChg"/> Sweep to side </label>
				</li>
			</ul>
		</div>
		<hr class="border-stone-400"/>
		<div>
			Sweep to parent
			<ul>
				<li>
					<label> <input type="radio" v-model="lytOpts.sweepToParent" value="none"
						@change="onLytOptChg"/> None </label>
				</li>
				<li>
					<label> <input type="radio" v-model="lytOpts.sweepToParent" value="prefer"
						@change="onLytOptChg"/> Prefer </label>
				</li>
				<li>
					<label> <input type="radio" v-model="lytOpts.sweepToParent" value="fallback"
						@change="onLytOptChg"/> Fallback </label>
				</li>
			</ul>
		</div>
		<hr class="border-stone-400"/>
		<div>
			Sweep Mode
			<ul>
				<li>
					<label> <input type="radio" v-model="lytOpts.sweepMode" value="left"
						@change="onLytOptChg"/> To left </label>
				</li>
				<li>
					<label> <input type="radio" v-model="lytOpts.sweepMode" value="top"
						@change="onLytOptChg"/> To top </label>
				</li>
				<li>
					<label> <input type="radio" v-model="lytOpts.sweepMode" value="shorter"
						@change="onLytOptChg"/> To shorter </label>
				</li>
				<li>
					<label> <input type="radio" v-model="lytOpts.sweepMode" value="auto"
						@change="onLytOptChg"/> Auto </label>
				</li>
			</ul>
		</div>
		<hr class="border-stone-400"/>
		<div>
			<label>Animation Duration <input type="range" min="0" max="3000" class="mx-2 w-[3cm]"
				v-model.number="uiOpts.tileChgDuration"/></label>
		</div>
		<hr class="border-stone-400"/>
		<div>
			<label> <input type="checkbox" v-model="uiOpts.jumpToSearchedNode"/> Jump to search result</label>
		</div>
		<hr class="border-stone-400"/>
		<div>
			Tree
			<ul>
				<li>
					<label> <input type="radio" v-model="uiOpts.useReducedTree" :value="false"
						@change="onTreeChg"/> Default </label>
				</li>
				<li>
					<label> <input type="radio" v-model="uiOpts.useReducedTree" :value="true"
						@change="onTreeChg"/> Reduced </label>
				</li>
			</ul>
		</div>
		<hr class="border-stone-400"/>
		<div class="flex justify-around mt-2">
			<r-button class="bg-stone-800 text-white" @click="onReset">
				Reset
			</r-button>
		</div>
	</div>
</div>
</template>
