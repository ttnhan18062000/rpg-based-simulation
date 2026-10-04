// Entry of the dev-only page frontend/rehearsal.html (Vite builds only index.html, so this is never in the production build).
// `?inject=` shows a failure on screen: `missing` (an image absent from the build), `corrupt` (undecodable image), `invalid` (a broken manifest).
import { createRoot } from 'react-dom/client'
import { browserDecode } from './browserDecode'
import { fixtureManifestText, fixtureUrlFor, fixtureUrls } from './fixtureSource'
import { RehearsalHarness } from './RehearsalHarness'

const inject = new URLSearchParams(window.location.search).get('inject')
const firstFile = Object.keys(fixtureUrls).sort()[0]
const urlFor = (file: string) => (inject === 'missing' && file === firstFile ? undefined : fixtureUrlFor(file))
const decode = inject === 'corrupt'
  ? async (url: string) => (url === fixtureUrlFor(firstFile) ? Promise.reject(new Error('corrupt')) : browserDecode(url))
  : browserDecode
const manifestText = inject === 'invalid' ? fixtureManifestText.replace('"schema_version":1', '"schema_version":2') : fixtureManifestText

createRoot(document.getElementById('root')!).render(<RehearsalHarness manifestText={manifestText} urlFor={urlFor} decode={decode} />)
