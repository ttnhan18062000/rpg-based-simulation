// Entry of the dev-only page frontend/rehearsal-icons.html (Vite builds only index.html, so this is never in the production build).
import { createRoot } from 'react-dom/client'
import { IconHarness } from './IconHarness'
import { iconDraftManifestText, iconDraftUrlFor, iconDraftFixesManifestText, iconDraftV2ManifestText, iconRuleResultFixesText, iconRuleResultText, iconRuleResultV2Text, iconSilhouetteSheetText } from './iconDraftSource'

createRoot(document.getElementById('root')!).render(<IconHarness manifestText={iconDraftManifestText} ruleResultText={iconRuleResultText} urlFor={iconDraftUrlFor} v2={{ manifestText: iconDraftV2ManifestText, ruleResultText: iconRuleResultV2Text }} silhouettes={{ sheetText: iconSilhouetteSheetText }} fixes={{ manifestText: iconDraftFixesManifestText, ruleResultText: iconRuleResultFixesText }} />)
