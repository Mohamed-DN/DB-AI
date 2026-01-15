import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// =============================================================================
// NEXI AI CMDB V2 - Vite Configuration
// =============================================================================
// Frontend: Port 3002
// Backend:  Port 8000
// =============================================================================

export default defineConfig({
    envDir: '../../',
    plugins: [react(), tailwindcss()],
    server: {
        port: 3002,
        proxy: {
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true,
            }
        }
    }
})
