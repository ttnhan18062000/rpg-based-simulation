// The committed icon draft export (a test-time copy of `draft export icons-key-v1`, see tests/visual_assets/icon_draft_fixture.py) as the build sees it, with the recorded result of the
// Python sheet rule. Only the icon preview page and tests import this.
import manifestText from './__fixtures__/icondraft/draft_preview_manifest.json?raw'
import ruleResultText from './__fixtures__/icondraft/rule_result.json?raw'

const urlModules = import.meta.glob('./__fixtures__/icondraft/*.png', { eager: true, query: '?url', import: 'default' }) as Record<string, string>

export const iconDraftManifestText: string = manifestText
export const iconRuleResultText: string = ruleResultText

export const iconDraftUrls: Readonly<Record<string, string>> = Object.freeze(
  Object.fromEntries(Object.entries(urlModules).map(([path, url]) => [path.slice(path.lastIndexOf('/') + 1), url])),
)
export const iconDraftUrlFor = (file: string): string | undefined => iconDraftUrls[file]
