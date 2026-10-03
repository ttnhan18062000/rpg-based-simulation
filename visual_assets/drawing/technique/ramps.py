"""Hue-shifted colour ramps."""

from __future__ import annotations

import colorsys

from visual_assets.drawing.colors import hex_to_rgba, hue_toward, rgba_to_hex
from visual_assets.drawing.errors import AdapterError


def make_ramp(
    base: str,
    steps: int = 5,
    hue_shift: float = 14.0,
    dark_hue: float = 250.0,
    light_hue: float = 55.0,
    base_index: int | None = None,
) -> list[str]:
    """Hue-shifted colour ramp, dark -> light, with `base` exactly at `base_index`.

    Rules (docs/assets/pixel_art_technique.md §1): value rises monotonically; shadows drift toward blue/purple
    (`dark_hue`) and highlights toward yellow (`light_hue`) by `hue_shift` degrees per step along
    the shortest hue arc, never overshooting the target; saturation peaks near the base and falls
    toward the light end (avoids "eye-burning" bright saturated colours); near-neutral bases pick up a
    slight tint so shadows/highlights still read as warm/cool.
    """
    if not isinstance(steps, int) or not 2 <= steps <= 9:
        raise AdapterError("steps must be an integer in [2, 9]")
    if not 0.0 <= hue_shift <= 60.0:
        raise AdapterError("hue_shift must be in [0, 60] degrees per step")
    bi = steps // 2 if base_index is None else base_index
    if not 0 <= bi < steps:
        raise AdapterError("base_index must be inside the ramp")
    r, g, b, _ = hex_to_rgba(base)
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    h *= 360.0
    n_dark, n_light = bi, steps - 1 - bi
    v_dark = v * 0.42
    v_light = min(1.0, v * 1.18 + 0.14)
    out = []
    for i in range(steps):
        d = i - bi
        if d == 0:
            out.append(rgba_to_hex(r, g, b))
            continue
        if d < 0:
            frac = -d / n_dark
            # a near-neutral base has no meaningful hue: take the target hue outright
            hh = dark_hue if s < 0.10 else hue_toward(h, dark_hue, hue_shift * -d)
            vv = v - (v - v_dark) * frac
            ss = s * (1.0 - 0.10 * frac) + (0.06 * frac if s < 0.10 else 0.0)
        else:
            frac = d / n_light
            hh = light_hue if s < 0.10 else hue_toward(h, light_hue, hue_shift * d)
            vv = v + (v_light - v) * frac
            ss = s * (1.0 - 0.40 * frac) + (0.05 * frac if s < 0.10 else 0.0)
        rr, gg, bb = colorsys.hsv_to_rgb(hh / 360.0, max(0.0, min(1.0, ss)), max(0.0, min(1.0, vv)))
        out.append(rgba_to_hex(round(rr * 255), round(gg * 255), round(bb * 255)))
    return out
