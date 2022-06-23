<script lang="ts">
import {defineComponent, PropType} from 'vue';
import CloseIcon from './icon/CloseIcon.vue';
import RButton from './RButton.vue';
import {Action} from '../lib';

export default defineComponent({
	props: {
		uiOpts: {type: Object, required: true},
		triggerFlag: {type: Boolean, required: true},
		skipWelcome: {type: Boolean, default: false},
		height: {type: String, default: 'auto'},
	},
	data(){
		return {
			stage: this.skipWelcome ? 1 : 0,
			maxStage: 10,
		};
	},
	computed: {
		 styles(): Record<string,string> {
			return {
				backgroundColor: this.uiOpts.tutorialPaneBgColor,
				color: this.uiOpts.tutorialPaneTextColor,
				height: this.height,
			};
		 },
		 contentStyles(): Record<string,string> {
			return {
				padding: '0 0.5cm',
				maxWidth: '15cm',
				margin: '0 auto',
				fontSize: 'small',
				overflow: 'auto',
			};
		 },
	},
	watch: {
		triggerFlag(){
			if (this.stage < this.maxStage){
				this.onNextClick();
			} else {
				this.onClose();
			}
		},
	},
	methods: {
		onStartTutorial(){
			this.stage = 1;
			this.sendEnabledFeatures();
		},
		onPrevClick(){
			this.stage = Math.max(1, this.stage - 1);
			this.sendEnabledFeatures();
		},
		onNextClick(){
			this.stage = Math.min(this.maxStage, this.stage + 1);
			this.sendEnabledFeatures();
		},
		onClose(){
			this.$emit('close');
		},
		sendEnabledFeatures(){
			const stageActions = [
				null,
				'expand', 'expand', 'collapse', 'expandToView', 'unhideAncestor',
				'tileInfo', 'search', 'autoMode', 'settings', 'help'
			] as (Action | null)[];
			let disabledActions = new Set() as Set<Action>;
			for (let i = this.stage + 1; i < this.maxStage; i++){
				disabledActions.add(stageActions[i] as Action);
			}
			disabledActions.delete(stageActions[this.stage] as Action);
			let triggerAction = stageActions[this.stage] as Action;
			this.$emit('stage-chg', disabledActions, triggerAction);
		},
	},
	created(){
		if (this.skipWelcome){
			this.sendEnabledFeatures();
		}
	},
	components: {CloseIcon, RButton, },
	emits: ['close', 'stage-chg', ],
});
</script>

<template>
<div :style="styles" class="p-2 flex flex-col justify-between">
	<div class="flex">
		<h2 class="text-center mb-2">{{stage == 0 ? 'Welcome' : 'Tutorial'}}</h2>
		<close-icon @click.stop="onClose"
			class="block ml-auto w-6 h-6 hover:cursor-pointer"/>
	</div>
	<template v-if="stage == 0">
		<div :style="contentStyles">
			Lorem ipsum dolor sit amet, consectetur adipiscing
			elit, sed do eiusmod tempor incididunt ut labore
			et dolore magna aliqua. Ut enim ad minim veniam,
			quis nostrud exercitation ullamco.
		</div>
		<div class="w-full flex justify-evenly mt-2">
			<r-button class="bg-stone-800 text-white" @click="onStartTutorial">
				Start Tutorial
			</r-button>
			<r-button class="bg-stone-800 text-white" @click="onClose">
				Close
			</r-button>
		</div>
	</template>
	<template v-else>
		<div v-if="stage == 1" :style="contentStyles">
			Click/touch on the tile to expand it and see it's children. <br/>
			A green title means the tile has children. Orange and red mean 100+ or 1000+ children.
				If a clicked tile won't fit on screen, expansion fails.
				There is a way around this, which we'll describe later.
		</div>
		<div v-else-if="stage == 2" :style="contentStyles">
			You can keep expanding tiles, and they are repositioned to try and save space,
				while still trying to maintain a stable layout, to avoid disorientation.
		</div>
		<div v-else-if="stage == 3" :style="contentStyles">
			Click on an expanded tile's header to shrink it, hiding it's children
			You can keep exploring the tree this way, expanding and collapsing tiles as needed,
			to better show the groups you're interested in.
		</div>
		<div v-else-if="stage == 4" :style="contentStyles">
			Eventually, you might run out of screen space, and be unable to go deeper.
			Click and hold on a tile to make it fill the view, and move it's
				ancestors to a sidebar. You can do the same thing on an expanded tile's header.
		</div>
		<div v-else-if="stage == 5" :style="contentStyles">
			Click on a tile in the sidebar to bring it back into the main view.
			In this way, you can explore as deeply as you want, occasionally jumping back
				upward to explore a different ancestral branch.
		</div>
		<div v-else-if="stage == 6" :style="contentStyles">
			Each tile has an info icon on the bottom right. Clicking on this brings up
				information about the corresponding biological taxon. <br/>
			A similar icon appears at the right end of each expanded-tile header.
		</div>
		<div v-else-if="stage == 7" :style="contentStyles">
			The search icon allows for finding a particular tile, and bringing it into view.
			To stop the traversal, just click anywhere on screen.
		</div>
		<div v-else-if="stage == 8" :style="contentStyles">
			The play icon enables 'auto mode', which continuously expands/collapses
				random tiles, until you click to make it stop.
		</div>
		<div v-else-if="stage == 9" :style="contentStyles">
			The settings icon allows for adjusting the layout, among other things.
			<ul class="list-disc">
				<li>The animation speed can be slowed down if you find the tile-repositioning hard to follow.</li>
				<li>The 'reduced tree' setting replaces the original tree with a simplified version.</li>
			</ul>
		</div>
		<div v-else-if="stage == 10" :style="contentStyles">
			And finally, the help icon provides summarised usage information.
		</div>
		<!-- Buttons -->
		<div class="w-full flex justify-evenly mt-2">
			<r-button :disabled="stage == 1" class="bg-stone-800 text-white" @click="onPrevClick">
				Prev
			</r-button>
			<r-button class="bg-stone-800 text-white" @click="(stage != maxStage) ? onNextClick() : onClose()">
				{{stage != maxStage ? 'Next' : 'Finish'}}
			</r-button>
		</div>
	</template>
</div>
</template>
