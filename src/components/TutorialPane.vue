<template>
<div :style="styles" class="relative flex flex-col justify-between">
	<close-icon @click.stop="onClose"
		class="block absolute top-2 right-2 w-8 h-8 hover:cursor-pointer"/>
	<h1 class="text-center text-lg font-bold pt-3 pb-2">
		{{stage == 0 ? 'Welcome' : `Tutorial (Step ${stage} of ${lastStage})`}}
	</h1>
	<transition name="fade" mode="out-in">
		<div v-if="stage == 0" :style="contentStyles">
			This site provides a visualisation for the biological Tree of Life.
		</div>
		<div v-else-if="stage == 1" :style="contentStyles">
			{{touchDevice ? 'Tap' : 'Click'}} a tile to expand it and show it's children
		</div>
		<div v-else-if="stage == 2" :style="contentStyles">
			{{touchDevice ? 'Tap' : 'Click'}} an expanded tile's header to shrink it
		</div>
		<div v-else-if="stage == 3" :style="contentStyles">
			{{touchDevice ? 'Double tap' : 'Click and hold'}} a tile to hide it's ancestors
			<span class="block text-sm brightness-50">
				For an expanded tile, use the header
			</span>
		</div>
		<div v-else-if="stage == 4" :style="contentStyles">
			{{touchDevice ? 'Tap' : 'Click'}} a tile in the sidebar to unhide it
		</div>
		<div v-else-if="stage == 5" :style="contentStyles">
			{{touchDevice ? 'Tap' : 'Click'}} the icon on a tile's bottom-right to
			bring up more information
			<span class="block text-sm brightness-50">
				For an expanded tile, it's on the header's right
			</span>
		</div>
		<div v-else-if="stage == 6" :style="contentStyles">
			{{touchDevice ? 'Tap' : 'Click'}} the icon at the top-right to search
			<span class="block text-sm brightness-50">
				Or press Ctrl-F
			</span>
		</div>
		<div v-else-if="stage == 7" :style="contentStyles">
			{{touchDevice ? 'Tap' : 'Click'}} the play icon to start Auto Mode
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
		skipWelcome: {type: Boolean, default: false},
		triggerFlag: {type: Boolean, required: true},
			// Used to indicate that a tutorial-requested 'trigger' action has been done
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
	watch: {
		stage(newVal, oldVal){
			// If starting tutorial, disable 'all' actions
			if (newVal == 1 && !this.disabledOnce){
				for (let action of this.stageActions){
					if (action != null){
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
	created(){
		if (this.skipWelcome){
			this.stage += 1;
		}
	},
	components: {CloseIcon, SButton, },
	emits: ['close', 'stage-chg', 'skip', ],
});
</script>
