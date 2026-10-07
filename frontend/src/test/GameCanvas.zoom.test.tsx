// D20: the real GameCanvas zoom controls and wheel only reach whole-number device-pixel scales, at several device pixel ratios.
import { act, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { GameCanvas } from '@/components/GameCanvas'
import { CELL_SIZE } from '@/constants/colors'
import { WORLD_MAX_ZOOM, WORLD_MIN_ZOOM, isOverviewZoom, zoomLevels } from '@/lib/pixelScale'

let dprValue = 1
const listeners: Array<() => void> = []

function stubContext(): CanvasRenderingContext2D {
  const target: Record<string | symbol, unknown> = {}
  return new Proxy(target, {
    get: (t, key) => (key in t ? t[key] : key === 'measureText' ? () => ({ width: 0 }) : key === 'createImageData' || key === 'getImageData' ? () => ({ data: new Uint8ClampedArray(4) }) : () => undefined),
    set: (t, key, value) => { t[key] = value; return true },
  }) as unknown as CanvasRenderingContext2D
}

beforeEach(() => {
  dprValue = 1
  listeners.length = 0
  Object.defineProperty(window, 'devicePixelRatio', { configurable: true, get: () => dprValue })
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    media: query, matches: true, addEventListener: (_: string, cb: () => void) => listeners.push(cb), removeEventListener: () => undefined,
  })) as unknown as typeof window.matchMedia
  vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockImplementation(() => stubContext() as never)
})
afterEach(() => { vi.restoreAllMocks() })

const mapData = { width: 8, height: 6, grid: Array.from({ length: 6 }, () => Array.from({ length: 8 }, () => 0)) }

function mount(dpr: number) {
  dprValue = dpr
  return render(<GameCanvas mapData={mapData} entities={[]} selectedEntity={null} groundItems={[]} buildings={[]} resourceNodes={[]} regions={[]} selectedEntityId={null} onEntityClick={() => undefined} />)
}

const scaleOf = (container: HTMLElement): number => {
  const canvas = container.querySelector('canvas') as HTMLCanvasElement
  const match = /scale\(([\d.]+)\)/.exec(canvas.style.transform)
  if (!match) throw new Error(`no scale in ${canvas.style.transform}`)
  return parseFloat(match[1])
}
const press = (title: string) => fireEvent.click(screen.getByTitle(title))

