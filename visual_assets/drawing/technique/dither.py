"""Ordered (Bayer) dithering."""

from __future__ import annotations

from visual_assets.drawing.errors import AdapterError

BAYER = {
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
    if matrix not in BAYER:
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
    m = BAYER[matrix]
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
