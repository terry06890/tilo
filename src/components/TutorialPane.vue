<template>
<div :style="styles" class="relative flex flex-col justify-between">
	<close-icon @click.stop="onClose" class="absolute top-2 right-2 w-8 h-8 hover:cursor-pointer"/>
	<h1 class="text-center text-lg font-bold pt-3 pb-2">
		{{stage == 0 ? 'Welcome' : `Tutorial (Step ${stage} of ${LAST_STAGE})`}}
	</h1>
	<transition name="fade" mode="out-in">
		<div v-if="stage == 0" :style="contentStyles">
			This is a visual explorer for the biological Tree of Life.
		</div>
		<div v-else-if="stage == 1" :style="contentStyles">
			{{touchDevice ? 'Tap' : 'Click'}} a tile to expand it, showing its children
		</div>
		<div v-else-if="stage == 2" :style="contentStyles">
			{{touchDevice ? 'Tap' : 'Click'}} an expanded tile's title to shrink it
		</div>
		<div v-else-if="stage == 3" :style="contentStyles">
			{{touchDevice ? 'Double tap' : 'Click and hold'}} a tile to hide its ancestors
			<span class="block text-sm brightness-50">
				For an expanded tile, {{touchDevice ? 'double tap' : 'click and hold'}} its title
			</span>
		</div>
		<div v-else-if="stage == 4" :style="contentStyles">
			{{touchDevice ? 'Tap' : 'Click'}} a tile in the sidebar to unhide it
		</div>
		<div v-else-if="stage == 5" :style="contentStyles">
			{{touchDevice ? 'Tap' : 'Click'}} the icon on a tile's bottom-right to
			bring up more information
			<span class="block text-sm brightness-50">
				For an expanded tile, it's to the right of the title
			</span>
		</div>
		<div v-else-if="stage == 6" :style="contentStyles">
			{{touchDevice ? 'Tap' : 'Click'}} the icon at the top right of screen to search
			<span class="block text-sm brightness-50">
				Or press Ctrl-F
			</span>
		</div>
		<div v-else-if="stage == 7" :style="contentStyles">
			{{touchDevice ? 'Tap' : 'Click'}} the play icon to traverse the tree automatically
		</div>
		<div v-else-if="stage == 8" :style="contentStyles">
			{{touchDevice ? 'Tap' : 'Click'}} the settings icon
		</div>
		<div v-else-if="stage == 9" :style="contentStyles">
			And finally, {{touchDevice ? 'tap' : 'click'}} the help icon for more information
		</div>
	</transition>
	<!-- Buttons -->
	<div class="w-full my-2 flex justify-evenly">
		<template v-if="stage == 0">
			<s-button :style="buttonStyles" @click="onStartTutorial">Start Tutorial</s-button>
			<s-button :style="buttonStyles" @click="onSkipTutorial">Skip</s-button>
		</template>
		<template v-else>
			<s-button :class="{invisible: !hidNextPrevOnce && stage == 1}" :disabled="stage == 1"
				@click="onPrevClick" :style="buttonStyles">
				Prev
			</s-button>
			<s-button :class="{invisible: !hidNextPrevOnce && stage == 1}"
				@click="stage != LAST_STAGE ? onNextClick() : onClose()" :style="buttonStyles">
				{{stage != LAST_STAGE ? 'Next' : 'Finish'}}
			</s-button>
		</template>
	</div>
</div>
</template>

<script setup lang="ts">
import {ref, computed, watch, onMounted, PropType} from 'vue';
import SButton from './SButton.vue';
import CloseIcon from './icon/CloseIcon.vue';
import {Action} from '../lib';
import {useStore} from '../store';

// Global store
const store = useStore();

// Props + events
const props = defineProps({
	actionsDone: {type: Object as PropType<Set<Action>>, required: true},
		// Used to avoid disabling actions already done
	triggerFlag: {type: Boolean, required: true},
		// Used to indicate that a tutorial-requested 'trigger' action has been done
	skipWelcome: {type: Boolean, default: false},
});
const touchDevice = computed(() => store.touchDevice);
const emit = defineEmits(['close', 'stage-chg', 'skip']);

// For tutorial stage
const stage = ref(props.skipWelcome ? 1 : 0);
	// Indicates the current step of the tutorial (stage 0 is the welcome message)
const LAST_STAGE = 9;
const STAGE_ACTIONS = [
	// Specifies, for stages 1+, what action to enable (can repeat an action to enable nothing new)
	'expand', 'collapse', 'expandToView', 'unhideAncestor',
	'tileInfo', 'search', 'autoMode', 'settings', 'help',
] as Action[];
let disabledOnce = false; // Set to true after disabling features at stage 1
const hidNextPrevOnce = ref(false); // Used to hide prev/next buttons when initially at stage 1

// For stage changes
function onStartTutorial(){
	stage.value = 1;
}
function onSkipTutorial(){
	emit('skip');
	emit('close');
}
function onPrevClick(){
	stage.value = Math.max(1, stage.value - 1);
}
function onNextClick(){
	stage.value = Math.min(stage.value + 1, LAST_STAGE);
}
function onClose(){
	emit('close');
}
function onStageChange(){
	// If starting tutorial, disable 'all' actions
	if (stage.value == 1 && !disabledOnce){
		for (let action of STAGE_ACTIONS){
			if (action != null && !props.actionsDone.has(action)){
				store.disabledActions.add(action);
			}
		}
		disabledOnce = true;
	}
	// Enable action for this stage
	store.disabledActions.delete(STAGE_ACTIONS[stage.value - 1]);
	// Notify of new trigger-action
	emit('stage-chg', STAGE_ACTIONS[stage.value - 1]);
	// After stage 1, show prev/next buttons
	if (stage.value == 2){
		hidNextPrevOnce.value = true;
	}
}
onMounted(() => {
	if (props.skipWelcome){
		onStageChange();
	}
})
watch(stage, onStageChange);
watch(() => props.triggerFlag, () => {
	if (stage.value < LAST_STAGE){
		onNextClick();
	} else {
		onClose();
	}
});

// Styles
const styles = computed(() => ({
	backgroundColor: store.color.bgDark,
	color: store.color.text,
}));
const contentStyles = {
	padding: '0 0.5cm',
	overflow: 'auto',
	textAlign: 'center',
};
const buttonStyles = computed(() => ({
	color: store.color.text,
	backgroundColor: store.color.bg,
}));
</script>
