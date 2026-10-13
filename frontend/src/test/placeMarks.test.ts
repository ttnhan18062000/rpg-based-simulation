import { describe, expect, it, vi } from 'vitest'
import { CELL_SIZE } from '@/constants/colors'
import { PLACE_DEFAULT_COLOR, PLACE_TYPE_COLORS, drawPlaces, placeColor, placeRect } from '@/lib/placeMarks'
import type { Location } from '@/types/api'

const place = (over: Partial<Location> = {}): Location => ({ location_id: 'hometown_city', name: 'Hometown City', location_type: 'city', x: 25, y: 25, region_id: 'hometown', ...over })

describe('places on the live map', () => {
  it('outlines a point place as its one tile and a footprint place as its whole rectangle', () => {
    expect(placeRect(place())).toEqual({ x: 25 * CELL_SIZE, y: 25 * CELL_SIZE, w: CELL_SIZE, h: CELL_SIZE })
    expect(placeRect(place({ tiles: { x: 10, y: 20, width: 5, height: 3 } }))).toEqual({ x: 10 * CELL_SIZE, y: 20 * CELL_SIZE, w: 5 * CELL_SIZE, h: 3 * CELL_SIZE })
  })

  it('colours by place type and falls back visibly for an unknown type', () => {
    expect(placeColor(place({ location_type: 'nest' }))).toBe(PLACE_TYPE_COLORS.nest)
    expect(placeColor(place({ location_type: 'moon_base' }))).toBe(PLACE_DEFAULT_COLOR)
  })

  it('draws an outline and the name label for every place, and leaves the context state as it found it', () => {
    const ctx = { strokeRect: vi.fn(), fillText: vi.fn(), save: vi.fn(), restore: vi.fn() } as unknown as CanvasRenderingContext2D
    drawPlaces(ctx, [place(), place({ location_id: 'wolf_den_nest', name: 'Wolf Den Nest', location_type: 'nest', x: 87, y: 50 })])
    expect(ctx.strokeRect).toHaveBeenCalledTimes(2)
    expect((ctx.fillText as ReturnType<typeof vi.fn>).mock.calls.map((c) => c[0])).toEqual(['Hometown City', 'Wolf Den Nest'])
    expect(ctx.save).toHaveBeenCalledTimes(1)
    expect(ctx.restore).toHaveBeenCalledTimes(1)
  })

  it('draws nothing for a world with no places', () => {
    const ctx = { strokeRect: vi.fn(), fillText: vi.fn(), save: vi.fn(), restore: vi.fn() } as unknown as CanvasRenderingContext2D
    drawPlaces(ctx, [])
    expect(ctx.strokeRect).not.toHaveBeenCalled()
    expect(ctx.fillText).not.toHaveBeenCalled()
  })
})
