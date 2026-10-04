import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { CELL_SIZE } from '../cell'
import { FAMILY_FALLBACKS, GENERIC_FALLBACK, describeResolution, drawFallback, fallbackFor, glyphMask, type Glyph } from '../fallback'
import { parseManifest } from '../manifest'
import { fixtureManifestText, fixtureUrls } from '../fixtureSource'
import { resolveVisual, type FallbackReason } from '../resolver'
import { RecordingContext, alphaMask, differing } from './helpers'

function luminance(hex: string): number {
  const channels = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255).map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4))
  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]
}
const contrast = (a: string, b: string) => (Math.max(luminance(a), luminance(b)) + 0.05) / (Math.min(luminance(a), luminance(b)) + 0.05)

const GLYPHS: Glyph[] = ['diamond', 'disc', 'frame', 'cross']
const snapshot = parseManifest(fixtureManifestText)

describe('fallbacks keep the role without the image and without hue', () => {
  it('every family of the fixture, and the generic one, has a glyph and a text label', () => {
    for (const family of new Set([...snapshot.entries.values()].map((e) => e.family))) {
      expect(FAMILY_FALLBACKS[family], family).toBeDefined()
    }
    for (const fb of [...Object.values(FAMILY_FALLBACKS), GENERIC_FALLBACK]) {
      expect(fb.letter.length).toBeGreaterThan(0)
      expect(fb.name.length).toBeGreaterThan(0)
    }
    expect(new Set([...Object.values(FAMILY_FALLBACKS), GENERIC_FALLBACK].map((f) => f.letter)).size).toBe(4)
    expect(fallbackFor('no-such-family')).toBe(GENERIC_FALLBACK)
    expect(fallbackFor(null)).toBe(GENERIC_FALLBACK)
  })

  it('the four glyph shapes are pairwise clearly different masks (shape, not colour)', () => {
    for (let i = 0; i < GLYPHS.length; i++) {
      expect(glyphMask(GLYPHS[i])).toHaveLength(CELL_SIZE * CELL_SIZE)
      for (let j = i + 1; j < GLYPHS.length; j++) expect(differing(glyphMask(GLYPHS[i]), glyphMask(GLYPHS[j])), `${GLYPHS[i]}/${GLYPHS[j]}`).toBeGreaterThanOrEqual(20)
    }
  })

  it('every family fallback paints in the same two colours, so the shape and the letter carry the difference', () => {
    const palettes = [...Object.keys(FAMILY_FALLBACKS), null].map((family) => {
      const ctx = new RecordingContext()
      drawFallback(ctx, { kind: 'fallback', visualKey: 'k', family, reason: 'missing_image' }, 0, 0)
      return [...ctx.fillStyles].sort().join('|')
    })
    expect(new Set(palettes).size).toBe(1)
  })

  it('draws the glyph with rectangles and the role letter with fillText inside the cell', () => {
    const ctx = new RecordingContext()
    drawFallback(ctx, { kind: 'fallback', visualKey: 'k', family: 'terrain', reason: 'decode_failed' }, 32, 48)
    expect(ctx.of('fillText')).toEqual([['fillText', 'T', 32 + CELL_SIZE / 2, 48 + CELL_SIZE / 2 + 1]])
    for (const [, x, y, w, h] of ctx.of('fillRect') as unknown as [string, number, number, number, number][]) {
      expect(x).toBeGreaterThanOrEqual(32)
      expect(y).toBeGreaterThanOrEqual(48)
      expect(x + w).toBeLessThanOrEqual(32 + CELL_SIZE)
      expect(y + h).toBeLessThanOrEqual(48 + CELL_SIZE)
    }
  })

  it('the role letter always has at least 3:1 contrast with what is under it (the hollow frame gets a light letter)', () => {
    for (const family of [...Object.keys(FAMILY_FALLBACKS), null]) {
      const ctx = new RecordingContext()
      drawFallback(ctx, { kind: 'fallback', visualKey: 'k', family, reason: 'missing_image' }, 0, 0)
      const [backdrop, glyph] = [ctx.rectColors[0], ctx.rectColors[1]]
      const centreOn = glyphMask(fallbackFor(family).glyph)[Math.floor(CELL_SIZE / 2) * CELL_SIZE + Math.floor(CELL_SIZE / 2)]
      expect(ctx.textColors).toHaveLength(1)
      expect(contrast(ctx.textColors[0], centreOn ? glyph : backdrop), String(family)).toBeGreaterThanOrEqual(3)
    }
  })

  it('every fallback reason has a text alternative that names the role and the reason', () => {
    const reasons: FallbackReason[] = ['unknown_key', 'missing_image', 'decode_failed', 'manifest_invalid', 'late_result_dropped']
    const texts = reasons.map((reason) => describeResolution({ kind: 'fallback', visualKey: 'fixture.rehearsal.gem', family: 'item', reason }))
    for (const text of texts) expect(text.name).toContain('item')
    expect(new Set(texts.map((t) => t.detail)).size).toBe(reasons.length)
    expect(describeResolution(resolveVisual(snapshot, 'fixture.rehearsal.gem', { urlFor: (f) => fixtureUrls[f] })).detail).toContain('16x16')
  })
})

describe('the three fixture images', () => {
  it('differ in their alpha masks, not only in colour', () => {
    const masks = [...snapshot.entries.values()].map((entry) => {
      const decoded = alphaMask(readFileSync(path.resolve(process.cwd(), 'src/visualAssets/__fixtures__/rehearsal', entry.file)))
      expect([decoded.width, decoded.height]).toEqual([16, 16])
      return decoded.mask
    })
    for (let i = 0; i < masks.length; i++) {
      for (let j = i + 1; j < masks.length; j++) expect(differing(masks[i], masks[j])).toBeGreaterThanOrEqual(20)
    }
  })
})
