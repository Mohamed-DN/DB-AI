import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// =============================================================================
// NEXI AI CMDB V2 - Vite Configuration
// =============================================================================
// Frontend: Port 4002
// Backend:  Port 9000
// =============================================================================

export default defineConfig({
    envDir: '../../',
    plugins: [react(), tailwindcss()],
    server: {
        port: 4002,
        proxy: {
            '/api': {
                target: 'http://127.0.0.1:8000',
                changeOrigin: true,
            }
        }
    }
})
