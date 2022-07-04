<template>
<div class="fixed left-0 top-0 w-full h-full bg-black/40" @click="onClose">
	<div class="absolute left-1/2 -translate-x-1/2 top-1/2 -translate-y-1/2
		w-4/5 max-w-[16cm] max-h-[80%] overflow-auto" :style="styles">
		<close-icon @click.stop="onClose" ref="closeIcon"
			class="block absolute top-1 right-1 md:top-2 md:right-2 w-8 h-8 hover:cursor-pointer"/>
		<h1 class="text-center text-xl font-bold pt-2 pb-1">Help</h1>
		<div class="flex flex-col gap-2 p-2">
			<s-collapsible :class="scClasses">
				<template #summary="slotProps">
					<div :class="scSummaryClasses">
						<down-icon :class="slotProps.collapsed ? downIconClasses : downIconExpandedClasses"/>
						What is the Tree of Life?
					</div>
				</template>
				<template #content>
					<div :class="contentClasses">
						<p>
							In theory, the Tree of Life represents all living organisms, along with their parents,
							grandparents, and so on, all the way up to a single common ancestor.
						</p>
						<div class="my-2 w-4/5 mx-auto flex flex-col items-center gap-1 md:flex-row md:gap-2 md:w-fit">
							<img src="data:," width="240" height="180" alt="Simple Tree of Life"
								class="border border-black block mx-auto md:mx-0 md:shrink-0"/>
							<p class="text-sm md:max-w-[4cm]">
								Each dot is a <strong>node</strong>, and represents a <strong>taxon</strong>,
								which might be a species, genus, or otherwise. The top node is the
								<strong>root</strong>, and those without children are <strong>leaves</strong>.
							</p>
						</div>
						<p>
							The metaphor doesn't always fit. For example, many bacteria can transfer
							DNA to each other without creating children. But the concept is still helpful for
							visualisation.
						</p>
						<br/>
						<p>
							Determining the structure of the tree is an ongoing area
							of work, but much of it has been traced out using genetic information,
							statistical analysis, and human inference.
						</p>
					</div>
				</template>
			</s-collapsible>
			<s-collapsible :class="scClasses">
				<template #summary="slotProps">
					<div :class="scSummaryClasses">
						<down-icon :class="slotProps.collapsed ? downIconClasses : downIconExpandedClasses"/>
						Visualising the Tree
					</div>
				</template>
				<template #content>
					<div :class="contentClasses">
						<p>
							Tilo attempts to display the Tree of Life by representing nodes with tiles,
							and placing tiles within other tiles to show tree structure.
						</p>
						<img src="data:," width="400" height="200" alt="Tree with Tile layout"
							class="border border-black block mx-auto mt-2"/>
						<br/>
						<p>
							Within a tile's header:
							<ul class="list-disc pl-4">
								<li>
									The color denotes the number of children.
									White means zero,
									<span style="color: limegreen">green</span> means 1+,
									<span style="color: darkorange">orange</span> means 10+,
									and <span style="color: crimson">red</span> means 100+.
								</li>
								<li>
									An asterisk indicates that the node's placement lack evidence, or is disputed.
									<span class="text-xs md:text-sm text-stone-500">
										(In the Open Tree of Life, each node has zero or more associated hypothetical
										trees that either support or conflict with it. The asterisk is added if
										there are no supporting trees, or if there is a single conflicting tree.)
									</span>
								</li>
							</ul>
						</p>
						<br/>
						<p>
							There are many other methods of visualisation, which can enable viewing
							many more nodes as text, or for exploring a more natural tree-like diagram.
							Examples include
							<a href="https://itol.embl.de/">iTOL</a>
								<external-link-icon :class="linkIconClasses"/>
							and <a href="https://www.onezoom.org/">OneZoom</a>
								<external-link-icon :class="linkIconClasses"/>.
							<div class="flex gap-2 justify-evenly mt-1 md:mt-2">
								<img src="data:," width="200" height="200" alt="iTOL"
									class="border border-black block"/>
								<img src="data:," width="200" height="200" alt="OneZoom"
									class="border border-black block"/>
							</div>
						</p>
					</div>
				</template>
			</s-collapsible>
			<s-collapsible :class="scClasses">
				<template #summary="slotProps">
					<div :class="scSummaryClasses">
						<down-icon :class="slotProps.collapsed ? downIconClasses : downIconExpandedClasses"/>
						Using Tilo
					</div>
				</template>
				<template #content>
					<div :class="contentClasses">
						<p>
							This section provides some details not included in the tutorial.
						</p>
						<br/>
						<h1 class="text-lg font-bold">Settings</h1>
						<ul class="list-disc pl-4">
							<li>
								<h2 class="font-bold">Sweep leaves left</h2>
								<p>
									If disabled, an expanded tile's children are simply laid out in order.
									This can leave a lot of empty space when large children are next to small ones.
									Moving the unexpanded children (the 'leaves') to the left helps avoid this.
									<img src="data:," width="400" height="200" alt="Sweep leaves setting effect"
										class="border border-black block mx-auto my-1"/>
								</p>
							</li>
							<li>
								<h2 class="font-bold">Sweep into parent</h2>
								<p>
									If enabled, leaves being swept left can be moved beyond the tile's
									rectangle, into leftover space in the parent.
									<img src="data:," width="400" height="200" alt="Sweep into parent setting effect"
										class="border border-black block mx-auto my-1"/>
								</p>
							</li>
							<li>
								<h2 class="font-bold">Trees to use</h2>
								<p>
									Three choices are available, and all are simplified versions of
									the tree from the Open Tree of Life.
									<span class="text-xs md:text-sm text-stone-500">
										(Without this, some nodes would have over 10,000 children, and
										significantly slow the browser down during rendering)
									</span>
								</p>
								<ul class="list-[circle] pl-4">
									<li>
										<span class="font-bold">Complex:</span>
										The least simplified choice. In short, it only includes
										nodes that have an image or description, with a soft limit of 600 children.
										<span class="text-xs md:text-sm text-stone-500">
											(Has about 450,000 nodes)
										</span>
									</li>
									<li>
										<span class="font-bold">Visual:</span>
										Only keeps nodes with images, with a soft limit of 300 children.
										<span class="text-xs md:text-sm text-stone-500">
											(Has about 140,000 nodes)
										</span>
									</li>
									<li>
										<span class="font-bold">Minimal:</span>
										Created using a rough list of 'well known'
										taxons, and adding a few more at random.
										<span class="text-xs md:text-sm text-stone-500">
											(Has about 3,300 nodes)
										</span>
									</li>
								</ul>
							</li>
							<li>
								<h2 class="font-bold">Slider Resets</h2>
								<p>
									You can {{touchDevice ? 'tap' : 'click'}} on
									a slider's label to reset it to the default value.
								</p>
							</li>
						</ul>
						<br/>
						<h1 class="text-lg font-bold">Keyboard Shortcuts</h1>
						<ul class="list-disc pl-4">
							<li>Ctrl-F opens the search bar</li>
							<li>Ctrl-Shift-F toggles the search animation</li>
							<li>Esc closes an open pane, and cancels an active search or auto mode</li>
						</ul>
						<br/>
						<h1 class="text-lg font-bold">Unusual Node Names</h1>
						<ul class="list-disc pl-4">
							<li>
								<h2 class="font-bold">Disambiguation Nodes</h2>
								<p>
									These have names like 'Iris [2]'. When multiple nodes have the same
									name, all but one gets an '[N]' appended, where N is 2 or above.
								</p>
							</li>
							<li>
								<h2 class="font-bold">Compound Nodes</h2>
								<p>
									These are only present in the Complex tree, and have names like
									'[Homo Sapiens + Homo Heidelbergensis]'. They provide structure for other nodes,
									and are named after two prominent descendants.
								</p>
							</li>
						</ul>
						<br/>
						<h1 class="text-lg font-bold">Overflowing Tiles</h1>
						<p>
							Some tiles have too many children to fit on-screen at once, and are displayed
							with a scroll bar. For layout reasons, this is only done if they are the
							outermost tile, so you may need to {{touchDevice ? 'double tap' : 'click and hold'}}
							the tile to expand it.
						</p>
					</div>
				</template>
			</s-collapsible>
			<s-collapsible :class="scClasses">
				<template #summary="slotProps">
					<div :class="scSummaryClasses">
						<down-icon :class="slotProps.collapsed ? downIconClasses : downIconExpandedClasses"/>
						Data Sources
					</div>
				</template>
				<template #content>
					<div :class="contentClasses">
						<h1 class="text-lg font-bold">Sources</h1>
						<ul class="list-disc pl-4">
							<li>
								The tree structure was obtained from the Open Tree of Life
								<a href="https://tree.opentreeoflife.org/about/synthesis-release"
									:style="anchorStyles">synthesis release</a>
									<external-link-icon :class="linkIconClasses"/>
								 version 13.4, accessed 23/04/2022.
							</li>
							<li>
								The images and alternative-names data was partly obtained from the
								Encyclopedia of Life. Name data was obtained from
								<a href="https://opendata.eol.org/dataset/vernacular-names" :style="anchorStyles"
									>here</a><external-link-icon :class="linkIconClasses"/>,
								and image metadata from
								<a href="https://opendata.eol.org/dataset/images-list" :style="anchorStyles"
									>here</a><external-link-icon :class="linkIconClasses"/>,
								accessed 24/04/2022.
							</li>
							<li>
								The short descriptions, along with the remaining images and name data,
								were obtained from Wikipedia. Descriptions were extracted from the
								<a href="https://dumps.wikimedia.org/enwiki/" :style="anchorStyles">Wikipedia dump</a>
									<external-link-icon :class="linkIconClasses"/> for 01/05/22,
								and also obtained from the
								<a href="https://databus.dbpedia.org/dbpedia/collections/latest-core"
									:style="anchorStyles">DBpedia knowledge base</a>
									<external-link-icon :class="linkIconClasses"/>
								for 01/03/22. Images were downloaded from Wikipedia during Jun 2022.
							</li>
						</ul>
						<br/>
						<h1 class="text-lg font-bold">Data Inconsistencies</h1>
						<p>
							When handling datasets this large, these are almost unavoidable. Significant effort
							was expended to minimise them, but, inevitably, there are always more. The most prominent
							types are listed below. If you find a major error, feel free to let me know at
							<a href="mailto:terry06890@gmail.com" :style="anchorStyles">terry06890@gmail.com</a>.
						</p>
						<ul class="list-disc pl-4">
							<li>
								<h2 class="font-bold">Errors in Node Linkage</h2>
								<p>
									The datasets don't share the same set of node identifiers. So, in order to
									link nodes from one dataset with another, their plain names were used.
									This doesn't work when names are ambiguous. For example, 'Proboscidea'
									might denote a taxon for elephants, but also plants. Most of these were
									manually corrected, but there are almost certainly more.
								</p>
							</li>
							<li>
								<h2 class="font-bold">Errors Within the Datasets</h2>
								<p>
									Some issues are internal to the datasets themselves. For example, an image from
									EOL might display a plant that is in the wrong taxon. As most of the datasets are
									large projects distributed over many people over a long period of time, these
									errors are difficult to avoid, and may require specialised knowledge to resolve.
								</p>
							</li>
							<li>
								<h2 class="font-bold">Errors in Descriptions</h2>
								<p>
									The short descriptions were extracted using imprecise heuristics.
									There are many cases of leftover wikitext markup, or cut-off sentences.
								</p>
							</li>
						</ul>
						<br/>
						<h1 class="text-lg font-bold">Some Possible Points of Confusion</h1>
						<ul class="list-disc pl-4">
							<li>
								<h2 class="font-bold">Unexpected Images</h2>
								<p>
									Not all the images are well-suited for display. For example, many
									birds have their heads cropped out. And some fish are shown in a
									preserved form that is hard to recognise. And some moths are shown
									alongside a more prominent plant, and are hard to see.
								</p>
							</li>
							<li>
								<h2 class="font-bold">Unexpected Search Results</h2>
								<ul class="list-[circle] pl-4">
									<li>
										In the Complex tree, searching for 'orange', then pressing enter, brings up
										a kind of butterfly, instead of a citrus plant. This is because suggestions
										are not yet ordered by how well known the taxon is.
									</li>
									<li>
										In some cases, a search might unexpectedly have no results. For example,
										searching for 'golden retriever' brings up nothing. This is because
										breeds of domestic dog are not considered separate species, but as
										variant descendants of Canis familiaris.
									</li>
								</ul>
							</li>
						</ul>
					</div>
				</template>
			</s-collapsible>
			<s-collapsible :class="scClasses">
				<template #summary="slotProps">
					<div :class="scSummaryClasses">
						<down-icon :class="slotProps.collapsed ? downIconClasses : downIconExpandedClasses"/>
						Other Credits
					</div>
				</template>
				<template #content>
					<div :class="contentClasses">
						<ul class="list-disc pl-4">
							<li>
								The UI was built using the
								<a href="https://vuejs.org/" :style="anchorStyles">Vue framework</a>
									<external-link-icon :class="linkIconClasses"/>
							</li>
							<li>
								Styling was enhanced using
								<a href="https://tailwindcss.com/" :style="anchorStyles">Tailwind</a>
									<external-link-icon :class="linkIconClasses"/>
							</li>
							<li>
								The font is called
								<a href="https://design.ubuntu.com/font/" :style="anchorStyles">Ubuntu Font</a>
									<external-link-icon :class="linkIconClasses"/>
							</li>
							<li>Icons were obtained from
								<a href="https://feathericons.com/" :style="anchorStyles">Feathericons</a>
									<external-link-icon :class="linkIconClasses"/>
								and <a href="https://ionic.io/ionicons" :style="anchorStyles">Ionicons</a>
									<external-link-icon :class="linkIconClasses"/>
							</li>
							<li>
								Images were cropped using
								<a href="https://github.com/jwagner/smartcrop.js" :style="anchorStyles">Smartcrop</a>
									<external-link-icon :class="linkIconClasses"/>
							</li>
						</ul>
					</div>
				</template>
			</s-collapsible>
		</div>
		<s-button v-if="!tutOpen" class="mx-auto mb-2"
			:style="{color: uiOpts.textColor, backgroundColor: uiOpts.bgColor}" @click.stop="onStartTutorial">
			Start Tutorial
		</s-button>
	</div>
