// Entry of the dev-only page frontend/rehearsal-draft.html (Vite builds only index.html, so this is never in the production build).
// It opens the committed fixture set; use the page's folder picker to open a set exported with `python -m visual_assets.store draft export <set_id> <out_dir>`.
import { createRoot } from 'react-dom/client'
import { browserDecode } from './browserDecode'
import { draftManifestText, draftUrlFor } from './draftSource'
import { DraftHarness } from './DraftHarness'

createRoot(document.getElementById('root')!).render(<DraftHarness manifestText={draftManifestText} urlFor={draftUrlFor} decode={browserDecode} />)
