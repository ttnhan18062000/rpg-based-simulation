"""Light-direction shading (pure; no Aseprite)."""

from __future__ import annotations

import pytest

from visual_assets.drawing.errors import AdapterError
from visual_assets.drawing.technique.masks import ellipse_cells, rect_cells
from visual_assets.drawing.technique.shading import N4, shade_offsets

# ============================================================ pure: shading


def test_bevel_rect_lights_top_left_edges_and_shades_bottom_right():
    mask = rect_cells(0, 0, 8, 8)
    off = shade_offsets(mask, "tl", 3, "bevel")
    assert off[(3, 0)] == 1 and off[(0, 3)] == 1  # top and left edge: lit
    assert off[(3, 7)] == -1 and off[(7, 3)] == -1  # bottom and right edge: shadow
    assert off[(3, 3)] == 0 and off[(4, 4)] == 0  # interior stays the base colour
    flipped = shade_offsets(mask, "br", 3, "bevel")
    assert flipped[(3, 7)] == 1 and flipped[(3, 0)] == -1  # light moved: edges swap


def test_round_ellipse_has_three_bands_light_side_toward_light():
    mask = ellipse_cells(0, 0, 12, 12)
    off = shade_offsets(mask, "tl", 3, "round")
    assert set(off.values()) == {-1, 0, 1}
    lit = [p for p, o in off.items() if o == 1]
    dark = [p for p, o in off.items() if o == -1]
    assert sum(x + y for x, y in lit) / len(lit) < sum(x + y for x, y in dark) / len(dark)
    br = shade_offsets(mask, "br", 3, "round")
    lit2 = [p for p, o in br.items() if o == 1]
    assert sum(x + y for x, y in lit2) / len(lit2) > sum(x + y for x, y in lit) / len(lit)


def test_five_bands_use_five_levels_on_a_large_form():
    off = shade_offsets(ellipse_cells(0, 0, 24, 24), "tl", 5, "round", contrast=0.08)
    assert set(off.values()) == {-2, -1, 0, 1, 2}


def test_shading_is_deterministic_and_has_no_orphan_bands():
    mask = ellipse_cells(0, 0, 14, 10)
    a = shade_offsets(mask, "tl", 3, "round")
    assert a == shade_offsets(mask, "tl", 3, "round")
    for p, o in a.items():
        nb = [a[(p[0] + dx, p[1] + dy)] for dx, dy in N4 if (p[0] + dx, p[1] + dy) in a]
        if len(nb) >= 2:
            assert o in nb, f"orphan band at {p}"


@pytest.mark.parametrize("kwargs", [
    {"light": "up"}, {"bands": 4}, {"form": "cone"}, {"contrast": 0.0}, {"contrast": 0.9},
])
def test_shading_validation(kwargs):
    with pytest.raises(AdapterError):
        shade_offsets(rect_cells(0, 0, 4, 4), **kwargs)


def test_shading_empty_mask_is_empty():
    assert shade_offsets(set()) == {}


