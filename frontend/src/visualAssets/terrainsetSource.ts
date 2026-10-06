// The committed whole-set export (a test-time copy of `export-runtime --catalog-id pilot --release-id rc-0005`, see docs/assets/pilot_terrain_key.md) as the build sees it.
// Only the terrain-set rehearsal page and tests import this.
import manifestText from './__fixtures__/terrainset/runtime_manifest.json?raw'

const urlModules = import.meta.glob('./__fixtures__/terrainset/*.png', { eager: true, query: '?url', import: 'default' }) as Record<string, string>

export const terrainsetManifestText: string = manifestText

export const terrainsetUrls: Readonly<Record<string, string>> = Object.freeze(
  Object.fromEntries(Object.entries(urlModules).map(([path, url]) => [path.slice(path.lastIndexOf('/') + 1), url])),
)

export const terrainsetUrlFor = (file: string): string | undefined => terrainsetUrls[file]
