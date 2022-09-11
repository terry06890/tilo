import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
	base: '/',
	plugins: [vue()],
	server: {
		proxy: {'/data': 'http://localhost:8000', '/tol_data': 'http://localhost:8000', },
		watch: {
			ignored: ['**/backend', '**/public']
		},
	},
	build: {
		sourcemap: true,
	},
	//server: {open: true} //open browser when dev server starts
})
