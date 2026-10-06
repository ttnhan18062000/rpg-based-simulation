// Entry of the dev-only page frontend/rehearsal-map.html (Vite builds only index.html, so this is never in the production build).
// `?inject=` shows a failure on screen: `missing` (every border mask is absent from the build, so no fringe), `corrupt` (undecodable images), `invalid` (a broken manifest).
import { createRoot } from 'react-dom/client'
import { browserDecode } from './browserDecode'
import { MapHarness } from './MapHarness'
import { terrainsetManifestText, terrainsetUrlFor, terrainsetUrls } from './terrainsetSource'

const inject = new URLSearchParams(window.location.search).get('inject')
const manifest = JSON.parse(terrainsetManifestText) as { entries: { visual_key: string; file: string }[] }
const maskFiles = new Set(manifest.entries.filter((e) => e.visual_key.startsWith('border.')).map((e) => e.file))
const first = Object.keys(terrainsetUrls)[0]
const urlFor = (name: string) => (inject === 'missing' && maskFiles.has(name) ? undefined : terrainsetUrlFor(name))
const decode = inject === 'corrupt'
  ? async (url: string) => (url === terrainsetUrlFor(first) ? Promise.reject(new Error('corrupt')) : browserDecode(url))
  : browserDecode
const manifestText = inject === 'invalid' ? terrainsetManifestText.replace('"schema_version":1', '"schema_version":2') : terrainsetManifestText

createRoot(document.getElementById('root')!).render(<MapHarness manifestText={manifestText} urlFor={urlFor} decode={decode} />)
