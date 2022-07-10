<template>
<div class="fixed left-0 top-0 w-full h-full bg-black/40" @click="onClose">
	<div class="absolute left-1/2 -translate-x-1/2 top-1/2 -translate-y-1/2
		min-w-[8cm] max-w-[80%] max-h-[80%] overflow-auto" :style="styles">
		<close-icon @click.stop="onClose" ref="closeIcon"
			class="absolute top-1 right-1 md:top-2 md:right-2 w-8 h-8 hover:cursor-pointer" />
		<h1 class="text-xl md:text-2xl font-bold text-center py-2" :class="borderBClasses">Settings</h1>
		<div class="pb-2" :class="borderBClasses">
			<h2 class="font-bold md:text-xl text-center pt-1 md:pt-2 md:pb-1">Timing</h2>
			<div class="grid grid-cols-[130px_minmax(0,1fr)_65px] gap-1 px-2 md:px-3">
				<!-- Row 1 -->
				<label for="animTimeInput" @click="onReset('UI', 'transitionDuration')" :class="rLabelClasses">
					Animation Time
				</label>
				<input type="range" min="0" max="1000" v-model.number="uiOpts.transitionDuration"
					@change="onSettingChg('UI', 'transitionDuration')" class="my-auto" name="animTimeInput"/>
				<div class="my-auto text-right">{{uiOpts.transitionDuration}} ms</div>
				<!-- Row 2 -->
				<label for="autoDelayInput" @click="onReset('UI', 'autoActionDelay')" :class="rLabelClasses">
					Auto-mode Delay
				</label>
				<input type="range" min="100" max="1000" v-model.number="uiOpts.autoActionDelay"
					@change="onSettingChg('UI', 'autoActionDelay')" class="my-auto" name="autoDelayInput"/>
				<div class="my-auto text-right">{{uiOpts.autoActionDelay}} ms</div>
			</div>
		</div>
		<div class="pb-2" :class="borderBClasses">
			<h2 class="font-bold md:text-xl text-center pt-1 md:pt-2 md:pb-1">Layout</h2>
			<div class="flex gap-2 justify-around px-2 pb-1">
				<div>
					<div>Sweep leaves left</div>
					<ul>
						<li> <label> <input type="radio" v-model="sweepLeaves" :value="true"
							@change="onSettingChg('LYT', 'layoutType')"/> Yes </label> </li>
						<li> <label> <input type="radio" v-model="sweepLeaves" :value="false"
							@change="onSettingChg('LYT', 'layoutType')"/> No </label> </li>
					</ul>
				</div>
				<div>
					<div>Sweep into parent</div>
					<ul>
						<li> <label> <input type="radio" :disabled="!sweepLeaves" v-model="lytOpts.sweepToParent"
							value="none" @change="onSettingChg('LYT', 'sweepToParent')"/> Never </label> </li>
						<li> <label> <input type="radio" :disabled="!sweepLeaves" v-model="lytOpts.sweepToParent"
							value="prefer" @change="onSettingChg('LYT', 'sweepToParent')"/> Always </label> </li>
						<li> <label> <input type="radio" :disabled="!sweepLeaves" v-model="lytOpts.sweepToParent"
							value="fallback" @change="onSettingChg('LYT', 'sweepToParent')"/> If needed </label> </li>
					</ul>
				</div>
			</div>
			<div class="grid grid-cols-[100px_minmax(0,1fr)_65px] gap-1 w-fit mx-auto px-2 md:px-3">
				<!-- Row 1 -->
				<label for="minTileSizeInput" @click="onReset('LYT', 'minTileSz')" :class="rLabelClasses">
					Min Tile Size
				</label>
				<input type="range"
					min="15" :max="uiOpts.breakpoint == 'sm' ? 150 : 200" v-model.number="lytOpts.minTileSz"
					@input="onSettingChgThrottled('LYT', 'minTileSz')" @change="onSettingChg('LYT', 'minTileSz')"
					name="minTileSizeInput" ref="minTileSzInput"/>
				<div class="my-auto text-right">{{lytOpts.minTileSz}} px</div>
				<!-- Row 2 -->
				<label for="maxTileSizeInput" @click="onReset('LYT', 'maxTileSz')" :class="rLabelClasses">
					Max Tile Size
				</label>
				<input type="range" min="15" max="400" v-model.number="lytOpts.maxTileSz"
					@input="onSettingChgThrottled('LYT', 'maxTileSz')" @change="onSettingChg('LYT', 'maxTileSz')"
					name="maxTileSizeInput" ref="maxTileSzInput"/>
				<div class="my-auto text-right">{{lytOpts.maxTileSz}} px</div>
				<!-- Row 3 -->
				<label for="tileSpacingInput" @click="onReset('LYT', 'tileSpacing')" :class="rLabelClasses">
					Tile Spacing
				</label>
				<input type="range" min="0" max="20" v-model.number="lytOpts.tileSpacing"
					@input="onSettingChgThrottled('LYT', 'tileSpacing')" @change="onSettingChg('LYT', 'tileSpacing')"
					name="tileSpacingInput"/>
				<div class="my-auto text-right">{{lytOpts.tileSpacing}} px</div>
			</div>
		</div>
		<div class="pb-2 px-2 md:px-3" :class="borderBClasses">
			<h2 class="font-bold md:text-xl text-center pt-1 md:pt-2 -mb-2 ">Other</h2>
			<div>
				Tree to use
				<ul class="flex justify-evenly">
					<li> <label> <input type="radio" v-model="uiOpts.tree" value="trimmed"
						@change="onSettingChg('UI', 'tree')"/> Complex </label> </li>
					<li> <label> <input type="radio" v-model="uiOpts.tree" value="images"
						@change="onSettingChg('UI', 'tree')"/> Visual </label> </li>
					<li> <label> <input type="radio" v-model="uiOpts.tree" value="picked"
						@change="onSettingChg('UI', 'tree')"/> Minimal </label> </li>
				</ul>
			</div>
			<div>
				<label> <input type="checkbox" v-model="uiOpts.searchJumpMode"
					@change="onSettingChg('UI', 'searchJumpMode')"/> Skip search animation </label>
			</div>
			<div>
				<label> <input type="checkbox" v-model="uiOpts.autoHide"
					@change="onSettingChg('UI', 'autoHide')"/> Auto-hide ancestors </label>
			</div>
			<div v-if="uiOpts.touchDevice == false">
				<label> <input type="checkbox" v-model="uiOpts.disableShortcuts"
					@change="onSettingChg('UI', 'disableShortcuts')"/> Disable keyboard shortcuts </label>
			</div>
		</div>
		<s-button class="mx-auto my-2" :style="{color: uiOpts.textColor, backgroundColor: uiOpts.bgColor}"
			@click="onResetAll">
			Reset
		</s-button>
		<transition name="fade">
			<div v-if="saved" class="absolute right-1 bottom-1" ref="saveIndicator">
				Saved
			</div>
		</transition>
	</div>
