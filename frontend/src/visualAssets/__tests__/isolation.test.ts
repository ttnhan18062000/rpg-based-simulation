// @vitest-environment node
// AM5-W08 isolation proof: the rehearsal is invisible to the normal app and to the production build.
import { mkdtempSync, readFileSync, readdirSync, rmSync, statSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'
import { build } from 'vite'
import { describe, expect, it } from 'vitest'
import { CELL_SIZE as APP_CELL_SIZE } from '@/constants/colors'
import { CELL_SIZE } from '../cell'

const FRONTEND = process.cwd() // vitest runs from frontend/ (jsdom has no file: import.meta.url)
const SRC = path.join(FRONTEND, 'src')
const MODULE = path.join(SRC, 'visualAssets')

function files(dir: string, keep: (p: string) => boolean): string[] {
  return readdirSync(dir).flatMap((name) => {
    const full = path.join(dir, name)
    if (name === 'node_modules' || name === 'dist') return []
    return statSync(full).isDirectory() ? files(full, keep) : keep(full) ? [full] : []
  })
}

const SOURCE = (p: string) => /\.(ts|tsx)$/.test(p)
const SPECIFIERS = /(?:from\s+|import\s*\(\s*|import\s+|require\(\s*)['"]([^'"]+)['"]/g
const specifiersOf = (p: string) => [...readFileSync(p, 'utf8').matchAll(SPECIFIERS)].map((m) => m[1])

describe('isolation of the surface rehearsal', () => {
  it('no file of the normal app imports anything from src/visualAssets', () => {
    const outside = files(SRC, SOURCE).filter((p) => !p.startsWith(MODULE + path.sep))
    expect(outside.length).toBeGreaterThan(20) // the scan really sees the app
    const offenders = outside.filter((p) => specifiersOf(p).some((s) => /visualAssets/.test(s)))
    expect(offenders.map((p) => path.relative(FRONTEND, p))).toEqual([])
  })

  it('the production entry, the Vite config and package.json do not mention the rehearsal', () => {
    for (const name of ['index.html', 'vite.config.ts', 'package.json']) {
      const text = readFileSync(path.join(FRONTEND, name), 'utf8')
      expect(text, name).not.toMatch(/visualAssets|rehearsal/i)
    }
    expect(readFileSync(path.join(FRONTEND, 'vite.config.ts'), 'utf8')).not.toContain('rollupOptions') // Vite builds only index.html
  })

  it('the rehearsal module imports nothing from outside src/visualAssets except react', () => {
    const own = files(MODULE, (p) => SOURCE(p) && !p.includes(`${path.sep}__tests__${path.sep}`))
    expect(own.length).toBeGreaterThan(6)
    for (const file of own) {
      for (const spec of specifiersOf(file)) {
        const ok = spec.startsWith('./') || /^react(-dom\/client)?$/.test(spec) || /^react\/jsx-runtime$/.test(spec)
        expect(ok, `${path.relative(FRONTEND, file)} imports ${spec}`).toBe(true)
      }
    }
  })

  it('its cell size is a copy that equals the Live Map\'s own, which it does not import', () => {
    expect(CELL_SIZE).toBe(APP_CELL_SIZE)
  })

  it('the production build output contains no fixture image, no visualAssets module and no rehearsal page', async () => {
    const out = mkdtempSync(path.join(tmpdir(), 'rehearsal-prod-build-'))
    try {
      await build({
        root: FRONTEND, configFile: path.join(FRONTEND, 'vite.config.ts'), mode: 'production', logLevel: 'silent',
        build: { outDir: out, emptyOutDir: true, write: true },
      })
      const built = files(out, () => true)
      expect(built.length).toBeGreaterThan(1) // there is an index.html and its assets
      // every fixture image under __fixtures__/* (the synthetic rehearsal set and the pilot terrain export), not one directory
      const fixtureNames = files(path.join(MODULE, '__fixtures__'), (p) => p.endsWith('.png')).map((p) => path.basename(p))
      expect(fixtureNames).toHaveLength(47) // 3 synthetic + 3 pilot (plain, bush, tree) + 7 draft-set previews + 34 terrain-set (rc-0005: 3 forest slots identical to the pilot's, 22 terrain tiles, 9 border masks): a new fixture image must be added to this count on purpose
      const names = built.map((p) => path.basename(p))
      expect(names.filter((n) => fixtureNames.includes(n) || /rehearsal/i.test(n))).toEqual([])
      expect(built.some((p) => p.endsWith('.png') && fixtureNames.some((n) => p.includes(n.slice(0, 16))))).toBe(false)
      const text = built.filter((p) => /\.(js|css|html)$/.test(p)).map((p) => readFileSync(p, 'utf8')).join('\n')
      // Vite inlines small images as data: URIs, so no .png file or name would show: look for every fixture's own bytes (base64) in the bundle too
      const fixturePaths = files(path.join(MODULE, '__fixtures__'), (p) => p.endsWith('.png'))
      for (const file of fixturePaths) {
        const encoded = readFileSync(file).toString('base64')
        expect(text.includes(encoded.slice(0, 120)), `the production build inlines ${path.basename(file)}`).toBe(false)
      }
      for (const needle of ['visualAssets', 'rehearsal', 'runtime_manifest', 'fallback_contract_version', 'duplicate object key', 'fixture.rehearsal', 'terrain.forest', ...fixtureNames.map((n) => n.slice(0, 16)), 'Visual asset surface', 'Pilot terrain rehearsal', 'Whole-map rehearsal', 'Draft set preview', 'draft_preview_manifest']) {
        expect(text.includes(needle), `the production build contains ${needle}`).toBe(false)
      }
    } finally {
      rmSync(out, { recursive: true, force: true })
    }
  }, 240_000)
})
