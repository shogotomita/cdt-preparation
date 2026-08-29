import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// GitHub Pages: set base to '/<repo>/' when deploying under a project path.
// Relative base works for both local preview and most Pages setups.
export default defineConfig({
  base: './',
  plugins: [react(), tailwindcss()],
})
