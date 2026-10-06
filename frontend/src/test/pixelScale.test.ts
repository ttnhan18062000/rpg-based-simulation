// D20: the Live Map zoom and pixel icons use whole-number pixel scales. Pure arithmetic of lib/pixelScale.ts.
import { describe, expect, it } from 'vitest'
import { CELL_SIZE } from '@/constants/colors'
import {
  WORLD_DEFAULT_ZOOM, WORLD_MAX_ZOOM, WORLD_MIN_ZOOM, deviceScale, fitScale, isOverviewZoom, normaliseDpr, snapToDevicePixel, snapZoom, stepZoom, zoomLevels,

} from '@/lib/pixelScale'

const DPRS = [1, 1.25, 1.5, 2, 3]
const levelsAt = (dpr: number) => zoomLevels(dpr, WORLD_MIN_ZOOM, WORLD_MAX_ZOOM)

describe('the reachable zoom levels', () => {
  it.each(DPRS)('at DPR %s every art level is a whole number of device pixels per art pixel and the one overview level a whole cell', (dpr) => {
    const levels = levelsAt(dpr)
    expect(levels.length).toBeGreaterThan(0)
    for (const zoom of levels) {
      expect(zoom).toBeGreaterThanOrEqual(WORLD_MIN_ZOOM - 0.1)
      expect(zoom).toBeLessThanOrEqual(WORLD_MAX_ZOOM + 1e-9)
      if (isOverviewZoom(zoom, dpr)) {
        expect(zoom).toBe(levels[0]) // only the bottom level can be an overview level
        expect(Math.abs(CELL_SIZE * zoom * dpr - Math.round(CELL_SIZE * zoom * dpr))).toBeLessThan(1e-9) // a cell is whole
      } else {
        expect(Math.abs(zoom * dpr - Math.round(zoom * dpr))).toBeLessThan(1e-9)
        expect(Math.round(zoom * dpr)).toBeGreaterThanOrEqual(1)
      }
    }
    expect(levels.filter((z) => isOverviewZoom(z, dpr)).length).toBeLessThanOrEqual(1)
    expect([...levels].sort((a, b) => a - b)).toEqual(levels)
    expect(new Set(levels).size).toBe(levels.length)
  })

  it('the level list per DPR is stated here, overview level first: 0.5 then 1x/2x/3x at DPR 1; nothing added at DPR 2', () => {
    expect(levelsAt(1)).toEqual([0.5, 1, 2, 3])
    expect(levelsAt(2)).toEqual([0.5, 1, 1.5, 2, 2.5, 3]) // 0.5 is already an art level (1 device pixel per art pixel)
    expect(levelsAt(1.5).map((z) => Math.round(z * 1.5 * 1000) / 1000)).toEqual([0.75, 1, 2, 3, 4]) // overview 0.5, then art n = 1..4
    expect(levelsAt(1.5)[0]).toBe(0.5)
    expect(levelsAt(1.25)[0]).toBe(0.5)
    expect(levelsAt(1.25).slice(1).map((z) => Math.round(z * 1.25))).toEqual([1, 2, 3])
    expect(levelsAt(3)[0]).toBe(0.5)
    expect(levelsAt(3).length).toBe(1 + 8) // overview 0.5, then n = 2..9 (0.667 ... 3.0)
  })

  it('the overview level is the zoom nearest the minimum at which a cell is a whole number of device pixels', () => {
    // at DPR 1, 1.25, 1.5 that is the minimum itself: 8, 10 and 12 device pixels per cell (the planner expected 0.4 or 0.6 at 1.25: 0.5 already gives a whole cell)
    for (const [dpr, cell] of [[1, 8], [1.25, 10], [1.5, 12]] as const) expect(CELL_SIZE * levelsAt(dpr)[0] * dpr).toBeCloseTo(cell, 9)
    // a ratio where the minimum itself does not give a whole cell: DPR 1.1 -> 8.8 device px, nearest whole 9 -> 9 / (16 x 1.1)
    expect(zoomLevels(1.1, 0.5, 3)[0]).toBeCloseTo(9 / (CELL_SIZE * 1.1), 12)
    expect(CELL_SIZE * zoomLevels(1.1, 0.5, 3)[0] * 1.1).toBeCloseTo(9, 9)
  })

  it('no overview level is added when the range minimum is itself an art level or above the first one', () => {
    expect(zoomLevels(2, 0.5, 3)[0]).toBe(0.5)
    expect(zoomLevels(1, 1, 3)).toEqual([1, 2, 3])
    expect(zoomLevels(1, 0.5, 3).length).toBe(4)
  })

  it('isOverviewZoom is true exactly when one art pixel is not a whole number (at least 1) of device pixels', () => {
    expect(isOverviewZoom(0.5, 1)).toBe(true)
    expect(isOverviewZoom(0.999, 1)).toBe(true)
    expect(isOverviewZoom(1, 1)).toBe(false)
    expect(isOverviewZoom(0.5, 2)).toBe(false) // 1 device pixel per art pixel
    expect(isOverviewZoom(0.5, 3)).toBe(true) // 1.5
    expect(isOverviewZoom(2.4, 1.25)).toBe(false) // 3
    expect(isOverviewZoom(2, 1.5)).toBe(false)
    expect(isOverviewZoom(0.5, 1.5)).toBe(true) // 0.75
    for (const dpr of DPRS) for (const z of levelsAt(dpr).slice(1)) expect(isOverviewZoom(z, dpr)).toBe(false)
  })

  it('the default zoom is reachable at DPR 1 and 2 (reset lands on a real level)', () => {
    for (const dpr of [1, 2]) expect(snapZoom(WORLD_DEFAULT_ZOOM, levelsAt(dpr))).toBe(WORLD_DEFAULT_ZOOM)
  })

  it('a range with no whole scale still yields the one art level 1 / dpr', () => {
    expect(zoomLevels(1, 0.3, 0.9)).toEqual([5 / 16, 1]) // the art level 1 / dpr, under an overview level at a whole 5-pixel cell
    expect(zoomLevels(2, 0.1, 0.4)).toEqual([3 / 32, 0.5])
  })

  it('a broken devicePixelRatio is treated as 1', () => {
    for (const bad of [0, -2, NaN, Infinity, undefined, null]) expect(normaliseDpr(bad as number)).toBe(1)
    expect(levelsAt(0)).toEqual(levelsAt(1))
  })
})

