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
	<div id="grid">
		<img v-for="tile in tiles" :src="'/src/assets/' + tile.name + '.jpg'" :alt="tile.name" :id="tile.name"
			@click="$event.target.style.transform = 'translate(20%,30%)'"/>
	</div>
</template>

<style>
#app {
	background-color: black;
}
#grid {
	display: flex;
	flex-flow: row wrap;
	justify-content: center;
}
img {
	margin: 5px;
	flex: auto;
	transition: transform 1s;
	max-width: 100%;
}
</style>
