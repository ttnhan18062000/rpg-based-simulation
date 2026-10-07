import { useEffect, useState } from 'react'
import { normaliseDpr } from '@/lib/pixelScale'

const read = () => normaliseDpr(typeof window === 'undefined' ? 1 : window.devicePixelRatio)

/**
 * The current `devicePixelRatio`, kept up to date: browser zoom and moving the window to another display change it, and `matchMedia('(resolution: Xdppx)')`
 * fires once when the value leaves X (research_icon_craft.md §1). Falls back to a constant where `matchMedia` is missing.
 */
export function useDevicePixelRatio(): number {
  const [dpr, setDpr] = useState(read)
  useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return undefined
    const query = window.matchMedia(`(resolution: ${dpr}dppx)`)
    const onChange = () => setDpr(read())
    query.addEventListener('change', onChange)
    return () => query.removeEventListener('change', onChange)
  }, [dpr])
  return dpr
}