describe('stepping and snapping', () => {
  it('steps one level at a time and clamps at both ends', () => {
    const levels = levelsAt(1)
    expect(levels).toEqual([0.5, 1, 2, 3])
    expect(stepZoom(1, 1, levels)).toBe(2)
    expect(stepZoom(2, 1, levels)).toBe(3)
    expect(stepZoom(3, 1, levels)).toBe(3)
    expect(stepZoom(3, -1, levels)).toBe(2)
    expect(stepZoom(2, -1, levels)).toBe(1)
    expect(stepZoom(1, -1, levels)).toBe(0.5) // stepping down reaches the overview level ...
    expect(stepZoom(0.5, -1, levels)).toBe(0.5) // ... and clamps there
    expect(stepZoom(0.5, 1, levels)).toBe(1) // stepping up leaves it for the first art level
  })

  it('walking up then down visits exactly the level list', () => {
    for (const dpr of DPRS) {
      const levels = levelsAt(dpr)
      const up = [levels[0]]
      while (up[up.length - 1] !== levels[levels.length - 1]) up.push(stepZoom(up[up.length - 1], 1, levels))
      expect(up).toEqual(levels)
    }
  })

  it('an arbitrary zoom (a stale value after a DPR change) snaps to the nearest level; a tie goes up', () => {
    expect(snapZoom(1.4, levelsAt(1))).toBe(1)
    expect(snapZoom(1.6, levelsAt(1))).toBe(2)
    expect(snapZoom(1.5, levelsAt(1))).toBe(2)
    expect(snapZoom(2.0, levelsAt(2))).toBe(2)
    expect(stepZoom(1.4, 1, levelsAt(1))).toBe(2) // from the snapped level 1
  })

  it('moving from DPR 1 to DPR 2 keeps the zoom in force within one level of what it was', () => {
    for (const z of levelsAt(1)) expect(Math.abs(snapZoom(z, levelsAt(2)) - z)).toBeLessThanOrEqual(0.25)
  })
})

describe('device pixels', () => {
  it('deviceScale is the whole n of a level whatever the float noise', () => {
    for (const dpr of DPRS) {
      const art = levelsAt(dpr).filter((z) => !isOverviewZoom(z, dpr))
      art.forEach((z, i) => expect(deviceScale(z, dpr)).toBe(Math.round(art[0] * dpr) + i))
    }
  })

  it('a translation snaps to a whole device pixel', () => {
    expect(snapToDevicePixel(10.3, 1)).toBe(10)
    expect(snapToDevicePixel(10.3, 2)).toBe(10.5)
    expect(snapToDevicePixel(-7.26, 1.25) * 1.25).toBeCloseTo(Math.round(-7.26 * 1.25), 9)
    for (const dpr of DPRS) for (const v of [0, 0.1, 13.37, -250.42]) expect(snapToDevicePixel(v, dpr) * dpr).toBeCloseTo(Math.round(snapToDevicePixel(v, dpr) * dpr), 9)
  })
})

describe('fitScale for a pixel icon', () => {
  it('picks the largest whole scale that fits the box, never fractional', () => {
    expect(fitScale(40, 16, 1)).toEqual({ scale: 2, cssSize: 32, fits: true })
    expect(fitScale(48, 16, 1)).toEqual({ scale: 3, cssSize: 48, fits: true })
    expect(fitScale(47.9, 16, 1).scale).toBe(2)
    expect(fitScale(40, 16, 2)).toEqual({ scale: 5, cssSize: 40, fits: true }) // 5 * 16 = 80 device px = 40 css px
    expect(fitScale(24, 24, 1)).toEqual({ scale: 1, cssSize: 24, fits: true })
    expect(fitScale(32, 8, 1).scale).toBe(4)
  })

  it('a fractional DPR gives a fractional CSS size that is still a whole number of device pixels', () => {
    const { scale, cssSize } = fitScale(40, 16, 1.25)
    expect(scale).toBe(3)
    expect(cssSize).toBeCloseTo(38.4, 9)
    expect(cssSize * 1.25).toBeCloseTo(48, 9) // 3 x 16 device pixels
  })

  it('a box smaller than one whole scale shows scale 1 and says it does not fit', () => {
    expect(fitScale(10, 16, 1)).toEqual({ scale: 1, cssSize: 16, fits: false })
    expect(fitScale(10, 24, 2)).toEqual({ scale: 1, cssSize: 12, fits: false })
  })

  it('for every box, DPR and size the device size is an exact multiple of the native size', () => {
    for (const dpr of DPRS) for (const native of [8, 16, 24]) for (let box = 4; box <= 96; box += 5) {
      const { scale, cssSize } = fitScale(box, native, dpr)
      expect(Number.isInteger(scale)).toBe(true)
      expect(cssSize * dpr).toBeCloseTo(scale * native, 9)
    }
  })
})
