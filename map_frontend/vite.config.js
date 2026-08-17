import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  base: '/map/',
  plugins: [react()],
  server: {
    proxy: {
      '/map/api': 'http://localhost:8011',
      '/media': 'http://localhost:8011',
    },
  },
})