</div>
</template>

<script lang="ts">
import {defineComponent, PropType} from 'vue';
import SButton from './SButton.vue';
import CloseIcon from './icon/CloseIcon.vue';
import {UiOptions, OptionType, getDefaultLytOpts, getDefaultUiOpts} from '../lib';
import {LayoutOptions} from '../layout';

export default defineComponent({
	props: {
		lytOpts: {type: Object as PropType<LayoutOptions>, required: true},
		uiOpts: {type: Object as PropType<UiOptions>, required: true},
	},
	data(){
		return {
			sweepLeaves: this.lytOpts.layoutType == 'sweep',
				// For making only two of 'layoutType's values available for user selection
			saved: false, // Set to true after a setting is saved
			settingChgTimeout: 0, // Use to throttle some setting-change handling
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
		borderBClasses(): string {
			return 'border-b border-stone-400';
		},
		rLabelClasses(): string { // For reset-upon-click labels
			return "w-fit hover:cursor-pointer hover:text-lime-600";
		},
	},
	methods: {
		onClose(evt: Event){
			if (evt.target == this.$el || (this.$refs.closeIcon as typeof CloseIcon).$el.contains(evt.target)){
				this.$emit('close');
			}
		},
		onSettingChg(optionType: OptionType, option: string){
			// Maintain min/max-tile-size consistency
			if (optionType == 'LYT' && (option == 'minTileSz' || option == 'maxTileSz')){
				let minInput = this.$refs.minTileSzInput as HTMLInputElement;
				let maxInput = this.$refs.maxTileSzInput as HTMLInputElement;
				if (option == 'minTileSz' && Number(minInput.value) > Number(maxInput.value)){
					this.lytOpts.maxTileSz = this.lytOpts.minTileSz;
					this.$emit('setting-chg', 'LYT', 'maxTileSz');
				} else if (option == 'maxTileSz' && Number(maxInput.value) < Number(minInput.value)){
					this.lytOpts.minTileSz = this.lytOpts.maxTileSz;
					this.$emit('setting-chg', 'LYT', 'minTileSz');
				}
			}
			// Notify parent component
			this.$emit('setting-chg', optionType, option,
				{relayout: optionType == 'LYT', reinit: optionType == 'UI' && option == 'tree'});
			// Possibly make saved-indicator appear/animate
			if (!this.saved){
				this.saved = true;
			} else {
				let el = this.$refs.saveIndicator as HTMLDivElement;
				el.classList.remove('animate-flash-green');
				el.offsetWidth; // Triggers reflow
				el.classList.add('animate-flash-green');
			}
		},
		onSettingChgThrottled(optionType: OptionType, option: string){
			if (this.settingChgTimeout == 0){
				this.settingChgTimeout = setTimeout(() => {
					this.settingChgTimeout = 0;
					this.onSettingChg(optionType, option);
				}, this.uiOpts.animationDelay);
			}
		},
		onReset(optionType: OptionType, option: string){
			// Restore the setting's default
			let defaultLytOpts = getDefaultLytOpts();
			let defaultUiOpts = getDefaultUiOpts(defaultLytOpts);
			if (optionType == 'LYT'){
				let lytOpt = option as keyof LayoutOptions;
				if (this.lytOpts[lytOpt] == defaultLytOpts[lytOpt]){
					return;
				}
				(this.lytOpts[lytOpt] as any) = defaultLytOpts[lytOpt];
				if (option == 'layoutType'){
					this.sweepLeaves = this.lytOpts.layoutType == 'sweep';
				}
			} else {
				let uiOpt = option as keyof UiOptions;
				if (this.uiOpts[uiOpt] == defaultUiOpts[uiOpt]){
					return;
				}
				(this.uiOpts[uiOpt] as any) = defaultUiOpts[uiOpt];
			}
			// Notify parent component
			this.onSettingChg(optionType, option);
		},
		onResetAll(){
			// Restore default options
			let defaultLytOpts = getDefaultLytOpts();
			let defaultUiOpts = getDefaultUiOpts(defaultLytOpts);
			let needReinit = this.uiOpts.tree != defaultUiOpts.tree;
			Object.assign(this.lytOpts, defaultLytOpts);
			Object.assign(this.uiOpts, defaultUiOpts);
			// Notify parent component
			this.$emit('reset', needReinit);
			// Clear saved-indicator
			this.saved = false;
		},
	},
	watch: {
		sweepLeaves(newVal: boolean, oldVal: boolean){
			this.lytOpts.layoutType = newVal ? 'sweep' : 'rect';
		},
	},
	components: {SButton, CloseIcon, },
	emits: ['close', 'setting-chg', 'reset', ],
});
</script>
