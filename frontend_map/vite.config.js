import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../static/js/map-react',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        app: 'src/main.jsx',
      },
      output: {
        entryFileNames: 'main.js',
        assetFileNames: 'assets/[name][extname]',
      },
    },
  },
});
