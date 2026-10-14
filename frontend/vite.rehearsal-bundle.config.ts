import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// LOCAL ONLY (`make visual-assets-bundle-capture`, never CI): builds the dev-only rehearsal harness pages as a real bundle (hashed asset URLs) so the
// capture can run against `vite preview` instead of the dev server. A separate config: `vite.config.ts` and the app build are not touched.
//
// `assetsInlineLimit: 0` is deliberate: Vite inlines assets under 4 KiB as data: URLs, and the 16 px fixture PNGs are far smaller than that, so by default
// there would be no hashed image URL to check. This forces every fixture PNG to be emitted as `/assets/<name>-<hash>.png`.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { '@': path.resolve(__dirname, './src') } },
  build: {
    outDir: 'e2e-artifacts/rehearsal-bundle',
    emptyOutDir: true,
    assetsInlineLimit: 0,
    rollupOptions: {
      input: {
        rehearsal: path.resolve(__dirname, 'rehearsal.html'),
        'rehearsal-pilot': path.resolve(__dirname, 'rehearsal-pilot.html'),
        'rehearsal-map': path.resolve(__dirname, 'rehearsal-map.html'),
        'rehearsal-icons': path.resolve(__dirname, 'rehearsal-icons.html'),
        'rehearsal-draft': path.resolve(__dirname, 'rehearsal-draft.html'),
      },
    },
  },
})
