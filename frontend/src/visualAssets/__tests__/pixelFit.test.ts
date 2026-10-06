// The preview page's copy of the whole-number fit function equals the app's own (src/lib/pixelScale.ts), which the page may not import (AM5-W08 isolation).
import { describe, expect, it } from 'vitest'
import { fitScale as appFit, normaliseDpr as appNormalise } from '@/lib/pixelScale'
import { cssSizeAtScale, fitScale, normaliseDpr } from '../pixelFit'

const DPRS = [1, 1.25, 1.5, 2, 3, 0, NaN]

describe('pixelFit is a faithful copy of src/lib/pixelScale.ts', () => {
  it('fitScale gives the same answer over boxes, native sizes and ratios', () => {
    for (const dpr of DPRS) for (const native of [8, 16, 24]) for (let box = 1; box <= 120; box += 3) {
      expect(fitScale(box, native, dpr), `${box}/${native}/${dpr}`).toEqual(appFit(box, native, dpr))
    }
  })

  it('normaliseDpr gives the same answer', () => {
    for (const bad of [0, -1, NaN, Infinity, undefined, null, 1, 1.5, 2]) expect(normaliseDpr(bad)).toBe(appNormalise(bad))
  })

  it('cssSizeAtScale is a whole number of device pixels', () => {
    for (const dpr of [1, 1.25, 1.5, 2]) for (const n of [1, 2, 3, 4]) for (const native of [8, 16, 24]) {
      expect(Math.abs(cssSizeAtScale(n, native, dpr) * dpr - n * native)).toBeLessThan(1e-9)
    }
  })
})
