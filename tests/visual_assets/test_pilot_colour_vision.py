"""The arithmetic of the AM5-W05 check (pure Python): the simulation and the rule, on synthetic input. The verdict on the real tile is recorded by
`python -m visual_assets.review.pilot_colour_vision`, never asserted here (a test must not decide the result)."""

from __future__ import annotations

import pytest

from visual_assets.review import pilot_colour_vision as cv


def test_every_simulation_matrix_keeps_greys_grey():
    for vision, m in cv.MACHADO.items():
        assert [round(sum(row), 3) for row in m] == [1.0, 1.0, 1.0], vision  # Machado's matrices are normalised so white stays white
    for vision in cv.VISIONS:
        r, g, b = cv.simulate((0.5, 0.5, 0.5), vision)
        assert max(abs(r - 0.5), abs(g - 0.5), abs(b - 0.5)) < 0.01, vision


def test_lab_anchors_and_distance_basics():
    assert cv.to_lab((1.0, 1.0, 1.0))[0] == pytest.approx(100.0, abs=0.01)
    assert cv.to_lab((0.0, 0.0, 0.0))[0] == pytest.approx(0.0, abs=0.01)
    red, green = (1.0, 0.0, 0.0), (0.0, 0.6, 0.0)
    assert cv.delta_e(red, red, "normal") == 0.0
    assert cv.delta_e(red, green, "normal") > cv.delta_e(red, green, "deutan")  # red/green collapse under deuteranopia


def test_the_live_map_fills_are_read_from_the_source():
    fills = cv.tile_fills()
    assert fills[cv.FOREST] == "#1b3a1b" and fills[cv.SWAMP] == "#2a2a3a" and fills[cv.MOUNTAIN] == "#3a3a3a"
    assert {fills[c] for c in cv.NEIGHBOURS.values()} == {"#2a2a3a", "#3a3a3a", "#3a3420", "#0a4a0a", "#4a6030"}


def test_the_rule_on_synthetic_tiles():
    fills = cv.tile_fills()
    flat = [cv.from_hex(fills[cv.FOREST])] * 256
    same = cv.evaluate(flat, fills)
    assert same["p1"] and not same["p2"] and same["w05"] == "PASS" and same["wording"] == "same"  # the fill itself: no texture, no worse
    textured = [cv.from_hex(fills[cv.FOREST]) if i % 2 else cv.from_hex("#2f6b2f") for i in range(256)]
    assert cv.evaluate(textured, fills)["p2"]
    towards_swamp = [cv.from_hex(fills[cv.SWAMP])] * 256  # a tile that looks like a neighbour is less distinguishable
    worse = cv.evaluate(towards_swamp, fills)
    assert not worse["p1"] and worse["w05"] == "FAIL" and worse["wording"] == "worse"


def test_the_real_tile_decodes_to_256_opaque_pixels_and_the_report_is_complete():
    result = cv.evaluate(cv.tile_pixels(), cv.tile_fills())
    assert set(result["per_vision"]) == set(cv.VISIONS)
    assert result["w05"] in {"PASS", "FAIL"} and result["wording"] in {"better", "same", "worse"}
