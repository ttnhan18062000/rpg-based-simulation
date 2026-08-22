"""Terrain-string casing normalization at the render boundary.

TCK-20260821-WORLD-RENDER-CORE: real compiled content mixes 'PLAIN'/'plain'/'forest'
as distinct dict keys (uppercase code-level defaults vs. lowercase-or-mixed
content-authored strings). terrain_color() must normalize case-insensitively and
give unrecognized values a loud, visually distinct fallback — never silently
mismap them onto an existing color.
"""
from __future__ import annotations

from src.rendering.render import DEFAULT_TERRAIN_COLOR, TERRAIN_COLORS, terrain_color


def test_terrain_casing_normalized_with_loud_fallback():
    # (a) case variants of a known terrain resolve to the same color.
    assert terrain_color("PLAIN") == terrain_color("plain") == terrain_color("Plain")

    # (b) another known-vocabulary value, regardless of input case.
    assert terrain_color("forest") == terrain_color("FOREST") == TERRAIN_COLORS["FOREST"]

    # (c) a genuinely unrecognized value gets the loud fallback, distinct from every
    # known terrain color — not silently blended into an existing one.
    fallback = terrain_color("NOT_A_REAL_TERRAIN")
    assert fallback == DEFAULT_TERRAIN_COLOR
    assert DEFAULT_TERRAIN_COLOR not in TERRAIN_COLORS.values()
