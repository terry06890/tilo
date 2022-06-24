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
	data(){
		return {
			changedLytOpts: new Set(),
			changedUiOpts: new Set(),
		};
	},
	methods: {
		onCloseClick(evt: Event){
			if (evt.target == this.$el || (this.$refs.closeIcon as typeof CloseIcon).$el.contains(evt.target)){
				this.$emit('settings-chg', this.changedLytOpts, this.changedUiOpts);
				this.$emit('close');
			}
		},
		onLytOptChg(opt: string){
			if (opt == 'minTileSz'){
				let minInput = this.$refs.minTileSzInput as HTMLInputElement;
				let maxInput = this.$refs.maxTileSzInput as HTMLInputElement;
				if (Number(minInput.value) > Number(maxInput.value)){
					this.lytOpts.maxTileSz = this.lytOpts.minTileSz;
					this.changedLytOpts.add('maxTileSz');
				}
			} else if (opt == 'maxTileSz'){
				let minInput = this.$refs.minTileSzInput as HTMLInputElement;
				let maxInput = this.$refs.maxTileSzInput as HTMLInputElement;
				if (Number(maxInput.value) < Number(minInput.value)){
					this.lytOpts.minTileSz = this.lytOpts.maxTileSz;
					this.changedLytOpts.add('minTileSz');
				}
			}
			this.$emit('layout-setting-chg');
			this.changedLytOpts.add(opt);
		},
		onUiOptChg(opt: string){
			if (opt == 'useReducedTree'){
				this.$emit('tree-chg');
			}
			this.changedUiOpts.add(opt);
		},
		onReset(){
			this.$emit('reset');
		},
	},
	components: {CloseIcon, RButton, },
	emits: ['close', 'layout-setting-chg', 'tree-chg', 'reset', 'settings-chg', ],
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
				v-model.number="lytOpts.tileSpacing" @input="onLytOptChg('tileSpacing')"/></label>
		</div>
		<hr class="border-stone-400"/>
		<div>
			<label>
				<span class="inline-block w-[3cm]">Min Tile Size</span>
				<input type="range" min="0" max="400" v-model.number="lytOpts.minTileSz" class="w-[3cm]"
					@input="onLytOptChg('minTileSz')" ref="minTileSzInput"/>
			</label>
		</div>
		<div>
			<label>
				<span class="inline-block w-[3cm]">Max Tile Size</span>
				<input type="range" min="0" max="400" v-model.number="lytOpts.maxTileSz" class="w-[3cm]"
					@input="onLytOptChg('maxTileSz')" ref="maxTileSzInput"/>
			</label>
		</div>
		<hr class="border-stone-400"/>
		<div>
			Layout Method
			<ul>
				<li>
					<label> <input type="radio" v-model="lytOpts.layoutType" value="sqr"
						@change="onLytOptChg('layoutType')"/> Squares </label>
				</li>
				<li>
					<label> <input type="radio" v-model="lytOpts.layoutType" value="rect"
						@change="onLytOptChg('layoutType')"/> Rectangles </label>
				</li>
				<li>
					<label> <input type="radio" v-model="lytOpts.layoutType" value="sweep"
						@change="onLytOptChg('layoutType')"/> Sweep to side </label>
				</li>
			</ul>
		</div>
		<hr class="border-stone-400"/>
		<div>
			Sweep to parent
			<ul>
				<li>
					<label> <input type="radio" v-model="lytOpts.sweepToParent" value="none"
						@change="onLytOptChg('sweepToParent')"/> None </label>
				</li>
				<li>
					<label> <input type="radio" v-model="lytOpts.sweepToParent" value="prefer"
						@change="onLytOptChg('sweepToParent')"/> Prefer </label>
				</li>
				<li>
					<label> <input type="radio" v-model="lytOpts.sweepToParent" value="fallback"
						@change="onLytOptChg('sweepToParent')"/> Fallback </label>
				</li>
			</ul>
		</div>
		<hr class="border-stone-400"/>
		<div>
			Sweep Mode
			<ul>
				<li>
					<label> <input type="radio" v-model="lytOpts.sweepMode" value="left"
						@change="onLytOptChg('sweepMode')"/> To left </label>
				</li>
				<li>
					<label> <input type="radio" v-model="lytOpts.sweepMode" value="top"
						@change="onLytOptChg('sweepMode')"/> To top </label>
				</li>
				<li>
					<label> <input type="radio" v-model="lytOpts.sweepMode" value="shorter"
						@change="onLytOptChg('sweepMode')"/> To shorter </label>
				</li>
				<li>
					<label> <input type="radio" v-model="lytOpts.sweepMode" value="auto"
						@change="onLytOptChg('sweepMode')"/> Auto </label>
				</li>
			</ul>
		</div>
		<hr class="border-stone-400"/>
		<div>
			<label>Animation Duration <input type="range" min="0" max="3000" class="mx-2 w-[3cm]"
				v-model.number="uiOpts.tileChgDuration" @change="onUiOptChg('tileChgDuration')"/></label>
		</div>
		<hr class="border-stone-400"/>
		<div>
			<label>
				<input type="checkbox" v-model="uiOpts.jumpToSearchedNode" @change="onUiOptChg('jumpToSearchedNode')"/>
				Jump to search result
			</label>
		</div>
		<hr class="border-stone-400"/>
		<div>
			Tree
			<ul>
				<li>
					<label> <input type="radio" v-model="uiOpts.useReducedTree" :value="false"
						@change="onUiOptChg('useReducedTree')"/> Default </label>
				</li>
				<li>
					<label> <input type="radio" v-model="uiOpts.useReducedTree" :value="true"
						@change="onUiOptChg('useReducedTree')"/> Reduced </label>
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
