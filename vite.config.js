import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
	plugins: [vue()],
	server: {
		proxy: {
			'/tolnode': 'http://localhost:8000',
		}
	},
	//server: {open: true} //open browser when dev server starts
})
