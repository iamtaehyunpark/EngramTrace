import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/chat': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/state': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/logs': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/memory': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/day-change': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/kb': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/trace': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      }
    }
  }
})
