<script>
import tol from './tol.json';
export default {
	data() {
		return {
			tol: tol,
			tiles: tol.map(e => ({name: e.name}))
		}
	}
}
</script>

<template>
	<div class="bg-black flex flex-row flex-wrap justify-center">
		<img v-for="tile in tiles" :src="'/src/assets/' + tile.name + '.jpg'" :alt="tile.name" :id="tile.name"
			@click="$event.target.style.transform = 'translate(20%,30%)'"
			class="m-1 flex-auto transition-transform duration-300"/>
	</div>
</template>

<style>
</style>
