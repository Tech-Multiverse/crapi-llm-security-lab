import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Proxy to crAPI services for local development. In production the Nginx
// container handles the same routing so the browser sees a single origin.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/chatbot': {
        target: 'http://127.0.0.1:5002',
        changeOrigin: true,
      },
      '/gateway': {
        target: 'http://127.0.0.1:8088',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/gateway/, ''),
      },
      '/identity': {
        target: 'http://127.0.0.1:8888',
        changeOrigin: true,
      },
      '/community': {
        target: 'http://127.0.0.1:8888',
        changeOrigin: true,
      },
      '/workshop': {
        target: 'http://127.0.0.1:8888',
        changeOrigin: true,
      },
    },
  },
})
