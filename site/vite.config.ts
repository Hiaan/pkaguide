import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // chat local: npm run chat:dev (na raiz) com CHAT_MOCK=1 ou ANTHROPIC_API_KEY
  server: { proxy: { '/api': 'http://localhost:8787' } },
})
