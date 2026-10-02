"""Ordered Bayer dithering (pure; no Aseprite)."""

from __future__ import annotations

import pytest

from visual_assets.drawing.errors import AdapterError
from visual_assets.drawing.technique.dither import BAYER, dither_cells

# ============================================================ pure: dithering


def test_bayer_matrices_are_permutations():
    for n, m in BAYER.items():
        flat = sorted(v for row in m for v in row)
        assert flat == list(range(n * n))


@pytest.mark.parametrize("matrix, level, light_of_total", [
    (2, 0.5, (2, 4)), (4, 0.5, (8, 16)), (4, 0.25, (4, 16)), (8, 0.25, (16, 64)), (8, 0.75, (48, 64)),
])
def test_dither_coverage_over_full_tile_is_exact(matrix, level, light_of_total):
    cells = [(x, y) for y in range(matrix) for x in range(matrix)]
    got = dither_cells(cells, level, matrix=matrix)
    assert sum(got.values()) == light_of_total[0] and len(got) == light_of_total[1]


def test_dither_extremes_and_gradient_monotone():
    cells = [(x, y) for y in range(8) for x in range(8)]
    assert not any(dither_cells(cells, 0.0).values())
    assert all(dither_cells(cells, 1.0).values())
    g = dither_cells(cells, 0.0, 1.0, axis="x", matrix=4)
    per_col = [sum(g[(x, y)] for y in range(8)) for x in range(8)]
    assert per_col[0] == 0 and per_col[-1] == 8 and per_col == sorted(per_col)
    d = dither_cells(cells, 0.0, 1.0, axis="diag", matrix=8)
    assert not d[(0, 0)] and d[(7, 7)]


def test_dither_is_deterministic_and_validates():
    cells = [(x, y) for y in range(6) for x in range(6)]
    assert dither_cells(cells, 0.4, 0.9, "y", 4) == dither_cells(cells, 0.4, 0.9, "y", 4)
    for bad in ({"level": 1.5}, {"level": -0.1}, {"level": 0.5, "matrix": 3},
                {"level": 0.5, "axis": "z"}, {"level": 0.5, "level_to": 2}):
        with pytest.raises(AdapterError):
            dither_cells(cells, **bad)
    assert dither_cells([], 0.5) == {}


