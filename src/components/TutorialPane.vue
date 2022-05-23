<script lang="ts">
import {defineComponent, PropType} from 'vue';
import CloseIcon from './icon/CloseIcon.vue';
import {EnabledFeatures} from '../lib';

export default defineComponent({
	props: {
		skipWelcome: {type: Boolean, default: false},
		pos: {type: Array as unknown as PropType<[number,number]>, required: true},
		dims: {type: Array as unknown as PropType<[number,number]>, required: true},
		uiOpts: {type: Object, required: true},
		triggerFlag: {type: Boolean, required: true},
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
				position: 'absolute',
				left: this.pos[0] + 'px',
				top: this.pos[1] + 'px',
				width: this.dims[0] + 'px',
				height: this.dims[1] + 'px',
				backgroundColor: this.uiOpts.tutorialPaneBgColor,
				color: this.uiOpts.tutorialPaneTextColor,
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
		 buttonStyles(): Record<string,string> {
			return {
				display: 'block',
				padding: '8px 16px',
				borderRadius: '5px',
				backgroundColor: '#292524',
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
			this.$emit('tutorial-stage-chg', {enabledFeatures: new EnabledFeatures(), tutTriggerFeature: null});
			this.$emit('tutorial-close');
		},
		sendEnabledFeatures(){
			let ef = new EnabledFeatures();
			switch (this.stage){
				case  1:
				case  2: ef.collapse = false;
				case  3: ef.expandToView = false;
				case  4: ef.unhideAncestor = false;
				case  5: ef.infoIcon = false;
				case  6: ef.search = false;
				case  7: ef.autoMode = false;
				case  8: ef.settings = false;
				case  9: ef.help = false;
				case 10:
			}
			let tf = null;
			switch (this.stage){
				case  1:
				case  2: tf = 'expand'; break;
				case  3: tf = 'collapse'; break;
				case  4: tf = 'expandToView'; break;
				case  5: tf = 'unhideAncestor'; break;
				case  6: tf = 'infoIcon'; break;
				case  7: tf = 'search'; break;
				case  8: tf = 'autoMode'; break;
				case  9: tf = 'settings'; break;
				case 10: tf = 'help'; break;
			}
			this.$emit('tutorial-stage-chg', {enabledFeatures: ef, tutTriggerFeature: tf});
		},
	},
	created(){
		if (this.skipWelcome){
			this.sendEnabledFeatures();
		}
	},
	components: {CloseIcon, },
	emits: ['tutorial-close', 'tutorial-stage-chg', ],
});
</script>

<template>
<div :style="styles" class="flex flex-col justify-evenly">
	<close-icon @click.stop="onClose"
		class="block absolute top-2 right-2 w-6 h-6 hover:cursor-pointer"/>
	<template v-if="stage == 0">
		<h2 class="text-center">Welcome</h2>
		<div :style="contentStyles">
			Lorem ipsum dolor sit amet, consectetur adipiscing
			elit, sed do eiusmod tempor incididunt ut labore
			et dolore magna aliqua. Ut enim ad minim veniam,
			quis nostrud exercitation ullamco.
		</div>
		<div class="w-full flex justify-evenly">
			<button :style="buttonStyles" class="hover:brightness-125" @click="onStartTutorial">
				Start Tutorial
			</button>
			<button :style="buttonStyles" class="hover:brightness-125" @click="onClose">
				Close
			</button>
		</div>
	</template>
	<template v-else>
		<h2 class="text-center">Tutorial</h2>
		<!-- Text content -->
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
		<div class="w-full flex justify-evenly">
			<button :style="buttonStyles"
				:disabled="stage == 1" :class="stage == 1 ? ['brightness-75'] : ['hover:brightness-125']"
				@click="onPrevClick">
				Prev
			</button>
			<button :style="buttonStyles" class="hover:brightness-125"
				@click="(stage != maxStage) ? onNextClick() : onClose()">
				{{stage != maxStage ? 'Next' : 'Finish'}}
			</button>
		</div>
	</template>
</div>
</template>
