<template>
<div :style="styles" class="p-2 flex flex-col justify-between">
	<div class="flex">
		<h2 class="text-center mb-2 mx-auto">
			{{stage == 0 ? 'Welcome' : `Tutorial (${stage} / ${lastStage})`}}
		</h2>
		<close-icon @click.stop="onClose"
			class="block w-6 h-6 hover:cursor-pointer"/>
	</div>
	<transition name="fade" mode="out-in">
		<div v-if="stage == 0" :style="contentStyles">
			This page provides a visualisation of the biological Tree of Life.
			It is unfinished, and is just here for testing.
		</div>
		<div v-else-if="stage == 1" :style="contentStyles">
			Clicking/touching a tile expands it and shows it's children.
		</div>
		<div v-else-if="stage == 2" :style="contentStyles">
			Clicking on an expanded tile's header shrinks it back.
		</div>
		<div v-else-if="stage == 3" :style="contentStyles">
			Clicking and holding on a tile makes it fill the view, and moves it's
				ancestors to a sidebar. The same thing applies for an expanded tile's header.
		</div>
		<div v-else-if="stage == 4" :style="contentStyles">
			Clicking on a tile in the sidebar brings it back into the main view.
		</div>
		<div v-else-if="stage == 5" :style="contentStyles">
			Clicking on the icon at a tile's bottom-right, or at the right of
				an expanded tile's header, brings up more information.
		</div>
		<div v-else-if="stage == 6" :style="contentStyles">
			You can search using the icon at the top-right. Alternatively, press Ctrl-F.
		</div>
		<div v-else-if="stage == 7" :style="contentStyles">
			You can use the play icon to enable 'Auto Mode'.
		</div>
		<div v-else-if="stage == 8" :style="contentStyles">
			The settings icon allows adjusting the layout, animation speed, etc.
		</div>
		<div v-else-if="stage == 9" :style="contentStyles">
			And finally, the help icon provides more information.
		</div>
	</transition>
	<!-- Buttons -->
	<div class="w-full flex justify-evenly mt-2">
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
			hidNextPrevOnce: false, // Used to hide prev/next buttons when initially at stage 1
			stageActions: [
				// Specifies, for stages 1+, what action to enable (can repeat an action to enable nothing new)
				'expand', 'collapse', 'expandToView', 'unhideAncestor',
				'tileInfo', 'search', 'autoMode', 'settings', 'help',
			] as Action[],
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
				maxWidth: '15cm',
				margin: '0 auto',
				overflow: 'auto',
			};
		 },
		 buttonStyles(): Record<string,string> {
			return {
				color: this.uiOpts.textColor,
				backgroundColor: this.uiOpts.bgColor,
			};
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
