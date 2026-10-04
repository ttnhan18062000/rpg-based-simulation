// The committed fixture draft set (a test-time copy of `draft export fixture-terrain`, see tests/visual_assets/store/draft_fixture.py) as the build sees it.
// Only the draft preview page and tests import this.
import manifestText from './__fixtures__/draft/draft_preview_manifest.json?raw'

const urlModules = import.meta.glob('./__fixtures__/draft/*.png', { eager: true, query: '?url', import: 'default' }) as Record<string, string>

export const draftManifestText: string = manifestText

export const draftUrls: Readonly<Record<string, string>> = Object.freeze(
  Object.fromEntries(Object.entries(urlModules).map(([path, url]) => [path.slice(path.lastIndexOf('/') + 1), url])),
)

export const draftUrlFor = (file: string): string | undefined => draftUrls[file]
