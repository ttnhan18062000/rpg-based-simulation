"""Pixel-perfect polylines."""

from __future__ import annotations

from visual_assets.drawing.errors import AdapterError


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
