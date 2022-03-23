<script lang="ts">
import {defineComponent, PropType} from 'vue';
import {LayoutNode} from '../lib';

export default defineComponent({
	props: {
		layoutNode: {type: Object as PropType<LayoutNode>, required: true},
		tileSz: {type: Number, required: true}, //px (length of tile edge)
	},
	computed: {
		styles(): Record<string,string> {
			return {
				border: '1px black solid',
				width: this.tileSz + 'px',
				height: this.tileSz + 'px',
				minWidth: this.tileSz + 'px',
				minHeight: this.tileSz + 'px',
				backgroundImage: 'url(\'/img/' + this.layoutNode.tolNode.name.replaceAll('\'', '\\\'') + '.png\')',
				backgroundSize: 'cover',
				borderRadius: '5px',
			};
		},
		headerStyles(): Record<string,string> {
			return {
				color: 'greenyellow',
				// For ellipsis
				overflow: 'hidden',
				textOverflow: 'ellipsis',
				whiteSpace: 'nowrap',
			};
		},
	},
});
</script>

<template>
	<div :style="styles">
		<div :style="headerStyles">{{layoutNode.tolNode.name}}</div>
	</div>
</template>
