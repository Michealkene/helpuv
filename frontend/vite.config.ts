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
    port: 5173,
    host: '0.0.0.0', // Required for Docker
    strictPort: true,
    allowedHosts: [
      'helpuvio.com',
      'www.helpuvio.com',
      'api.helpuvio.com',
      'localhost',
      '185.113.249.211',
      '.helpuvio.com', // Allow all subdomains
    ],
    // HMR settings for Docker/reverse proxy with HTTPS
    hmr: {
      clientPort: 443,
      protocol: 'wss',
    },
    // Proxy API requests to backend container
    proxy: {
      '/api': {
        target: 'http://helpuvio-backend:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})
