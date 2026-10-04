// The committed pilot export (a test-time copy of `export-runtime --catalog-id pilot --release-id rc-0001`, see docs/assets/pilot_terrain_key.md)
// as the build sees it. Only the pilot rehearsal page and tests import this.
import manifestText from './__fixtures__/pilot/runtime_manifest.json?raw'

const urlModules = import.meta.glob('./__fixtures__/pilot/*.png', { eager: true, query: '?url', import: 'default' }) as Record<string, string>

export const pilotManifestText: string = manifestText

export const pilotUrls: Readonly<Record<string, string>> = Object.freeze(
  Object.fromEntries(Object.entries(urlModules).map(([path, url]) => [path.slice(path.lastIndexOf('/') + 1), url])),
)

export const pilotUrlFor = (file: string): string | undefined => pilotUrls[file]
