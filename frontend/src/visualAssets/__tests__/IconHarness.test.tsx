import { act, fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { IconHarness } from '../IconHarness'
import { iconDraftManifestText, iconDraftUrlFor, iconRuleResultText } from '../iconDraftSource'
import { ICON_KEYS, MARKER_LAYERS, SCENE_MARKERS, TIERS } from '../iconScene'

let dprValue = 1
const listeners: Array<() => void> = []
beforeEach(() => {
  dprValue = 1
  listeners.length = 0
  Object.defineProperty(window, 'devicePixelRatio', { configurable: true, get: () => dprValue })
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    media: query, matches: true, addEventListener: (_: string, cb: () => void) => listeners.push(cb), removeEventListener: () => undefined,
  })) as unknown as typeof window.matchMedia
})
// React reports each warning once per run, so the guard is file-wide: whichever test mounts first would see a bad DOM nesting (a whitespace node in a table row once did).
let consoleProblems: ReturnType<typeof vi.spyOn>[] = []
beforeEach(() => {
  consoleProblems = [vi.spyOn(console, 'error').mockImplementation(() => undefined), vi.spyOn(console, 'warn').mockImplementation(() => undefined)]
})
afterEach(() => {
  const calls = consoleProblems.flatMap((spy) => spy.mock.calls)
  vi.restoreAllMocks()
  expect(calls).toEqual([])
})

const mount = () => render(<IconHarness manifestText={iconDraftManifestText} ruleResultText={iconRuleResultText} urlFor={iconDraftUrlFor} />)

describe('the icon preview page', () => {
  it('opens the committed draft set and says it is a draft', () => {
    mount()
    expect(screen.getByText(/icon key set preview/i)).toBeInTheDocument()
    expect(screen.getByText('icons-key-v1')).toBeInTheDocument()
    expect(screen.getByText(/nothing here is adopted/i)).toBeInTheDocument()
    expect(screen.getByText(/sha256:[0-9a-f]{64}/)).toBeInTheDocument()
  })

  it('shows every key of the set on the contact sheet with its fallback, at 1x and 2x on a dark and a light panel', () => {
    mount()
    const sheet = screen.getByRole('heading', { name: /contact sheet/i }).closest('section')!
    for (const key of ICON_KEYS) {
      const row = within(sheet).getByText(key, { selector: 'code' }).closest('tr')!
      const images = row.querySelectorAll('img')
      expect(images, key).toHaveLength(4)
      expect([...images].map((i) => i.getAttribute('data-scale'))).toEqual(['1', '2', '1', '2'])
      expect(row.textContent).toMatch(/identifying|decorative/)
    }
  })

  it('draws every image on a whole device-pixel scale (CSS size x devicePixelRatio is a whole multiple of the native size)', () => {
    dprValue = 1.25
    const { container } = mount()
    const images = [...container.querySelectorAll('img[data-key]')] as HTMLImageElement[]
    expect(images.length).toBeGreaterThan(60)
    for (const img of images) {
      const key = img.dataset.key!
      const native = key.startsWith('icon.tier.') ? 8 : key.includes('building') || key.includes('class') ? 24 : 16
      expect(Math.abs(parseFloat(img.getAttribute('width')!) * 1.25 - Number(img.dataset.scale) * native), key).toBeLessThan(1e-6)
      expect(img.style.imageRendering).toBe('pixelated')
    }
  })

  it('composites each marker plate first, then the glyph, over the dark and the bright tile and in the scene', () => {
    const { container } = mount()
    const markers = [...container.querySelectorAll('[data-marker="plate-then-glyph"]')]
    expect(markers).toHaveLength(2 + SCENE_MARKERS.length)
    for (const marker of markers) expect([...marker.querySelectorAll('img')].map((i) => i.dataset.key)).toEqual([...MARKER_LAYERS])
    for (const id of ['rim-terrain.floor', 'rim-terrain.snow']) expect(screen.getByTestId(id).querySelector('[data-marker]')).not.toBeNull()
  })

  it('changing the scale redraws tiles and scene and the note states device pixels', () => {
    const { container } = mount()
    expect(screen.getByTestId('dpr-note').textContent).toMatch(/2 device pixels/)
    fireEvent.change(screen.getByLabelText(/device pixels per art pixel/i), { target: { value: '3' } })
    expect(screen.getByTestId('dpr-note').textContent).toMatch(/3 device pixels/)
    const tile = screen.getByTestId('scene').querySelector('img[data-key^="terrain."]') as HTMLImageElement
    expect(tile.dataset.scale).toBe('3')
    expect(container.querySelector('[data-marker] img')!.getAttribute('data-scale')).toBe('3')
  })

  it('follows a device pixel ratio change', () => {
    mount()
    expect(screen.getByTestId('dpr-note').textContent).toMatch(/devicePixelRatio 1:/)
    act(() => { dprValue = 2; listeners.forEach((l) => l()) })
    expect(screen.getByTestId('dpr-note').textContent).toMatch(/devicePixelRatio 2:/)
  })

  it('shows the tier ladder and the status frames in colour, greyscale and three visions, labelled as an approximation', () => {
    const { container } = mount()
    expect(screen.getByTestId('approximation-note').textContent).toMatch(/visual approximation only/i)
    expect(screen.getByTestId('approximation-note').textContent).toMatch(/computes no pass or fail/i)
    for (const vision of ['colour', 'grey', 'protan', 'deutan', 'tritan']) {
      const cells = container.querySelectorAll(`td[data-vision="${vision}"]`)
      expect(cells, vision).toHaveLength(2)
      expect(cells[0].querySelectorAll('img')).toHaveLength(TIERS.length)
      expect(cells[1].querySelectorAll('img')).toHaveLength(2)
      const filter = (cells[0] as HTMLElement).style.filter
      expect(filter.replace(/"/g, '')).toBe(vision === 'colour' ? '' : `url(#icon-vision-${vision})`)
    }
    expect(container.querySelectorAll('filter')).toHaveLength(4)
    for (const f of container.querySelectorAll('filter')) expect(f.getAttribute('color-interpolation-filters')).toBe('linearRGB')
  })

  it("prints the recorded result of the Python rule and computes none of its own", () => {
    mount()
    const table = screen.getByTestId('recorded-result')
    const recorded = JSON.parse(iconRuleResultText)
    expect(within(table).getByText(recorded.result)).toBeInTheDocument()
    expect(table.textContent).toContain('I1')
    expect(table.textContent).toContain('closest terrain tile')
    expect(table.textContent).toMatch(/margins 2, 2, 2, 2 px/)
  })

  it('refuses a manifest that is not a draft preview manifest', () => {
    render(<IconHarness manifestText="{}" ruleResultText="{}" urlFor={() => undefined} />)
    expect(screen.getByRole('alert').textContent).toMatch(/refused/)
  })

  it('without a result file the sheets still render and no result section is shown', () => {
    render(<IconHarness manifestText={iconDraftManifestText} ruleResultText="not json" urlFor={iconDraftUrlFor} />)
    expect(screen.queryByTestId('recorded-result')).toBeNull()
    expect(screen.getByRole('heading', { name: /contact sheet/i })).toBeInTheDocument()
  })
})
