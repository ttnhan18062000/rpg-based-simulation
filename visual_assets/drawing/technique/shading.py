"""Hard-banded light-direction shading."""

from __future__ import annotations

import math
from collections import Counter, deque

from visual_assets.drawing.errors import AdapterError

N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))

LIGHTS = {
    "tl": (-1, -1), "t": (0, -1), "tr": (1, -1), "l": (-1, 0),
    "r": (1, 0), "bl": (-1, 1), "b": (0, 1), "br": (1, 1),
}


def _distance(mask: set) -> dict:
    """4-neighbour distance (in pixels) from each mask pixel to the nearest non-mask pixel."""
    dist, q = {}, deque()
    for p in mask:
        if any((p[0] + dx, p[1] + dy) not in mask for dx, dy in N4):
            dist[p] = 1
            q.append(p)
    while q:
        p = q.popleft()
        for dx, dy in N4:
            n = (p[0] + dx, p[1] + dy)
            if n in mask and n not in dist:
                dist[n] = dist[p] + 1
                q.append(n)
    return dist


def shade_offsets(
    mask, light: str = "tl", bands: int = 3, form: str = "round", bevel: int = 1,
    contrast: float = 0.12,
) -> dict[tuple[int, int], int]:
    """Hard-banded light-direction shading. Returns {pixel: offset} where offset is the ramp step
    relative to the base colour (negative = shadow, positive = highlight), in -(bands//2)..bands//2.

    Surface normals come from a height field derived from the mask's distance-to-edge: `round` uses
    a sphere profile (crescent shadows, flat core), `bevel` caps the height at `bevel` pixels (clean
    edge highlight/shadow on boxes). Shading follows the light, never the outline ("no pillow
    shading"). A final pass removes orphan pixels (a band shared with none of its 4 neighbours).
    """
    mask = set(mask)
    if light not in LIGHTS:
        raise AdapterError(f"light must be one of {sorted(LIGHTS)}")
    if bands not in (3, 5):
        raise AdapterError("bands must be 3 or 5")
    if form not in ("round", "bevel"):
        raise AdapterError("form must be 'round' or 'bevel'")
    if not 0.02 <= contrast <= 0.5:
        raise AdapterError("contrast must be in [0.02, 0.5]")
    if not mask:
        return {}
    k = bands // 2
    ldx, ldy = LIGHTS[light]
    norm = math.hypot(ldx, ldy)
    lx, ly, lz = 0.6 * ldx / norm, 0.6 * ldy / norm, 0.55
    ln = math.sqrt(lx * lx + ly * ly + lz * lz)
    lx, ly, lz = lx / ln, ly / ln, lz / ln
    dist = _distance(mask)
    dmax = max(dist.values())
    big_r = max(0.5, dmax - 0.5)

    def height(p) -> float:
        d = dist.get(p, 0)
        if d == 0:
            return 0.0
        if form == "bevel":
            return float(min(d, max(1, bevel)))
        dc = d - 0.5
        return math.sqrt(max(0.0, 2 * big_r * dc - dc * dc))

    flat = lz
    off: dict[tuple[int, int], int] = {}
    for p in mask:
        x, y = p
        gx = (height((x + 1, y)) - height((x - 1, y))) / 2
        gy = (height((x, y + 1)) - height((x, y - 1))) / 2
        nl = math.sqrt(gx * gx + gy * gy + 1.0)
        lit = (-gx * lx - gy * ly + lz) / nl
        off[p] = max(-k, min(k, int((lit - flat) / contrast)))
    # cluster hygiene: an orphan band becomes the majority band of its in-mask neighbours
    fixed = dict(off)
    for p, o in off.items():
        nb = [off[(p[0] + dx, p[1] + dy)] for dx, dy in N4 if (p[0] + dx, p[1] + dy) in off]
        if len(nb) >= 2 and o not in nb:
            fixed[p] = Counter(nb).most_common(1)[0][0]
    return fixed
