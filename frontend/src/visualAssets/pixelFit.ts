// Whole-number pixel scales for the icon preview page: a COPY of the fit function in src/lib/pixelScale.ts (D20), because this module imports nothing from outside src/visualAssets/
// (the AM5-W08 isolation guard). A test asserts the two give the same answers over a grid of boxes, sizes and device pixel ratios.

/** A device pixel ratio the code can divide by: finite and positive, else 1. */
export function normaliseDpr(dpr: number | undefined | null): number {
  return typeof dpr === 'number' && Number.isFinite(dpr) && dpr > 0 ? dpr : 1
}

/** The largest whole-number scale at which a `native` px image fits a CSS box of `boxCss` px, never fractional (scale 1 at least). */
export function fitScale(boxCss: number, native: number, dpr: number): { scale: number; cssSize: number; fits: boolean } {
  const d = normaliseDpr(dpr)
  const raw = Math.floor((boxCss * d) / native + 1e-9)
  const scale = Math.max(1, raw)
  return { scale, cssSize: (scale * native) / d, fits: raw >= 1 }
}

/** The CSS size of a `native` px image drawn at the whole device-pixel scale `scale`. */
export function cssSizeAtScale(scale: number, native: number, dpr: number): number {
  return (scale * native) / normaliseDpr(dpr)
}
