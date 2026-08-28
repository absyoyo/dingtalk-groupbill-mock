import { resolve } from 'node:path'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  build: {
    outDir: '../server/static',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        index: resolve(__dirname, 'index.html'),
        cashier: resolve(__dirname, 'cashier.html'),
      },
    },
  },
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:18722',
      '/debug': 'http://127.0.0.1:18722',
      '/ws': {
        target: 'ws://127.0.0.1:18722',
        ws: true,
      },
    },
  },
})
