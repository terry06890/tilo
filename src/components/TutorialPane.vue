<template>
<div :style="styles" class="relative flex flex-col justify-between">
	<close-icon @click.stop="onClose" class="absolute top-2 right-2 w-8 h-8 hover:cursor-pointer"/>
	<h1 class="text-center text-lg font-bold pt-3 pb-2">
		{{stage == 0 ? 'Welcome' : `Tutorial (Step ${stage} of ${lastStage})`}}
	</h1>
	<transition name="fade" mode="out-in">
		<div v-if="stage == 0" :style="contentStyles">
			This is a visual explorer for the biological Tree of Life.
		</div>
		<div v-else-if="stage == 1" :style="contentStyles">
			{{touchDevice ? 'Tap' : 'Click'}} a tile to expand it, showing it's children
		</div>
		<div v-else-if="stage == 2" :style="contentStyles">
			{{touchDevice ? 'Tap' : 'Click'}} an expanded tile's title to shrink it
		</div>
		<div v-else-if="stage == 3" :style="contentStyles">
			{{touchDevice ? 'Double tap' : 'Click and hold'}} a tile to hide it's ancestors
			<span class="block text-sm brightness-50">
				For an expanded tile, {{touchDevice ? 'double tap' : 'click and hold'}} it's title
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
			{{touchDevice ? 'Tap' : 'Click'}} the icon at the top-right to search
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
				@click="stage != lastStage ? onNextClick() : onClose()" :style="buttonStyles">
				{{stage != lastStage ? 'Next' : 'Finish'}}
			</s-button>
		</template>
	</div>
</div>
</template>

<script lang="ts">
import {defineComponent, PropType} from 'vue';
import SButton from './SButton.vue';
import CloseIcon from './icon/CloseIcon.vue';
import {Action, UiOptions} from '../lib';

export default defineComponent({
	props: {
		actionsDone: {type: Object as PropType<Set<Action>>, required: true},
			// Used to avoid disabling actions already done
		triggerFlag: {type: Boolean, required: true},
			// Used to indicate that a tutorial-requested 'trigger' action has been done
		skipWelcome: {type: Boolean, default: false},
		uiOpts: {type: Object as PropType<UiOptions>, required: true},
	},
	data(){
		return {
			stage: 0, // Indicates the current step of the tutorial (stage 0 is the welcome message)
			lastStage: 9,
			disabledOnce: false, // Set to true after disabling features at stage 1
			stageActions: [
				// Specifies, for stages 1+, what action to enable (can repeat an action to enable nothing new)
				'expand', 'collapse', 'expandToView', 'unhideAncestor',
				'tileInfo', 'search', 'autoMode', 'settings', 'help',
			] as Action[],
			hidNextPrevOnce: false, // Used to hide prev/next buttons when initially at stage 1
		};
	},
	computed: {
		 styles(): Record<string,string> {
			return {
				backgroundColor: this.uiOpts.bgColorDark,
				color: this.uiOpts.textColor,
			};
		 },
		 contentStyles(): Record<string,string> {
			return {
				padding: '0 0.5cm',
				overflow: 'auto',
				textAlign: 'center',
			};
		 },
		 buttonStyles(): Record<string,string> {
			return {
				color: this.uiOpts.textColor,
				backgroundColor: this.uiOpts.bgColor,
			};
		},
		touchDevice(): boolean {
			return this.uiOpts.touchDevice;
		},
	},
	methods: {
		onStartTutorial(){
			this.stage = 1;
		},
		onSkipTutorial(){
			this.$emit('skip');
			this.$emit('close');
		},
		onPrevClick(){
			this.stage = Math.max(1, this.stage - 1);
		},
		onNextClick(){
			this.stage = Math.min(this.stage + 1, this.lastStage);
		},
		onClose(){
			this.$emit('close');
		},
	},
	watch: {
		stage(newVal, oldVal){
			// If starting tutorial, disable 'all' actions
			if (newVal == 1 && !this.disabledOnce){
				for (let action of this.stageActions){
					if (action != null && !this.actionsDone.has(action)){
						this.uiOpts.disabledActions.add(action);
					}
				}
				this.disabledOnce = true;
			}
			// Enable action for this stage
			this.uiOpts.disabledActions.delete(this.stageActions[this.stage - 1]);
			// Notify of new trigger-action
			this.$emit('stage-chg', this.stageActions[this.stage - 1]);
			// After stage 1, show prev/next buttons
			if (newVal == 2){
				this.hidNextPrevOnce = true;
			}
		},
		// Called when a trigger-action is done, and advances to the next stage
		triggerFlag(){
			if (this.stage < this.lastStage){
				this.onNextClick();
			} else {
				this.onClose();
			}
		},
	},
	created(){
		if (this.skipWelcome){
			this.stage += 1;
		}
	},
	components: {CloseIcon, SButton, },
	emits: ['close', 'stage-chg', 'skip', ],
});
</script>