describe.each([1, 1.25, 1.5, 2])('GameCanvas zoom at devicePixelRatio %s', (dpr) => {
  it('starts, steps in, steps out and resets only on whole device-pixel scales', () => {
    const { container } = mount(dpr)
    const reachable = zoomLevels(dpr, WORLD_MIN_ZOOM, WORLD_MAX_ZOOM)
    const seen = new Set<string>()
    const check = () => {
      const z = scaleOf(container)
      expect(reachable.some((l) => Math.abs(l - z) < 1e-9), `zoom ${z} is not a level of ${reachable}`).toBe(true)
      if (isOverviewZoom(z, dpr)) expect(Math.abs(CELL_SIZE * z * dpr - Math.round(CELL_SIZE * z * dpr))).toBeLessThan(1e-9) // the overview level: a whole cell
      else expect(Math.abs(z * dpr - Math.round(z * dpr))).toBeLessThan(1e-9) // an art level: a whole art pixel
      seen.add(z.toFixed(9))
    }
    check()
    for (let i = 0; i < reachable.length + 2; i += 1) { press('Zoom In'); check() }
    expect(scaleOf(container)).toBeCloseTo(reachable[reachable.length - 1], 9) // clamped at the top
    for (let i = 0; i < reachable.length + 2; i += 1) { press('Zoom Out'); check() }
    expect(scaleOf(container)).toBeCloseTo(reachable[0], 9) // clamped at the bottom
    press('Reset Zoom'); check()
    expect(scaleOf(container)).toBeCloseTo(reachable.reduce((a, b) => (Math.abs(b - 1) < Math.abs(a - 1) ? b : a)), 9)
    expect(seen.size).toBe(reachable.length) // every level was reachable by the buttons
  })

  it('the overview level is the bottom one, is reached by stepping down and left by stepping up, and the pan stays on whole device pixels there', () => {
    const { container } = mount(dpr)
    const reachable = zoomLevels(dpr, WORLD_MIN_ZOOM, WORLD_MAX_ZOOM)
    const overview = reachable.filter((l) => isOverviewZoom(l, dpr))
    expect(overview).toEqual(dpr === 2 ? [] : [reachable[0]]) // none at DPR 2, where 0.5 already is an art level
    for (let i = 0; i < reachable.length + 1; i += 1) press('Zoom Out')
    expect(scaleOf(container)).toBeCloseTo(reachable[0], 9)
    expect(isOverviewZoom(scaleOf(container), dpr)).toBe(dpr !== 2)
    const holder = container.querySelector('canvas')!.parentElement as HTMLElement
    fireEvent.mouseDown(holder, { button: 0, clientX: 100, clientY: 100 })
    fireEvent.mouseMove(holder, { clientX: 107, clientY: 111 })
    const match = /translate\(([-\d.]+)px, ([-\d.]+)px\)/.exec(holder.style.transform)!
    for (const v of [match[1], match[2]]) expect(Math.abs(parseFloat(v) * dpr - Math.round(parseFloat(v) * dpr))).toBeLessThan(1e-9)
    press('Zoom In')
    expect(scaleOf(container)).toBeCloseTo(reachable[1], 9)
    expect(isOverviewZoom(scaleOf(container), dpr)).toBe(false)
  })

  it('the mouse wheel steps the same levels', () => {
    const { container } = mount(dpr)
    const reachable = zoomLevels(dpr, WORLD_MIN_ZOOM, WORLD_MAX_ZOOM)
    const root = container.firstElementChild as HTMLElement
    for (let i = 0; i < 12; i += 1) {
      fireEvent.wheel(root, { deltaY: -100 })
      const z = scaleOf(container)
      expect(reachable.some((l) => Math.abs(l - z) < 1e-9)).toBe(true)
    }
    expect(scaleOf(container)).toBeCloseTo(reachable[reachable.length - 1], 9)
    for (let i = 0; i < 12; i += 1) fireEvent.wheel(root, { deltaY: 100 })
    expect(scaleOf(container)).toBeCloseTo(reachable[0], 9)
  })

  it('the overlay canvas draws one tile pixel as a whole number of device pixels too', () => {
    const { container } = mount(dpr)
    press('Zoom In')
    const overlay = container.querySelectorAll('canvas')[2] as HTMLCanvasElement
    const factor = parseFloat(/scale\(([\d.]+)\)/.exec(overlay.style.transform)![1])
    expect(Math.abs(factor * dpr - Math.round(factor * dpr))).toBeLessThan(1e-9) // CELL_SIZE (16) x zoom x dpr
    expect(overlay.style.imageRendering).toBe('pixelated')
  })
})

describe('GameCanvas panning', () => {
  const drag = (container: HTMLElement, dx: number, dy: number) => {
    const holder = container.querySelector('canvas')!.parentElement as HTMLElement
    fireEvent.mouseDown(holder, { button: 0, clientX: 100, clientY: 100 })
    fireEvent.mouseMove(holder, { clientX: 100 + dx, clientY: 100 + dy })
    const match = /translate\(([-\d.]+)px, ([-\d.]+)px\)/.exec(holder.style.transform)!
    return [parseFloat(match[1]), parseFloat(match[2])]
  }

  it.each([1.25, 1.5, 2])('at DPR %s a dragged offset is drawn on whole device pixels, not at the raw mouse distance', (dpr) => {
    const { container } = mount(dpr)
    const [x, y] = drag(container, 7, 11)
    for (const v of [x, y]) expect(Math.abs(v * dpr - Math.round(v * dpr))).toBeLessThan(1e-9)
    expect(Math.abs(x - 7)).toBeLessThanOrEqual(0.5 / dpr + 1e-9)
    if (dpr === 1.5) expect([x, y]).not.toEqual([7, 11]) // 7 css px = 10.5 device px: it moved to a whole one
  })

  it('at DPR 1 the offset is the mouse distance itself', () => {
    const { container } = mount(1)
    expect(drag(container, 7, 11)).toEqual([7, 11])
  })
})

describe('GameCanvas when the device pixel ratio changes while open', () => {
  it('re-snaps the zoom in force to a level of the new ratio', () => {
    const { container } = mount(1)
    press('Zoom In') // 2x at DPR 1
    expect(scaleOf(container)).toBe(2)
    act(() => { dprValue = 1.5; listeners.forEach((l) => l()) })
    const z = scaleOf(container)
    expect(Math.abs(z * 1.5 - Math.round(z * 1.5))).toBeLessThan(1e-9)
    expect(Math.abs(z - 2)).toBeLessThanOrEqual(1 / 3 + 1e-9) // nearest level of the new list
  })
})
