// Entry of the dev-only page frontend/rehearsal-pilot.html (Vite builds only index.html, so this is never in the production build).
// `?inject=` shows a failure on screen: `missing` (the image is absent from the build), `corrupt` (undecodable image), `invalid` (a broken manifest).
import { createRoot } from 'react-dom/client'
import { browserDecode } from './browserDecode'
import { pilotManifestText, pilotUrlFor, pilotUrls } from './pilotSource'
import { PilotHarness } from './PilotHarness'

const inject = new URLSearchParams(window.location.search).get('inject')
const file = Object.keys(pilotUrls)[0]
const urlFor = (name: string) => (inject === 'missing' && name === file ? undefined : pilotUrlFor(name))
const decode = inject === 'corrupt'
  ? async (url: string) => (url === pilotUrlFor(file) ? Promise.reject(new Error('corrupt')) : browserDecode(url))
  : browserDecode
const manifestText = inject === 'invalid' ? pilotManifestText.replace('"schema_version":1', '"schema_version":2') : pilotManifestText

createRoot(document.getElementById('root')!).render(<PilotHarness manifestText={manifestText} urlFor={urlFor} decode={decode} />)
