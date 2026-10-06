import { act, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { PixelIcon } from '@/components/PixelIcon'
import { useDevicePixelRatio } from '@/hooks/useDevicePixelRatio'

type Listener = () => void
let dprValue = 1
let listeners: Listener[] = []

beforeEach(() => {
  dprValue = 1
  listeners = []
  Object.defineProperty(window, 'devicePixelRatio', { configurable: true, get: () => dprValue })
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    media: query, matches: true,
    addEventListener: (_: string, cb: Listener) => listeners.push(cb),
    removeEventListener: (_: string, cb: Listener) => { listeners = listeners.filter((l) => l !== cb) },
  })) as unknown as typeof window.matchMedia
})
afterEach(() => { vi.restoreAllMocks() })

const changeDpr = (next: number) => act(() => { dprValue = next; [...listeners].forEach((l) => l()) })

function Probe() { return <span data-testid="dpr">{useDevicePixelRatio()}</span> }

describe('useDevicePixelRatio', () => {
  it('reads the ratio, follows a change and stops listening on unmount', () => {
    const { unmount } = render(<Probe />)
    expect(screen.getByTestId('dpr').textContent).toBe('1')
    changeDpr(2)
    expect(screen.getByTestId('dpr').textContent).toBe('2')
    unmount()
    expect(listeners).toHaveLength(0)
  })

  it('a broken ratio reads as 1', () => {
    dprValue = 0
    render(<Probe />)
    expect(screen.getByTestId('dpr').textContent).toBe('1')
  })

  it('without matchMedia it still returns the ratio', () => {
    // @ts-expect-error simulating a very old environment
    window.matchMedia = undefined
    render(<Probe />)
    expect(screen.getByTestId('dpr').textContent).toBe('1')
  })
})

describe('PixelIcon', () => {
  it('draws at the largest whole scale that fits the box and labels itself', () => {
    render(<PixelIcon src="/x.png" native={16} box={40} label="Enemy camp" />)
    const img = screen.getByRole('img', { name: 'Enemy camp' })
    expect(img.dataset.scale).toBe('2')
    expect(img).toHaveStyle({ width: '32px', height: '32px', imageRendering: 'pixelated' })
    expect(img).toHaveAttribute('draggable', 'false')
  })

  it('re-picks the scale when the device pixel ratio changes (browser zoom, another display)', () => {
    render(<PixelIcon src="/x.png" native={16} box={40} label="Shrine" />)
    const img = screen.getByRole('img', { name: 'Shrine' })
    expect(img.dataset.scale).toBe('2')
    changeDpr(2)
    expect(img.dataset.scale).toBe('5')
    expect(img).toHaveStyle({ width: '40px' })
    changeDpr(1.25)
    expect(img.dataset.scale).toBe('3')
    expect(parseFloat(img.style.width) * 1.25).toBeCloseTo(48, 9)
  })

  it('never goes below scale 1 for a box that is too small', () => {
    render(<PixelIcon src="/x.png" native={24} box={10} label="Blacksmith" />)
    expect(screen.getByRole('img', { name: 'Blacksmith' }).dataset.scale).toBe('1')
  })
})
