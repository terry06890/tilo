<template>
<div class="fixed left-0 top-0 w-full h-full bg-black/20" @click="onClose" ref="rootRef">
	<!-- Outer div is slightly less dark to make scrollbar more distinguishable -->
	<div class="absolute left-1/2 -translate-x-1/2 top-1/2 -translate-y-1/2
		w-[90%] max-w-[16cm] max-h-[80%] overflow-auto" :style="styles">
		<close-icon @click.stop="onClose" ref="closeRef"
			class="absolute top-1 right-1 md:top-2 md:right-2 w-8 h-8 hover:cursor-pointer"/>

		<h1 class="text-center text-xl sm:text-2xl font-bold pt-2 pb-1">Help</h1>

		<div class="flex flex-col gap-2 p-2">
			<s-collapsible :class="scClasses">
				<template #summary="slotProps">
					<div :class="scSummaryClasses">
						<down-icon :class="slotProps.open ? downIconExpandedClasses : downIconClasses"/>
						What is the Tree of Life?
					</div>
				</template>
				<template #content>
					<div :class="contentClasses">
						<p>
							In theory, the Tree of Life represents all living organisms, along with their parents,
							grandparents, and so on, all the way up to a single common ancestor.
						</p>
						<div class="my-2 flex flex-col items-center gap-1 md:flex-row md:gap-2">
							<img src="/basicTol.svg" alt="Simple Tree of Life"
								class="border border-stone-300 rounded mx-auto md:mx-0 md:shrink-0"/>
							<p class="text-xs md:text-sm text-stone-500 md:text-current">
								Each name labels a <strong>node</strong>, and represents a biological
								<strong>taxon</strong>, such as a species or genus.
								The top node is the <strong>root</strong>, and those at the bottom are
								<strong>leaves</strong>.
							</p>
						</div>
						<p>
							The metaphor doesn't always fit. For example, many bacteria can transfer
							DNA to each other without creating children. But the concept is still helpful for
							visualisation.
						</p>
						<br/>
						<p>
							Determining the structure of the tree is an ongoing area of work,
							but much of it has been traced out using genetic information,
							statistical analysis, and human inference.
						</p>
					</div>
				</template>
			</s-collapsible>

			<s-collapsible :class="scClasses">
				<template #summary="slotProps">
					<div :class="scSummaryClasses">
						<down-icon :class="slotProps.open ? downIconExpandedClasses : downIconClasses"/>
						Using Tilo
					</div>
				</template>
				<template #content>
					<div :class="contentClasses">
						<p class="text-xs md:text-sm text-center text-stone-500 pb-2">
							(More info can be found in the tutorial)
						</p>
						<h1 class="text-lg font-bold">Visualising the Tree</h1>
						<p>
							Tilo displays the Tree of Life by representing nodes with tiles,
							and placing tiles within other tiles to show structure.
						</p>
						<img src="/treeWithTiles.jpg" alt="Tree and tile-layout comparison"
							class="border border-stone-300 mx-auto my-2"/>
						<p>
							Within a tile's header:
							<ul class="list-disc pl-4">
								<li>
									The color denotes the number of child tiles.
									White means zero,
									<span style="color: limegreen">green</span> means 1+,
									<span style="color: darkorange">orange</span> means 10+,
									and <span style="color: crimson">red</span> means 100+.
								</li>
								<li>
									An asterisk indicates uncertain placement.
									<span class="text-xs md:text-sm text-stone-500">
										(In the Open Tree of Life, a node can have supporting or conflicting
										hypothesized trees. The asterisk means no supporting trees,
										or at least one conflicting tree.)
									</span>
								</li>
							</ul>
						</p>
						<br/>
						<div>
							There are many other methods of visualisation.
							Examples include <a href="https://itol.embl.de/" :style="aStyles">iTOL</a>
							and <a href="https://www.onezoom.org/" :style="aStyles">OneZoom</a>
							<div class="flex gap-2 mt-1 md:mt-2">
								<div class="flex flex-col items-center">
									<img src="/itol.jpg" alt="iTOL screenshot"
										class="border border-stone-300"/>
									<div class="text-xs text-center">
										iTOL screenshot taken 05/07/2022
									</div>
								</div>
								<div class="flex flex-col items-center">
									<img src="/onezoom.jpg" alt="OneZoom screenshot"
										class="border border-stone-300"/>
									<div class="text-xs text-center">
										OneZoom screenshot taken 05/07/2022
									</div>
								</div>
							</div>
						</div>
						<br/>
						<h1 class="text-lg font-bold">Settings</h1>
						<ul class="list-disc pl-4">
							<li>
								<h2 class="font-bold">Sweep leaves left</h2>
								<p>
									If disabled, an expanded tile's children are simply laid out left to right,
									top to bottom.
									This can leave a lot of empty space when large children are near small ones.
									Moving the unexpanded children (the 'leaves') to the left helps avoid this.
									<img src="/sweepCmp.jpg" alt="Sweep-leaves on/off comparison"
										class="border border-stone-300 mx-auto my-1"/>
								</p>
							</li>
							<li>
								<h2 class="font-bold">Sweep into parent</h2>
								<p>
									Allows leaves being swept left to be moved beyond the tile's
									rectangle, into empty space in the parent.
									<img src="/sweepPCmp.jpg" alt="Sweep-into-parent on/off comparison"
										class="border border-stone-300 mx-auto my-1"/>
								</p>
							</li>
							<li>
								<h2 class="font-bold">Trees to use</h2>
								<p>
									These are simplified versions of the tree from the Open Tree of Life.
									<span class="text-xs md:text-sm text-stone-500">
										(In the original, some nodes have over 10k children,
										which can be quite slow to render)
									</span>
								</p>
								<ul class="list-[circle] pl-4">
									<li>
										<span class="font-bold">Complex:</span>
										The least simplified. In short, only keeps nodes with an
										image or description, with a soft limit of 600 children.
										<span class="text-xs md:text-sm text-stone-500">
											(Has about 450k nodes)
										</span>
									</li>
									<li>
										<span class="font-bold">Visual:</span>
										Only keeps nodes with images, with a soft limit of 300 children.
										<span class="text-xs md:text-sm text-stone-500">
											(About 140k)
										</span>
									</li>
									<li>
										<span class="font-bold">Minimal:</span>
										Created using a rough list of 'well known' taxons,
										and adding a few more at random.
										<span class="text-xs md:text-sm text-stone-500">
											(About 3k)
										</span>
									</li>
								</ul>
							</li>
							<li>
								<h2 class="font-bold">Auto-hide ancestors</h2>
								<p>
									Normally, if there isn't enough space to expand a tile,
									an ancestor is hidden, and expansion is tried again.
									Disabling this can make tile movements more predictable.
								</p>
							</li>
							<li>
								<h2 class="font-bold">Slider resets</h2>
								<p>
									{{touchDevice ? 'Tapping' : 'Clicking'}} on
									a slider's label resets it to the default value.
								</p>
							</li>
						</ul>
						<br/>
						<h1 class="text-lg font-bold">Keyboard Shortcuts</h1>
						<ul class="list-disc pl-4">
							<li><span class="font-bold">Ctrl-F</span> opens the search bar</li>
							<li><span class="font-bold">Ctrl-Shift-F</span> toggles the search animation</li>
							<li><span class="font-bold">Esc</span> closes an open pane,
								and cancels an active search or auto mode</li>
						</ul>
						<br/>
						<h1 class="text-lg font-bold">Unusual Node Names</h1>
						<ul class="list-disc pl-4">
							<li>
								<h2 class="font-bold">Disambiguation Nodes</h2>
								<p>
									These have names like 'Iris [2]'. When multiple nodes are found to
									have the same name, numbers are added to disambiguate.
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
					</div>
				</template>
			</s-collapsible>

			<s-collapsible :class="scClasses">
				<template #summary="slotProps">
					<div :class="scSummaryClasses">
						<down-icon :class="slotProps.open ? downIconExpandedClasses : downIconClasses"/>
						Licensing and Credits
					</div>
				</template>
				<template #content>
					<div :class="contentClasses">
						<p>
							Tilo's source code is available on
							<a href="https://github.com/terry06890/tilo" :style="aStyles">GitHub</a>, under the
							<a href="https://github.com/terry06890/tilo/blob/main/LICENCE.txt"
								:style="aStyles">MIT Licence</a>.
						</p>
						<br/>
						<h1 class="text-lg font-bold">Data Sources</h1>
						<ul class="list-disc pl-4">
							<li>
								The tree structure was obtained from the
								<a href="https://tree.opentreeoflife.org" :style="aStyles">Open Tree of Life</a>,
								in <a href="https://tree.opentreeoflife.org/about/synthesis-release"
									:style="aStyles">synthesis release</a>
								version 13.4, accessed 23/04/2022. The data is licensed under
								<a href="https://creativecommons.org/publicdomain/zero/1.0/" :style="aStyles">CC0</a>.
							</li>
							<li>
								The images, along with name and node&#8209;mapping data, was partly obtained from the
								<a href="https://eol.org" :style="aStyles">Encyclopedia of Life</a>, using their
								<a href="https://opendata.eol.org/dataset/images-list" :style="aStyles">images list</a>,
								<a href="https://opendata.eol.org/dataset/vernacular-names" :style="aStyles">
									vernacular names</a>, and
								<a href="https://opendata.eol.org/dataset/identifier-map" :style="aStyles">
									identifier map</a> data sets, accessed 22/08/2022.
								<br/>
								For the source of a specific tile's image, look in its info pane.
							</li>
							<li>
								The short descriptions, the remaining images, and other data,
								were obtained from the
								<a href="https://dumps.wikimedia.org/enwiki/" :style="aStyles">Wikimedia dump</a>
								for 01/05/22, the
								<a href="https://databus.dbpedia.org/dbpedia/collections/latest-core"
									:style="aStyles">DBpedia knowledge base</a>
								for 01/03/22, and the
								<a href="https://dumps.wikimedia.org/wikidatawiki/entities/" :style="aStyles">
									Wikidata dump</a> for 23/08/22.
								Wikipedia page content is available under
								<a href="https://creativecommons.org/licenses/by-sa/3.0/" :style="aStyles"
									>CC BY-SA 3.0</a>.
								Images were downloaded during June and August 2022.
							</li>
						</ul>
						<br/>
						<h1 class="text-lg font-bold">Other Credits</h1>
						<ul class="list-disc pl-4">
							<li>
								The UI was mostly coded in
								<a href="https://www.typescriptlang.org/" :style="aStyles">Typescript</a>,
								and built wth <a href="https://vuejs.org/" :style="aStyles">Vue</a>,
								<a href="https://vitejs.dev/" :style="aStyles">Vite</a> &amp;
								<a href="https://pinia.vuejs.org/" :style="aStyles">Pinia</a>
							</li>
							<li>
								Tree data was processed using
								<a href="https://www.python.org/" :style="aStyles">Python</a>,
								and stored using
								<a href="https://www.sqlite.org/index.html" :style="aStyles">Sqlite</a>
							</li>
							<li>
								Styling was enhanced using
								<a href="https://tailwindcss.com/" :style="aStyles">Tailwind</a>
							</li>
							<li>
								The font is <a href="https://design.ubuntu.com/font/" :style="aStyles">Ubuntu Font</a>,
								licensed under
								<a href="https://ubuntu.com/legal/font-licence"
									:style="aStyles">Ubuntu font licence</a>
							</li>
							<li>Icons were used from
								<a href="https://feathericons.com/" :style="aStyles">Feathericons</a>
								and <a href="https://ionic.io/ionicons" :style="aStyles">Ionicons</a>,
								both under MIT License
							</li>
							<li>
								Images were cropped using
								<a href="https://github.com/jwagner/smartcrop.js" :style="aStyles">Smartcrop</a>
							</li>
							<li>
								Thanks to <a href="https://www.onezoom.org/" :style="aStyles">OneZoom</a> for having
								<a href="https://github.com/OneZoom/OZtree/tree/main/OZprivate/ServerScripts/TaxonMappingAndPopularity"
									:style="aStyles">code</a>
								that automates taxon ID mapping
							</li>
							<li>
								Thanks to
								<a href="https://twitter.com/JosephusPaye" :style="aStyles">Josephus Paye II</a>
								for helpful suggestions and clarifications
							</li>
						</ul>
					</div>
				</template>
			</s-collapsible>

			<s-collapsible :class="scClasses">
				<template #summary="slotProps">
					<div :class="scSummaryClasses">
						<down-icon :class="slotProps.open ? downIconExpandedClasses : downIconClasses"/>
						FAQs
					</div>
				</template>
				<template #content>
					<div :class="contentClasses">
						<h1 class="text-lg font-bold">How accurate is the information?</h1>
						<p>
							This is hard to answer precisely. The datasets are from large projects with
							many contributors, trying to track a constantly changing field of knowledge.
							And the process of merging them was inherently imprecise. Significant effort
							has been expended to minimise errors, but, inevitably, there are always more of them.
						</p>
						<br/>
						<p>
							Here's a list of the most common kinds. If you find any major errors,
							feel free to let me know at
							<a href="mailto:terry06890@gmail.com" :style="aStyles">terry06890@gmail.com</a>.
						</p>
						<ul class="list-disc pl-4">
							<li>
								<h2 class="font-bold">Errors in node linkage</h2>
								<p>
									The datasets don't share the same set of node identifiers. So, in order to
									link nodes from one dataset with another, their plain names were used.
									This doesn't work when names are ambiguous. For example, 'Proboscidea'
									might denote a taxon for elephants, but also plants. Most of these were
									manually corrected, but there are almost certainly more.
								</p>
							</li>
							<li>
								<h2 class="font-bold">Errors within the datasets</h2>
								<p>
									Some issues are internal to the datasets themselves. For example, an image from
									EOL might display a plant that is in the wrong taxon. Some of these can be
									quite difficult to recognise, or may require specialised knowledge.
								</p>
							</li>
							<li>
								<h2 class="font-bold">Errors in descriptions</h2>
								<p>
									Many of the short descriptions were extracted using imprecise heuristics.
									There are many cases of leftover wikitext markup, or cut-off sentences.
								</p>
							</li>
						</ul>
						<br/>
						<h1 class="text-lg font-bold">Where are the dogs?</h1>
						<p>
							Generally, the nodes in the tree don't go below the species level.
							And dog breeds aren't considered separate species, but as variant
							descendants of Canis familiaris.
						</p>
						<br/>
						<h1 class="text-lg font-bold">Why is there no tile for the dinosaurs?</h1>
						<p>
							Some names don't correspond to a single node, but to multiple nodes
							from different ancestors. Many dinosaurs are under Sauria, but share
							that parent with non-dinosaurs, such as turtles.
						</p>
						<br/>
						<h1 class="text-lg font-bold">Shouldn't there be more bacteria?</h1>
						<p>
							Many of the bacteria don't have images, and were excluded from the default
							Visual tree.
						</p>
						<br/>
						<h1 class="text-lg font-bold">Why do some grasses share the same description?</h1>
						<p>
							Nodes are largely matched with descriptions using Wikipedia page names.
							And, if two names redirect to a page that provides a generic description,
							they will both get the same description. Unfortunately, this can result in
							two species of grass being described like a third closely-related species.
						</p>
						<br/>
						<h1 class="text-lg font-bold">Why do a lot of fish have their heads clipped out?</h1>
						<p>
							Cropping images into squares was done semi-automatically, and sometimes this
							doesn't work well, especially for animals with long bodies. It's not always
							straightforward to figure out which end is the head, and should be kept in frame.
						</p>
						<br/>
						<h1 class="text-lg font-bold">Why do some snail images just look like documents?</h1>
						<p>
							Not all organisms are easy to get live images of. Some of them only have
							small parts shown, or are in a preserved form, with nearby documentation
							appearing more prominent.
						</p>
						<br/>
						<h1 class="text-lg font-bold">I'm an arachnophobe. How do I avoid spider images?</h1>
						<p>
							Spiders are placed under Araneae, so don't go there. You might want to avoid
							Chelicerata in general, as it contains pseudo-spiders like harvestmen and tickspiders.
							Actually, maybe avoid the arthropods altogether, as they include spider crabs.
							Come to think of it, some of the bird images show them eating spiders, so maybe
							that won't work either ...
						</p>
					</div>
				</template>
			</s-collapsible>
		</div>

		<div class="relative">
			<s-button class="mx-auto mb-2" :style="{color: store.color.text, backgroundColor: store.color.bg}"
				:disabled="tutOpen" @click.stop="onStartTutorial">
				Start Tutorial
			</s-button>
			<p class="absolute text-xs md:text-sm text-stone-500 right-2 bottom-0">
				Last updated 29/01/23
			</p>
		</div>
	</div>
