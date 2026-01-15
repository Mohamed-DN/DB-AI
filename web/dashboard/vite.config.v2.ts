import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// =============================================================================
// NEXI AI CMDB V2 - Vite Configuration (Shadow Mode)
// =============================================================================
// Frontend: Port 4002 (invece di 3002)
// Backend:  Port 9000 (invece di 8000)
// =============================================================================

export default defineConfig({
    envDir: '../../',
    plugins: [react(), tailwindcss()],
    server: {
        port: 4002, // V2 Frontend Port (V1 = 3002)
        proxy: {
            '/api': {
                target: 'http://localhost:9000', // V2 Backend Port (V1 = 8000)
                changeOrigin: true,
            }
        }
    }
})
