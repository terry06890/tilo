<script lang="ts">
import {defineComponent, PropType} from 'vue';
import CloseIcon from './icon/CloseIcon.vue';

export default defineComponent({
	props: {
		pos: {type: Array as unknown as PropType<[number,number]>, required: true},
		dims: {type: Array as unknown as PropType<[number,number]>, required: true},
		uiOpts: {type: Object, required: true},
	},
	data(){
		return {
			stage: 0,
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
		 tutContentStyles(): Record<string,string> {
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
	methods: {
		onPrevClick(){
			this.stage = Math.max(1, this.stage - 1);
		},
		onNextClick(){
			this.stage = Math.min(this.maxStage, this.stage + 1);
		},
	},
	components: {CloseIcon, },
	emits: ['tutorial-close', ],
});
</script>

<template>
<div :style="styles" class="flex flex-col justify-evenly">
	<template v-if="stage == 0">
		<div :style="tutContentStyles">
			Lorem ipsum dolor sit amet, consectetur adipiscing
			elit, sed do eiusmod tempor incididunt ut labore
			et dolore magna aliqua. Ut enim ad minim veniam,
			quis nostrud exercitation ullamco.
		</div>
		<div class="w-full flex justify-evenly">
			<button :style="buttonStyles" class="hover:brightness-125" @click="stage = 1">
				Start Tutorial
			</button>
			<button :style="buttonStyles" class="hover:brightness-125" @click="$emit('tutorial-close')">
				Continue
			</button>
		</div>
	</template>
	<template v-if="stage > 0">
		<div v-if="stage == 1" :style="tutContentStyles">
			Click/touch on the tile to expand it and see it's children. <br/>
			A green title means the tile has children. Orange and red mean 100+ or 1000+ children.
				If a clicked tile won't fit on screen, expansion fails.
				There is a way around this, which we'll describe later.
		</div>
		<div v-else-if="stage == 2" :style="tutContentStyles">
			You can keep expanding tiles, and they are repositioned to try and save space,
				while still trying to maintain a stable layout, to avoid disorientation.
		</div>
		<div v-else-if="stage == 3" :style="tutContentStyles">
			Click on an expanded tile's header to shrink it, hiding it's children
			You can keep exploring the tree this way, expanding and collapsing tiles as needed,
			to better show the groups you're interested in.
		</div>
		<div v-else-if="stage == 4" :style="tutContentStyles">
			Eventually, you might run out of screen space, and be unable to go deeper.
			Click and hold on a tile to make it fill the view, and move it's
				ancestors to a sidebar. You can do the same thing on an expanded tile's header.
		</div>
		<div v-else-if="stage == 5" :style="tutContentStyles">
			Click on a tile in the sidebar to bring it back into the main view.
			In this way, you can explore as deeply as you want, occasionally jumping back
				upward to explore a different ancestral branch.
		</div>
		<div v-else-if="stage == 6" :style="tutContentStyles">
			Each tile has an info icon on the bottom right. Clicking on this brings up
				information about the corresponding biological taxon. <br/>
			A similar icon appears at the right end of each expanded-tile header.
		</div>
		<div v-else-if="stage == 7" :style="tutContentStyles">
			The search icon allows for finding a particular tile, and bringing it into view.
			To stop the traversal, just click anywhere on screen.
		</div>
		<div v-else-if="stage == 8" :style="tutContentStyles">
			The play icon enables 'auto mode', which continuously expands/collapses
				random tiles, until you click to make it stop.
		</div>
		<div v-else-if="stage == 9" :style="tutContentStyles">
			The settings icon allows for adjusting the layout, among other things.
			<ul class="list-disc">
				<li>The animation speed can be slowed down if you find the tile-repositioning hard to follow.</li>
				<li>The 'reduced tree' setting replaces the original tree with a simplified version.</li>
			</ul>
		</div>
		<div v-else-if="stage == 10" :style="tutContentStyles">
			And finally, the help icon provides summarised usage information.
		</div>
		<div class="w-full flex justify-evenly">
			<button :style="buttonStyles"
				:disabled="stage < 2" :class="stage < 2 ? ['brightness-75'] : ['hover:brightness-125']"
				@click="onPrevClick">
				Previous
			</button>
			<button :style="buttonStyles"
				:disabled="stage == maxStage" :class="stage == maxStage ? ['brightness-75'] : ['hover:brightness-125']"
				@click="onNextClick">
				Next
			</button>
		</div>
	</template>
</div>
</template>
