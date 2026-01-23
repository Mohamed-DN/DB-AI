import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  envDir: '../../',
  plugins: [react(), tailwindcss()],
  server: {
    port: 3002, // React frontend (3000=old, 3001=OpenWebUI)
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:9000',
        changeOrigin: true,
      }
    }
  }
})
