import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
	plugins: [vue()],
	server: {
		watch: {
			ignored: ['**/backend', '**/public']
		},
	},
	//server: {open: true} //open browser when dev server starts
})