</div>
</template>

<script lang="ts">
import {defineComponent, PropType} from 'vue';
import SButton from './SButton.vue';
import SCollapsible from './SCollapsible.vue';
import CloseIcon from './icon/CloseIcon.vue';
import DownIcon from './icon/DownIcon.vue';
import ExternalLinkIcon from './icon/ExternalLinkIcon.vue';
import {UiOptions} from '../lib';

export default defineComponent({
	props: {
		tutOpen: {type: Boolean, default: false},
		uiOpts: {type: Object as PropType<UiOptions>, required: true},
	},
	computed: {
		styles(): Record<string,string> {
			return {
				backgroundColor: this.uiOpts.bgColorAlt,
				borderRadius: this.uiOpts.borderRadius + 'px',
				boxShadow: this.uiOpts.shadowNormal,
			};
		},
		scClasses(): string {
			return 'border border-stone-400 rounded';
		},
		scSummaryClasses(): string {
			return "relative text-center p-1 bg-stone-300 hover:brightness-90 hover:bg-lime-200 md:p-2";
		},
		downIconClasses(): string {
			return 'block absolute w-6 h-6 my-auto mx-1 transition-transform duration-300';
		},
		downIconExpandedClasses(): string {
			return this.downIconClasses + ' -rotate-90';
		},
		contentClasses(): string {
			return 'p-2 text-sm md:text-base';
		},
		anchorStyles(): Record<string,string> {
			return {
				color: this.uiOpts.altColorDark,
			};
		},
		linkIconClasses(): string {
			return 'inline-block w-3 h-3 ml-1';
		},
		touchDevice(): boolean {
			return this.uiOpts.touchDevice;
		},
	},
	methods: {
		onClose(evt: Event){
			if (evt.target == this.$el || (this.$refs.closeIcon as typeof CloseIcon).$el.contains(evt.target)){
				this.$emit('close');
			}
		},
		onStartTutorial(){
			this.$emit('start-tutorial');
			this.$emit('close');
		},
	},
	components: {SButton, SCollapsible, CloseIcon, DownIcon, ExternalLinkIcon, },
	emits: ['close', 'start-tutorial', ],
});
</script>
