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
				<label for="animTimeInput" @click="onResetOne('transitionDuration')" :class="rLabelClasses">
					Animation Time
				</label>
				<input type="range" min="0" max="1000" v-model.number="store.transitionDuration"
					@change="onSettingChg('transitionDuration')" class="my-auto" name="animTimeInput"/>
				<div class="my-auto text-right">{{store.transitionDuration}} ms</div>
				<!-- Row 2 -->
				<label for="autoDelayInput" @click="onResetOne('autoActionDelay')" :class="rLabelClasses">
					Auto-mode Delay
				</label>
				<input type="range" min="300" max="2000" v-model.number="store.autoActionDelay"
					@change="onSettingChg('autoActionDelay')" class="my-auto" name="autoDelayInput"/>
				<div class="my-auto text-right">{{store.autoActionDelay}} ms</div>
			</div>
		</div>
		<div class="pb-2" :class="borderBClasses">
			<h2 class="font-bold md:text-xl text-center pt-1 md:pt-2 md:pb-1">Layout</h2>
			<div class="flex gap-2 justify-around px-2 pb-1">
				<div>
					<div>Sweep leaves left</div>
					<ul>
						<li> <label> <input type="radio" v-model="sweepLeaves" :value="true"
							@change="onSettingChg('lytOpts.layoutType')"/> Yes </label> </li>
						<li> <label> <input type="radio" v-model="sweepLeaves" :value="false"
							@change="onSettingChg('lytOpts.layoutType')"/> No </label> </li>
					</ul>
				</div>
				<div>
					<div>Sweep into parent</div>
					<ul>
						<li> <label> <input type="radio" :disabled="!sweepLeaves" v-model="store.lytOpts.sweepToParent"
							value="none" @change="onSettingChg('lytOpts.sweepToParent')"/> Never </label> </li>
						<li> <label> <input type="radio" :disabled="!sweepLeaves" v-model="store.lytOpts.sweepToParent"
							value="prefer" @change="onSettingChg('lytOpts.sweepToParent')"/> Always </label> </li>
						<li> <label> <input type="radio" :disabled="!sweepLeaves" v-model="store.lytOpts.sweepToParent"
							value="fallback" @change="onSettingChg('lytOpts.sweepToParent')"/> If needed </label> </li>
					</ul>
				</div>
			</div>
			<div class="grid grid-cols-[100px_minmax(0,1fr)_65px] gap-1 w-fit mx-auto px-2 md:px-3">
				<!-- Row 1 -->
				<label for="minTileSizeInput" @click="onResetOne('lytOpts.minTileSz')" :class="rLabelClasses">
					Min Tile Size
				</label>
				<input type="range"
					min="15" :max="store.breakpoint == 'sm' ? 150 : 200" v-model.number="store.lytOpts.minTileSz"
					@input="onSettingChgThrottled('lytOpts.minTileSz')" @change="onSettingChg('lytOpts.minTileSz')"
					name="minTileSizeInput" ref="minTileSzRef"/>
				<div class="my-auto text-right">{{store.lytOpts.minTileSz}} px</div>
				<!-- Row 2 -->
				<label for="maxTileSizeInput" @click="onResetOne('lytOpts.maxTileSz')" :class="rLabelClasses">
					Max Tile Size
				</label>
				<input type="range" min="15" max="400" v-model.number="store.lytOpts.maxTileSz"
					@input="onSettingChgThrottled('lytOpts.maxTileSz')" @change="onSettingChg('lytOpts.maxTileSz')"
					name="maxTileSizeInput" ref="maxTileSzRef"/>
				<div class="my-auto text-right">{{store.lytOpts.maxTileSz}} px</div>
				<!-- Row 3 -->
				<label for="tileSpacingInput" @click="onResetOne('lytOpts.tileSpacing')" :class="rLabelClasses">
					Tile Spacing
				</label>
				<input type="range" min="0" max="20" v-model.number="store.lytOpts.tileSpacing"
					@input="onSettingChgThrottled('lytOpts.tileSpacing')" @change="onSettingChg('lytOpts.tileSpacing')"
					name="tileSpacingInput"/>
				<div class="my-auto text-right">{{store.lytOpts.tileSpacing}} px</div>
			</div>
		</div>
		<div class="pb-2 px-2 md:px-3" :class="borderBClasses">
			<h2 class="font-bold md:text-xl text-center pt-1 md:pt-2 -mb-2 ">Other</h2>
			<div>
				Tree to use
				<ul class="flex justify-evenly">
					<li> <label> <input type="radio" v-model="store.tree" value="trimmed"
						@change="onSettingChg('tree')"/> Complex </label> </li>
					<li> <label> <input type="radio" v-model="store.tree" value="images"
						@change="onSettingChg('tree')"/> Visual </label> </li>
					<li> <label> <input type="radio" v-model="store.tree" value="picked"
						@change="onSettingChg('tree')"/> Minimal </label> </li>
				</ul>
			</div>
			<div>
				<label> <input type="checkbox" v-model="store.searchJumpMode"
					@change="onSettingChg('searchJumpMode')"/> Skip search animation </label>
			</div>
			<div>
				<label> <input type="checkbox" v-model="store.autoHide"
					@change="onSettingChg('autoHide')"/> Auto-hide ancestors </label>
			</div>
			<div v-if="store.touchDevice == false">
				<label> <input type="checkbox" v-model="store.disableShortcuts"
					@change="onSettingChg('disableShortcuts')"/> Disable keyboard shortcuts </label>
			</div>
		</div>
		<s-button class="mx-auto my-2" :style="{color: store.color.text, backgroundColor: store.color.bg}"
			@click="onReset">
			Reset
		</s-button>
		<transition name="fade">
			<div v-if="saved" class="absolute right-1 bottom-1" ref="saveIndRef"> Saved </div>
		</transition>
	</div>
