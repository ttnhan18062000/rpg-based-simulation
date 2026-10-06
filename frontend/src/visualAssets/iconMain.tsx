// Entry of the dev-only page frontend/rehearsal-icons.html (Vite builds only index.html, so this is never in the production build).
import { createRoot } from 'react-dom/client'
import { IconHarness } from './IconHarness'
import { iconDraftManifestText, iconDraftUrlFor, iconRuleResultText } from './iconDraftSource'

createRoot(document.getElementById('root')!).render(<IconHarness manifestText={iconDraftManifestText} ruleResultText={iconRuleResultText} urlFor={iconDraftUrlFor} />)
