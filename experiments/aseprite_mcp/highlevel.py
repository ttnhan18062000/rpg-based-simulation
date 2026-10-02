"""High-level pixel-art operations built on the bounded low-level adapter (spike).

Everything here is a *composer*: it computes pixels in Python (deterministic, no randomness) and
submits them through `adapter.apply_ops`, so every safety property of the adapter (immutable
revisions, stale-base check, sandbox, bounds) still holds. Technique rules and their sources are in
TECHNIQUE_GUIDE.md. Pure functions are separated from the ones that read/write a sprite so the
former are unit-testable without Aseprite.
"""

from __future__ import annotations

import colorsys
import math
import re
from collections import Counter, deque

import adapter

AdapterError = adapter.AdapterError

# --------------------------------------------------------------------------- colour helpers

_HEX = re.compile(r"^#([0-9a-fA-F]{6})([0-9a-fA-F]{2})?$")


def hex_to_rgba(value: str) -> tuple[int, int, int, int]:
    m = _HEX.fullmatch(value) if isinstance(value, str) else None
    if not m:
        raise AdapterError("color must be #rrggbb or #rrggbbaa")
    rgb, a = m.group(1), m.group(2) or "ff"
    return (int(rgb[0:2], 16), int(rgb[2:4], 16), int(rgb[4:6], 16), int(a, 16))


def rgba_to_hex(r: int, g: int, b: int, a: int = 255) -> str:
    base = f"#{r:02x}{g:02x}{b:02x}"
    return base if a == 255 else base + f"{a:02x}"


def norm_hex(value: str) -> str:
    """Canonical 8-digit lowercase form, as Aseprite readback reports it."""
    return rgba_to_hex(*hex_to_rgba(value)).ljust(9, "f") if len(value) == 7 else value.lower()


def luma(rgb) -> float:
    """Rec.709 luma on 0..255 sRGB values (perceptual enough for value-separation checks)."""
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def _hue_toward(h: float, target: float, amount: float) -> float:
    """Move hue `h` (degrees) toward `target` along the shortest arc by at most `amount` degrees."""
    delta = (target - h + 180.0) % 360.0 - 180.0
    step = max(-amount, min(amount, delta))
    return (h + step) % 360.0


# --------------------------------------------------------------------------- ramps


