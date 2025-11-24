import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  resolve: {
    alias: {
      '@/components': '/src/components',
      '@/pages': '/src/pages',
      '@/api': '/src/api',
      '@/store': '/src/store',
      '@/lib': '/src/lib',
      '@/types': '/src/types',
    },
  },
})