</div>
</template>

<script setup lang="ts">
import {ref, computed} from 'vue';

import SButton from './SButton.vue';
import SCollapsible from './SCollapsible.vue';
import CloseIcon from './icon/CloseIcon.vue';
import DownIcon from './icon/DownIcon.vue';
import {useStore} from '../store';

const rootRef = ref(null as HTMLDivElement | null)
const closeRef = ref(null as typeof CloseIcon | null);

const store = useStore();
const touchDevice = computed(() => store.touchDevice)

defineProps({
	tutOpen: {type: Boolean, default: false},
});

const emit = defineEmits(['close', 'start-tutorial']);

// ========== Event handlers ==========

function onClose(evt: Event){
	if (evt.target == rootRef.value || closeRef.value!.$el.contains(evt.target)){
		emit('close');
	}
}

function onStartTutorial(){
	emit('start-tutorial');
	emit('close');
}

// ========== For styling ==========

const styles = computed(() => ({
	backgroundColor: store.color.bgAlt,
	borderRadius: store.borderRadius + 'px',
	boxShadow: store.shadowNormal,
}));

const aStyles = computed(() => ({
	color: store.color.altDark,
}));

const scClasses = 'border border-stone-400 rounded';
const scSummaryClasses = 'relative text-center p-1 bg-stone-300 hover:brightness-90 hover:bg-lime-200 md:p-2';
const downIconClasses = 'absolute w-6 h-6 my-auto mx-1 transition-transform duration-300';
const downIconExpandedClasses = computed(() => downIconClasses + ' -rotate-90');
const contentClasses = 'py-2 px-2 text-sm md:text-base';
</script>
