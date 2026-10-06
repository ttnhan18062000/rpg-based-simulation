import { useDevicePixelRatio } from '@/hooks/useDevicePixelRatio'
import { fitScale } from '@/lib/pixelScale'

interface PixelIconProps {
  /** URL of the sprite (a PNG drawn at its native size). */
  src: string
  /** The sprite's native size in art pixels (16 for a map glyph, 24 for a panel icon, 8 for a tier badge). */
  native: number
  /** The CSS box (px) the icon should fill as far as a whole-number scale allows. */
  box: number
  /** Text alternative: an icon never ships without a label (docs/assets/icon_style_guide.md). */
  label: string
  className?: string
}

/**
 * A pixel-art sprite at the largest whole-number scale that fits `box` at the current devicePixelRatio, never fractional (D20). The image is square, `native` x `native`;
 * its CSS size is `scale * native / devicePixelRatio`, i.e. exactly `scale * native` device pixels. Not used by any panel yet: wiring is the next batch.
 */
export function PixelIcon({ src, native, box, label, className }: PixelIconProps) {
  const dpr = useDevicePixelRatio()
  const { scale, cssSize } = fitScale(box, native, dpr)
  return (
    <img
      src={src}
      alt={label}
      width={cssSize}
      height={cssSize}
      data-scale={scale}
      draggable={false}
      className={className}
      style={{ width: cssSize, height: cssSize, imageRendering: 'pixelated' }}
    />
  )
}