</div>
</template>

<script setup lang="ts">
import {ref, computed, watch} from 'vue';
import SButton from './SButton.vue';
import CloseIcon from './icon/CloseIcon.vue';
import {useStore, StoreState} from '../store';

// Refs
const rootRef = ref(null as HTMLDivElement | null);
const closeRef = ref(null as typeof CloseIcon | null);
const minTileSzRef = ref(null as HTMLInputElement | null);
const maxTileSzRef = ref(null as HTMLInputElement | null);
const saveIndRef = ref(null as HTMLDivElement | null);

// Global store
const store = useStore();

// Events
const emit = defineEmits(['close', 'setting-chg', 'reset']);

// For making only two of 'layoutType's values available for user selection)
const sweepLeaves = ref(store.lytOpts.layoutType == 'sweep');
watch(sweepLeaves, (newVal) => {store.lytOpts.layoutType = newVal ? 'sweep' : 'rect'})

// Settings change handling
const saved = ref(false); // Set to true after a setting is saved
let settingChgTimeout = 0; // Used to throttle some setting-change handling
function onSettingChg(option: string){
	// Maintain min/max-tile-size consistency
	if (option == 'lytOpts.minTileSz' || option == 'lytOpts.maxTileSz'){
		let minInput = minTileSzRef.value!;
		let maxInput = maxTileSzRef.value!;
		if (Number(minInput.value) > Number(maxInput.value)){
			if (option == 'lytOpts.minTileSz'){
				store.lytOpts.maxTileSz = store.lytOpts.minTileSz;
				emit('setting-chg', 'lytOpts.maxTileSz');
			} else {
				store.lytOpts.minTileSz = store.lytOpts.maxTileSz;
				emit('setting-chg', 'lytOpts.minTileSz');
			}
		}
	}
	// Notify parent (might need to relayout)
	emit('setting-chg', option);
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
function onSettingChgThrottled(option: string){
	if (settingChgTimeout == 0){
		settingChgTimeout = setTimeout(() => {
			settingChgTimeout = 0;
			onSettingChg(option);
		}, store.animationDelay);
	}
}
function onResetOne(option: string){
	store.resetOne(option);
	if (option == 'lytOpts.layoutType'){
		sweepLeaves.value = (store.lytOpts.layoutType == 'sweep');
	}
	onSettingChg(option);
}
function onReset(){
	emit('reset'); // Notify parent (might need to relayout)
	saved.value = false; // Clear saved-indicator
}

// Close handling
function onClose(evt: Event){
	if (evt.target == rootRef.value || closeRef.value!.$el.contains(evt.target)){
		emit('close');
	}
}

// Styles and classes
const styles = computed(() => ({
	backgroundColor: store.color.bgAlt,
	borderRadius: store.borderRadius + 'px',
	boxShadow: store.shadowNormal,
}));
const borderBClasses = 'border-b border-stone-400';
const rLabelClasses = "w-fit hover:cursor-pointer hover:text-lime-600"; // For reset-upon-click labels
</script>
