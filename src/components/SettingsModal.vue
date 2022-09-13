<template>
<div class="fixed left-0 top-0 w-full h-full bg-black/40" @click="onClose" ref="rootRef">
	<div class="absolute left-1/2 -translate-x-1/2 top-1/2 -translate-y-1/2
		min-w-[8cm] max-w-[80%] max-h-[80%] overflow-auto" :style="styles">
		<close-icon @click.stop="onClose" ref="closeRef"
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
					name="minTileSizeInput" ref="minTileSzRef"/>
				<div class="my-auto text-right">{{lytOpts.minTileSz}} px</div>
				<!-- Row 2 -->
				<label for="maxTileSizeInput" @click="onReset('LYT', 'maxTileSz')" :class="rLabelClasses">
					Max Tile Size
				</label>
				<input type="range" min="15" max="400" v-model.number="lytOpts.maxTileSz"
					@input="onSettingChgThrottled('LYT', 'maxTileSz')" @change="onSettingChg('LYT', 'maxTileSz')"
					name="maxTileSizeInput" ref="maxTileSzRef"/>
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
			<div v-if="saved" class="absolute right-1 bottom-1" ref="saveIndRef"> Saved </div>
		</transition>
	</div>
</div>
</template>

<script setup lang="ts">
import {ref, computed, watch, PropType} from 'vue';
import SButton from './SButton.vue';
import CloseIcon from './icon/CloseIcon.vue';
import {UiOptions, OptionType, getDefaultLytOpts, getDefaultUiOpts} from '../lib';
import {LayoutOptions} from '../layout';

// Refs
const rootRef = ref(null as HTMLDivElement | null);
const closeRef = ref(null as typeof CloseIcon | null);
const minTileSzRef = ref(null as HTMLInputElement | null);
const maxTileSzRef = ref(null as HTMLInputElement | null);
const saveIndRef = ref(null as HTMLDivElement | null);

// Props + events
const props = defineProps({
	lytOpts: {type: Object as PropType<LayoutOptions>, required: true},
	uiOpts: {type: Object as PropType<UiOptions>, required: true},
});
const emit = defineEmits(['close', 'setting-chg', 'reset', ]);

// For settings
const sweepLeaves = ref(props.lytOpts.layoutType == 'sweep');
	// For making only two of 'layoutType's values available for user selection)
watch(sweepLeaves, (newVal) => {props.lytOpts.layoutType = newVal ? 'sweep' : 'rect'})

// Settings change handling
const saved = ref(false); // Set to true after a setting is saved
const settingChgTimeout = ref(0); // Used to throttle some setting-change handling
function onSettingChg(optionType: OptionType, option: string){
	// Maintain min/max-tile-size consistency
	if (optionType == 'LYT' && (option == 'minTileSz' || option == 'maxTileSz')){
		let minInput = minTileSzRef.value!;
		let maxInput = maxTileSzRef.value!;
		if (option == 'minTileSz' && Number(minInput.value) > Number(maxInput.value)){
			props.lytOpts.maxTileSz = props.lytOpts.minTileSz;
			emit('setting-chg', 'LYT', 'maxTileSz');
		} else if (option == 'maxTileSz' && Number(maxInput.value) < Number(minInput.value)){
			props.lytOpts.minTileSz = props.lytOpts.maxTileSz;
			emit('setting-chg', 'LYT', 'minTileSz');
		}
	}
	// Notify parent component
	emit('setting-chg', optionType, option,
		{relayout: optionType == 'LYT', reinit: optionType == 'UI' && option == 'tree'});
	// Possibly make saved-indicator appear/animate
	if (!saved.value){
		saved.value = true;
	} else {
		let el = saveIndRef.value!;
		el.classList.remove('animate-flash-green');
		el.offsetWidth; // Triggers reflow
		el.classList.add('animate-flash-green');
	}
}
function onSettingChgThrottled(optionType: OptionType, option: string){
	if (settingChgTimeout.value == 0){
		settingChgTimeout.value = setTimeout(() => {
			settingChgTimeout.value = 0;
			onSettingChg(optionType, option);
		}, props.uiOpts.animationDelay);
	}
}
function onReset(optionType: OptionType, option: string){
	// Restore the setting's default
	let defaultLytOpts = getDefaultLytOpts();
	let defaultUiOpts = getDefaultUiOpts(defaultLytOpts);
	if (optionType == 'LYT'){
		let lytOpt = option as keyof LayoutOptions;
		if (props.lytOpts[lytOpt] == defaultLytOpts[lytOpt]){
			return;
		}
		(props.lytOpts[lytOpt] as any) = defaultLytOpts[lytOpt];
		if (option == 'layoutType'){
			sweepLeaves.value = props.lytOpts.layoutType == 'sweep';
		}
	} else {
		let uiOpt = option as keyof UiOptions;
		if (props.uiOpts[uiOpt] == defaultUiOpts[uiOpt]){
			return;
		}
		(props.uiOpts[uiOpt] as any) = defaultUiOpts[uiOpt];
	}
	// Notify parent component
	onSettingChg(optionType, option);
}
function onResetAll(){
	// Restore default options
	let defaultLytOpts = getDefaultLytOpts();
	let defaultUiOpts = getDefaultUiOpts(defaultLytOpts);
	let needReinit = props.uiOpts.tree != defaultUiOpts.tree;
	Object.assign(props.lytOpts, defaultLytOpts);
	Object.assign(props.uiOpts, defaultUiOpts);
	// Notify parent component
	emit('reset', needReinit);
	// Clear saved-indicator
	saved.value = false;
}

// Close handling
function onClose(evt: Event){
	if (evt.target == rootRef.value || closeRef.value!.$el.contains(evt.target)){
		emit('close');
	}
}

// Styles and classes
const styles = computed(() => ({
	backgroundColor: props.uiOpts.bgColorAlt,
	borderRadius: props.uiOpts.borderRadius + 'px',
	boxShadow: props.uiOpts.shadowNormal,
}));
const borderBClasses = 'border-b border-stone-400';
const rLabelClasses = "w-fit hover:cursor-pointer hover:text-lime-600"; // For reset-upon-click labels
</script>
