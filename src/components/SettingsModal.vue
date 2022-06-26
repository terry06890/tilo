<script lang="ts">

import {defineComponent, PropType} from 'vue';
import RButton from './RButton.vue';
import CloseIcon from './icon/CloseIcon.vue';
import {UiOptions} from '../lib';
import {LayoutOptions} from '../layout';

export default defineComponent({
	props: {
		lytOpts: {type: Object as PropType<LayoutOptions>, required: true},
		uiOpts: {type: Object as PropType<UiOptions>, required: true},
	},
	data(){
		// For making subsets of various options' values available for user selection
		let userLayoutTypeVals = [ // Holds pairs of labels with option values
			['Yes', 'sweep'],
			['No', 'rect']
		];
		let userTileSpacingVals = [
			['Small', 6],
			['Medium', 10],
			['Large', 20]
		];
		let userTileSizeVals = [
			['Default', 50, 200],
			['Small', 50, 50],
			['Medium', 100, 100],
			['Large', 200, 200],
			['Flexible', 0, 400],
		];
		// Warn if user-available values don't include the active option value (indicates a developer mistake)
		let layoutTypeIdx = userLayoutTypeVals.findIndex(([, optVal]) => optVal == this.lytOpts.layoutType);
		if (layoutTypeIdx == -1){
			console.log("WARNING: Initial layoutType option value not included in user setting values");
		}
		let tileSpacingIdx = userTileSpacingVals.findIndex(([, optVal]) => optVal == this.lytOpts.tileSpacing);
		if (tileSpacingIdx == -1){
			console.log("WARNING: Initial tileSpacing option value not included in user setting values");
		}
		let tileSizeValIdx = userTileSizeVals.findIndex(
			([, min, max]) => min == this.lytOpts.minTileSz && max == this.lytOpts.maxTileSz
		);
		if (tileSizeValIdx == -1){
			console.log("WARNING: Initial minTileSz/maxTileSz option value not included in user setting values");
		}
		//
		return {
			userLayoutTypeVals,
			userLayoutType: userLayoutTypeVals[layoutTypeIdx != -1 ? layoutTypeIdx : 0][0],
			userTileSpacingVals,
			userTileSpacing: userTileSpacingVals[tileSpacingIdx != -1 ? tileSpacingIdx : 0][0],
			userTileSizeVals,
			userTileSize: userTileSizeVals[tileSizeValIdx != -1 ? tileSizeValIdx : 0][0],
		};
	},
	computed: {
		styles(): Record<string,string> {
			return {
				backgroundColor: this.uiOpts.bgColorAlt,
				borderRadius: this.uiOpts.borderRadius + 'px',
				boxShadow: this.uiOpts.shadowNormal,
			};
		},
	},
	methods: {
		onClose(evt: Event){
			if (evt.target == this.$el || (this.$refs.closeIcon as typeof CloseIcon).$el.contains(evt.target)){
				this.$emit('close');
			}
		},
		onSettingChg(setting: string){
			this.$emit('setting-chg', setting);
		},
	},
	watch: {
		// Propagate option-subsetting user-settings to options
		userLayoutType(newVal, oldVal){
			let [,optVal] = this.userLayoutTypeVals.find(([val,]) => val == newVal)!;
			this.lytOpts.layoutType = optVal as LayoutOptions['layoutType'];
		},
		userTileSpacing(newVal, oldVal){
			let [,optVal] = this.userTileSpacingVals.find(([val,]) => val == newVal)!;
			this.lytOpts.tileSpacing = optVal as LayoutOptions['tileSpacing'];
		},
		userTileSize(newVal, oldVal){
			let [,min,max] = this.userTileSizeVals.find(([val,,]) => val == newVal)!;
			this.lytOpts.minTileSz = min as LayoutOptions['minTileSz'];
			this.lytOpts.maxTileSz = max as LayoutOptions['maxTileSz'];
		},
	},
	components: {RButton, CloseIcon, },
	emits: ['close', 'setting-chg', 'reset', ],
});
</script>

