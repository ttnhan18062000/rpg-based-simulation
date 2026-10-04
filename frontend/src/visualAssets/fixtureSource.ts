// The committed synthetic fixture (a test-time copy of the store's `export-runtime` output, see docs/assets/store_contract.md) as the
// build sees it: the manifest text and one URL per PNG. Only the rehearsal harness and tests import this.
import manifestText from './__fixtures__/rehearsal/runtime_manifest.json?raw'

const urlModules = import.meta.glob('./__fixtures__/rehearsal/*.png', { eager: true, query: '?url', import: 'default' }) as Record<string, string>

export const fixtureManifestText: string = manifestText

// file name (`<64 hex>.png`) -> the build's URL
export const fixtureUrls: Readonly<Record<string, string>> = Object.freeze(
  Object.fromEntries(Object.entries(urlModules).map(([path, url]) => [path.slice(path.lastIndexOf('/') + 1), url])),
)

export const fixtureUrlFor = (file: string): string | undefined => fixtureUrls[file]
