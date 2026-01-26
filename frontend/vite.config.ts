import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },

  server: {
    host: '0.0.0.0', // REQUIRED for Docker
    port: 5173,
    strictPort: true,
    
    // Allow all hosts (required for reverse proxy)
    allowedHosts: [
      'helpuvio.com',
      'www.helpuvio.com',
      'api.helpuvio.com',
      'localhost',
      '185.113.249.211',
      '.helpuvio.com', // Allow all subdomains
    ],

    // Disable host check for Docker/reverse proxy
    hmr: {
      clientPort: 5173,
      host: 'localhost',
    },

    // Remove proxy - we're using Traefik for routing now
    // The frontend will call the API via Traefik
    // proxy: {
    //   '/api': {
    //     target: 'http://helpuvio-backend:8000',
    //     changeOrigin: true,
    //     secure: false,
    //   },
    // },
  },

  preview: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
  },
})