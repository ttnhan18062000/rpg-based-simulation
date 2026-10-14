// The committed icon draft export (a test-time copy of `draft export icons-key-v1`, see visual_assets/review/icon_draft_fixture.py) as the build sees it, with the recorded result of the
// Python sheet rule. Only the icon preview page and tests import this.
import manifestText from './__fixtures__/icondraft/draft_preview_manifest.json?raw'
import ruleResultText from './__fixtures__/icondraft/rule_result.json?raw'
import manifestV2Text from './__fixtures__/icondraft_v2/draft_preview_manifest.json?raw'
import ruleResultV2Text from './__fixtures__/icondraft_v2/rule_result.json?raw'
import manifestFixesText from './__fixtures__/icondraft_fixes/draft_preview_manifest.json?raw'
import ruleResultFixesText from './__fixtures__/icondraft_fixes/rule_result.json?raw'
import silhouetteSheetText from './__fixtures__/iconsilhouettes/silhouette_sheet.json?raw'

const urlModules = import.meta.glob(['./__fixtures__/icondraft/*.png', './__fixtures__/icondraft_v2/*.png', './__fixtures__/icondraft_fixes/*.png'], { eager: true, query: '?url', import: 'default' }) as Record<string, string>

export const iconDraftManifestText: string = manifestText
export const iconRuleResultText: string = ruleResultText
// Icon set v2 (`TCK-20261007-VISUAL-ASSETS-ICON-V2-DRAFT-SET`): its own export and recorded rule result, shown beside the adopted key set. The two exports share the adopted terrain files (same hash names).
export const iconDraftV2ManifestText: string = manifestV2Text
export const iconRuleResultV2Text: string = ruleResultV2Text

export const iconDraftUrls: Readonly<Record<string, string>> = Object.freeze(
  Object.fromEntries(Object.entries(urlModules).map(([path, url]) => [path.slice(path.lastIndexOf('/') + 1), url])),
)
export const iconDraftUrlFor = (file: string): string | undefined => iconDraftUrls[file]

// The one-colour silhouette sheet the owner approves before any full drawing (`TCK-20261008-VISUAL-ASSETS-ICON-OWNER-FIXES`): committed by visual_assets/review/icon_silhouette_sheet.py.
export const iconSilhouetteSheetText: string = silhouetteSheetText

// The owner-fix revisions (`TCK-20261008-VISUAL-ASSETS-ICON-OWNER-FIXES`): six new revisions of adopted icons, its own export and recorded results, shown beside the adopted drawings.
export const iconDraftFixesManifestText: string = manifestFixesText
export const iconRuleResultFixesText: string = ruleResultFixesText
