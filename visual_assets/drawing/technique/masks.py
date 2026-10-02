"""Shape masks as sets of (x, y) cells."""

from __future__ import annotations


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