def make_ramp(
    base: str,
    steps: int = 5,
    hue_shift: float = 14.0,
    dark_hue: float = 250.0,
    light_hue: float = 55.0,
    base_index: int | None = None,
) -> list[str]:
    """Hue-shifted colour ramp, dark -> light, with `base` exactly at `base_index`.

    Rules (TECHNIQUE_GUIDE.md §1): value rises monotonically; shadows drift toward blue/purple
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
            hh = dark_hue if s < 0.10 else _hue_toward(h, dark_hue, hue_shift * -d)
            vv = v - (v - v_dark) * frac
            ss = s * (1.0 - 0.10 * frac) + (0.06 * frac if s < 0.10 else 0.0)
        else:
            frac = d / n_light
            hh = light_hue if s < 0.10 else _hue_toward(h, light_hue, hue_shift * d)
            vv = v + (v_light - v) * frac
            ss = s * (1.0 - 0.40 * frac) + (0.05 * frac if s < 0.10 else 0.0)
        rr, gg, bb = colorsys.hsv_to_rgb(hh / 360.0, max(0.0, min(1.0, ss)), max(0.0, min(1.0, vv)))
        out.append(rgba_to_hex(round(rr * 255), round(gg * 255), round(bb * 255)))
    return out


# --------------------------------------------------------------------------- dithering

_BAYER = {
    2: [[0, 2], [3, 1]],
    4: [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]],
    8: [
        [0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26],
        [12, 44, 4, 36, 14, 46, 6, 38], [60, 28, 52, 20, 62, 30, 54, 22],
        [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
        [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21],
    ],
}


def dither_cells(
    cells, level: float, level_to: float | None = None, axis: str = "x", matrix: int = 4
) -> dict[tuple[int, int], bool]:
    """Ordered (Bayer) dithering. Returns {cell: True if the LIGHT colour goes there}.

    `level` is the light-colour coverage in [0, 1]. With `level_to`, coverage ramps linearly from
    `level` to `level_to` across the cells' bounding box along `axis` ('x', 'y' or 'diag').
    A cell is light when coverage > (M[y%n][x%n] + 0.5) / n^2, so level 0 is all dark, 1 all light,
    and 0.5 over a whole tile is exactly half.
    """
    if matrix not in _BAYER:
        raise AdapterError("matrix must be 2, 4 or 8")
    if axis not in ("x", "y", "diag"):
        raise AdapterError("axis must be 'x', 'y' or 'diag'")
    for v in (level, level_to):
        if v is not None and not (isinstance(v, (int, float)) and 0.0 <= v <= 1.0):
            raise AdapterError("level must be a number in [0, 1]")
    cells = list(cells)
    if not cells:
        return {}
    xs, ys = [c[0] for c in cells], [c[1] for c in cells]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    m = _BAYER[matrix]
    n2 = matrix * matrix
    out = {}
    for x, y in cells:
        cov = float(level)
        if level_to is not None:
            if axis == "x":
                t = 0.0 if x1 == x0 else (x - x0) / (x1 - x0)
            elif axis == "y":
                t = 0.0 if y1 == y0 else (y - y0) / (y1 - y0)
            else:
                span = (x1 - x0) + (y1 - y0)
                t = 0.0 if span == 0 else ((x - x0) + (y - y0)) / span
            cov = level + (level_to - level) * t
        out[(x, y)] = cov > (m[y % matrix][x % matrix] + 0.5) / n2
    return out


# --------------------------------------------------------------------------- strokes


def _bresenham(x0, y0, x1, y1):
    pts = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1:
            return pts
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def _cheb(a, b) -> int:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def _is_l_corner(a, b, c) -> bool:
    """b is the middle pixel of an L: a-b and b-c are orthogonal unit steps and a, c are diagonal."""
    return (abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1 and abs(b[0] - c[0]) + abs(b[1] - c[1]) == 1
            and abs(a[0] - c[0]) == 1 and abs(a[1] - c[1]) == 1)


def stroke_pixels(points, closed: bool = False, pixel_perfect: bool = True) -> list[tuple[int, int]]:
    """Rasterise a polyline. `pixel_perfect` drops the middle pixel of every L-shaped corner
    (a, b, c where a-b and b-c are orthogonal steps and a, c are diagonal), which removes the
    'doubles' that make hand-drawn lines look thick and jagged.

    Which corners are intentional (never removed): the two ends of an open stroke, and any vertex
    where at least one adjacent segment is longer than one pixel step (Chebyshev length > 1). A
    vertex whose two adjacent segments are both single-pixel steps is freehand trace, not an intended
    corner, and is cleaned like any other L. For a closed stroke the first vertex is judged by the same
    rule using its wrap-around neighbours; a cleaned closed loop never drops below 3 pixels.
    Consecutive duplicate points are ignored. Cleanup repeats until no removable L corner is left."""
    pts: list[tuple[int, int]] = []
    for p in points:
        p = tuple(p)
        if not pts or p != pts[-1]:
            pts.append(p)
    if len(pts) < 1:
        raise AdapterError("points must hold at least one point")
    closed = closed and len(pts) > 2
    if closed and pts[0] == pts[-1]:
        pts.pop()
        closed = len(pts) > 2
    ring = pts + [pts[0]] if closed else pts
    path: list[tuple[int, int]] = [ring[0]]
    for a, b in zip(ring, ring[1:]):
        path.extend(_bresenham(*a, *b)[1:])
    seq = path[:-1] if closed else path  # a closed ring is cyclic, without the repeated start
    if pixel_perfect and len(seq) >= 3:
        n = len(pts)
        protected = set()
        for i, v in enumerate(pts):
            if not closed and i in (0, n - 1):
                protected.add(v)
                continue
            prev, nxt = pts[i - 1], pts[(i + 1) % n]
            if _cheb(prev, v) > 1 or _cheb(v, nxt) > 1:
                protected.add(v)
        seq = _remove_l_corners(seq, protected, closed)
    return seq + [seq[0]] if closed else seq


def _remove_l_corners(seq, protected: set, cyclic: bool) -> list[tuple[int, int]]:
    seq = list(seq)
    floor = 3 if cyclic else 2
    changed = True
    while changed and len(seq) > floor:
        changed = False
        n = len(seq)
        for i in (range(n) if cyclic else range(1, n - 1)):
            b = seq[i]
            if b in protected:
                continue
            if _is_l_corner(seq[i - 1], b, seq[(i + 1) % n]):
                del seq[i]
                changed = True
                break
    return seq


# --------------------------------------------------------------------------- shading

LIGHTS = {
    "tl": (-1, -1), "t": (0, -1), "tr": (1, -1), "l": (-1, 0),
    "r": (1, 0), "bl": (-1, 1), "b": (0, 1), "br": (1, 1),
}
_N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _distance(mask: set) -> dict:
    """4-neighbour distance (in pixels) from each mask pixel to the nearest non-mask pixel."""
    dist, q = {}, deque()
    for p in mask:
        if any((p[0] + dx, p[1] + dy) not in mask for dx, dy in _N4):
            dist[p] = 1
            q.append(p)
    while q:
        p = q.popleft()
        for dx, dy in _N4:
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
        nb = [off[(p[0] + dx, p[1] + dy)] for dx, dy in _N4 if (p[0] + dx, p[1] + dy) in off]
        if len(nb) >= 2 and o not in nb:
            fixed[p] = Counter(nb).most_common(1)[0][0]
    return fixed


# --------------------------------------------------------------------------- masks / grids


def ellipse_cells(x, y, w, h) -> set:
    rx, ry = w / 2, h / 2
    cx, cy = x + rx, y + ry
    return {
        (px, py)
        for py in range(y, y + h)
        for px in range(x, x + w)
        if ((px + 0.5 - cx) / rx) ** 2 + ((py + 0.5 - cy) / ry) ** 2 <= 1.0
    }


def rect_cells(x, y, w, h) -> set:
    return {(px, py) for py in range(y, y + h) for px in range(x, x + w)}


def ascii_grid(grid: list[list[str]]) -> tuple[list[str], dict[str, str]]:
    """Turn a hex grid into text rows plus a legend. '.' is transparent; opaque colours get
    letters/digits in order of first appearance (most opaque colours first by frequency)."""
    counts = Counter(c for row in grid for c in row if not c.endswith("00"))
    symbols = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    legend = {}
    for i, (c, _) in enumerate(counts.most_common()):
        legend[c] = symbols[i] if i < len(symbols) else "?"
    rows = ["".join("." if c.endswith("00") else legend[c] for c in row) for row in grid]
    return rows, {sym: col for col, sym in legend.items()}


# --------------------------------------------------------------------------- lint (pure)

_BUDGETS = ((16, 8), (32, 12), (64, 16))  # (max side, colour budget); above: 24
OUTLINE_LUMA_MAX = 70.0


def lint_grid(grid: list[list[str]], layers_hint: dict | None = None) -> dict:
    """Check a flattened frame against the researched rules. Findings are advice, not gates."""
    h, w = len(grid), len(grid[0]) if grid else 0
    rgba = [[hex_to_rgba(c) for c in row] for row in grid]
    opaque = {(x, y) for y in range(h) for x in range(w) if rgba[y][x][3] > 0}
    findings: list[dict] = []
    stats: dict = {"width": w, "height": h, "opaque_pixels": len(opaque)}

    def add(level, code, message, **data):
        findings.append({"level": level, "code": code, "message": message, **data})

    if not opaque:
        add("warn", "empty", "frame has no opaque pixels")
        return {"ok": False, "findings": findings, "stats": stats}

    colors = Counter(grid[y][x] for x, y in opaque)
    side = max(w, h)
    budget = next((b for s, b in _BUDGETS if side <= s), 24)
    stats["colors"] = len(colors)
    stats["color_budget"] = budget
    if len(colors) > budget:
        add("warn", "palette_budget",
            f"{len(colors)} colours on a {w}x{h} sprite; guidance is <= {budget} "
            "(extra colours read as noise at this size)", count=len(colors), budget=budget)

    xs, ys = [p[0] for p in opaque], [p[1] for p in opaque]
    bbox = (min(xs), min(ys), max(xs), max(ys))
    stats["bbox"] = bbox
    if bbox[0] == 0 or bbox[1] == 0 or bbox[2] == w - 1 or bbox[3] == h - 1:
        add("info", "touches_edge",
            "artwork touches the canvas edge; leave 1px padding if overlays (HP bar, status) need room",
            bbox=bbox)

    orphans = []
    for x, y in sorted(opaque, key=lambda p: (p[1], p[0])):
        c = grid[y][x]
        same = sum(1 for dx, dy in _N4 if (x + dx, y + dy) in opaque and grid[y + dy][x + dx] == c)
        if same == 0:
            orphans.append((x, y))
    stats["orphan_pixels"] = len(orphans)
    if orphans:
        add("info", "orphan_pixels",
            f"{len(orphans)} single-pixel islands (a colour touching nothing of itself). Fine for "
            "deliberate details such as eyes; otherwise merge them into a cluster",
            pixels=orphans[:20])

    distinct = sorted(colors, key=lambda c: luma(hex_to_rgba(c)))
    close = []
    for a, b in zip(distinct, distinct[1:]):
        if abs(luma(hex_to_rgba(a)) - luma(hex_to_rgba(b))) < 12:
            close.append((a, b))
    if close:
        add("warn", "value_separation",
            "colours with almost equal brightness merge in grayscale (ART-W06: critical distinctions "
            "must survive without hue); separate their values or merge them", pairs=close[:5])

    boundary = {
        p for p in opaque
        if any((p[0] + dx, p[1] + dy) not in opaque for dx, dy in _N4)
    }
    dark = [p for p in boundary if luma(rgba[p[1]][p[0]]) <= OUTLINE_LUMA_MAX]
    frac = len(dark) / len(boundary) if boundary else 0.0
    stats["dark_boundary_fraction"] = round(frac, 3)
    if 0.15 < frac < 0.85:
        add("info", "mixed_outline",
            f"{frac:.0%} of the silhouette edge is dark. Sources disagree on mixed outlines: selective "
            "outlining is a valid style when intentional, but check it is not accidental",
            fraction=round(frac, 3))
    return {"ok": not any(f["level"] == "warn" for f in findings), "findings": findings, "stats": stats}
