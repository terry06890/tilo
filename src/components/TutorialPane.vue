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
			stageActions: [ // Specifies, for stages 1+, when actions are introduced (null means none)
				'expand', 'collapse', 'expandToView', 'unhideAncestor',
				'tileInfo', 'search', 'autoMode', 'settings', 'help',
			] as (Action | null)[],
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
			// Update disabled actions
			let disabledActions = this.uiOpts.disabledActions;
			if (this.stage == 0){
				disabledActions.clear();
				return;
			}
			let currentAction = null as null | Action;
			for (let i = 0; i < this.lastStage; i++){
				let action = this.stageActions[i];
				if (action != null){
					if (i < this.stage){
						currentAction = action;
						disabledActions.delete(action);
					} else {
						disabledActions.add(action);
					}
				}
			}
			// Notify of new trigger-action
			this.$emit('stage-chg', currentAction);
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

<template>
<div :style="styles" class="p-2 flex flex-col justify-between">
	<div class="flex">
		<h2 class="text-center mb-2 mx-auto">{{stage == 0 ? 'Welcome' : 'Tutorial'}}</h2>
		<close-icon @click.stop="onClose"
			class="block w-6 h-6 hover:cursor-pointer"/>
	</div>
	<template v-if="stage == 0">
		<div :style="contentStyles">
			This page provides a visualisation of the biological Tree of Life.
			It was made using data from OTOL, EOL, and Wikipedia.
			For more project information, click here.
		</div>
		<div class="w-full flex justify-evenly mt-2">
			<s-button :style="buttonStyles" @click="onStartTutorial">Start Tutorial</s-button>
			<s-button :style="buttonStyles" @click="onSkipTutorial">Skip</s-button>
		</div>
	</template>
	<template v-else>
		<div v-if="stage == 1" :style="contentStyles">
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
		<!-- Buttons -->
		<div class="w-full flex justify-evenly mt-2">
			<s-button :disabled="stage == 1" :style="buttonStyles" @click="onPrevClick">
				Prev
			</s-button>
			<s-button :style="buttonStyles" @click="(stage != lastStage) ? onNextClick() : onClose()">
				{{stage != lastStage ? 'Next' : 'Finish'}}
			</s-button>
		</div>
	</template>
</div>
</template>
