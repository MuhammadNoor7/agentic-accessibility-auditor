import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    // ngrok's free-plan subdomain is random per tunnel, so we can't pin one hostname here.
    allowedHosts: true,
    proxy: {
      '/api': { target: 'http://backend:8000', changeOrigin: true },
      '/auth': { target: 'http://backend:8000', changeOrigin: true },
      '/records': { target: 'http://backend:8000', changeOrigin: true },
    },
  },
})
