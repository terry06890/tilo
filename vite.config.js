import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
	plugins: [vue()],
	server: {
		proxy: {
			'/data': 'http://localhost:8000',
		},
		watch: {
			ignored: ['**/imgsForReview/*', '**/imgsReviewed/*', '**/img/*']
		},
	},
	//server: {open: true} //open browser when dev server starts
})