<template>
<div class="fixed left-0 top-0 w-full h-full bg-black/40" @click="onClose">
	<div class="absolute left-1/2 -translate-x-1/2 top-1/2 -translate-y-1/2
		min-w-[8cm] max-h-[80%] overflow-auto p-3" :style="styles">
		<close-icon @click.stop="onClose" ref="closeIcon"
			class="block absolute top-2 right-2 w-6 h-6 hover:cursor-pointer" />
		<h1 class="text-xl font-bold mb-2">Settings</h1>
		<div class="border rounded">
			<h2 class="text-center">Layout</h2>
			<div class="grid grid-cols-2 gap-2">
				<div>
					Sweep leaves to side
					<ul>
						<li v-for="[val,] in userLayoutTypeVals">
							<label> <input type="radio" v-model="userLayoutType" :value="val"
								@change="onSettingChg('layoutType')"/> {{val}} </label>
						</li>
					</ul>
				</div>
				<div>
					Sweep into parent
					<ul>
						<li> <label> <input type="radio" :disabled="lytOpts.layoutType != 'sweep'"
							v-model="lytOpts.sweepToParent" value="none"
							@change="onSettingChg('sweepToParent')"/> Never </label> </li>
						<li> <label> <input type="radio" :disabled="lytOpts.layoutType != 'sweep'"
							v-model="lytOpts.sweepToParent" value="prefer"
							@change="onSettingChg('sweepToParent')"/> Always </label> </li>
						<li> <label> <input type="radio" :disabled="lytOpts.layoutType != 'sweep'"
							v-model="lytOpts.sweepToParent" value="fallback"
							@change="onSettingChg('sweepToParent')"/> If needed </label> </li>
					</ul>
				</div>
				<div>
					Tile Spacing
					<ul>
						<li v-for="[val,] in userTileSpacingVals">
							<label> <input type="radio" v-model="userTileSpacing" :value="val"
								@change="onSettingChg('tileSpacing')"/> {{val}} </label>
						</li>
					</ul>
				</div>
				<div>
					Tile Size
					<ul>
						<li v-for="[val,,] in userTileSizeVals">
							<label> <input type="radio" v-model="userTileSize" :value="val"
								@change="onSettingChg('minTileSz'), onSettingChg('maxTileSz')"/> {{val}} </label>
						</li>
					</ul>
				</div>
			</div>
		</div>
		<div class="border rounded">
			<h2 class="text-center">Timing</h2>
			<div class="grid grid-cols-3">
				<!-- Row 1 -->
				<label for="animationTimeInput">Animation Time</label>
				<input type="range" min="0" max="3000" class="my-auto" name="animationTimeInput"
					v-model.number="uiOpts.transitionDuration" @change="onSettingChg('transitionDuration')"/>
				<div class="my-auto">{{uiOpts.transitionDuration}} ms</div>
				<!-- Row 2 -->
				<label for="autoModeDelayInput">Auo-mode Delay</label>
				<input type="range" min="0" max="3000" class="my-auto" name="autoModeDelayInput"
					v-model.number="uiOpts.autoActionDelay" @change="onSettingChg('autoActionDelay')"/>
				<div class="my-auto">{{uiOpts.autoActionDelay}} ms</div>
			</div>
		</div>
		<div class="border rounded">
			<h2 class="text-center">Other</h2>
			<div>
				<label> <input type="checkbox" v-model="uiOpts.useReducedTree"
					@change="onSettingChg('useReducedTree')"/> Use simplified tree </label>
			</div>
			<div>
				<label> <input type="checkbox" v-model="uiOpts.searchJumpMode"
					@change="onSettingChg('searchJumpMode')"/> Skip search animation </label>
			</div>
		</div>
		<r-button class="mx-auto mt-2" :style="{color: uiOpts.textColor, backgroundColor: uiOpts.bgColor}"
			@click="$emit('reset')">
			Reset
		</r-button>
	</div>
</div>
</template>
