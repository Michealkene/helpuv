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

    proxy: {
      '/api': {
        // IMPORTANT:
        // - use Docker service name inside containers
        // - use localhost when running without Docker
        target: process.env.DOCKER
          ? 'http://helpuvio:8000'
          : 'http://localhost:8000',

        changeOrigin: true,
        secure: false,
      },
    },
  },

  preview: {
    host: '0.0.0.0',
    port: 5173,
  },
})
