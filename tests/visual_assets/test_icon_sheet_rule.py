"""The icon palette and the icon sheet rule (I1-I3) on synthetic sprites and on the real terrain-v1 tiles (`TCK-20261006-VISUAL-ASSETS-ICON-PALETTE-AND-SHEET-RULE`).

The thresholds are the user's answers of 2026-10-06 (`docs/assets/icon_criteria.md`). A test here checks the arithmetic of the rule on planted input; it never decides a verdict on art (there is none yet).
"""

from __future__ import annotations

import json

import pytest

from tests.visual_assets import icon_palette as ip
from tests.visual_assets import icon_sheet_rule as rule
from tests.visual_assets import icon_sheet_synthetic as syn
from tests.visual_assets.pilot_colour_vision import VISIONS, from_hex, mean

PROTAN_COLLAPSE = ("#555b73", "#d04030")  # L* differ by 9.6 in normal vision and by 0.85 under protanopia


def _flat(side: int, colour: str, shape: set | None = None) -> rule.Sprite:
    shape = shape if shape is not None else {(x, y) for x in range(side) for y in range(side)}
    r, g, b = (round(c * 255) for c in from_hex(colour))
    return rule.Sprite(side, side, tuple((r, g, b, 255) if (i % side, i // side) in shape else (0, 0, 0, 0) for i in range(side * side)))


def _block(side: int, n: int) -> set:
    """A square-ish block of n pixels at the top-left of a side x side canvas (shape differing from the empty set by exactly n)."""
    return {(i % side, i // side) for i in range(n)}


# ---- the palette ---------------------------------------------------------------------------------------------------------------------------------------------------------------------


def test_the_committed_palette_is_exactly_what_the_derivation_builds():
    assert json.loads(ip.PALETTE_FILE.read_text()) == ip.build_palette()


def test_every_terrain_colour_traces_to_a_terrain_key_and_its_adopted_tile():
    fills = ip.terrain_fills()
    assert len(fills) == 23
    palette = ip.build_palette()
    assert all(colour in palette["colors"] for colour in fills.values())
    assert {e["source"] for e in palette["entries"] if e["role"] == "terrain"} <= set(fills)
    deviation = ip.fill_deviation()
    assert set(deviation) == set(fills) and max(deviation.values()) <= ip.FILL_TOLERANCE
    # forest is the pilot tile adopted before the re-tint; the other 22 are equal to their fill within a unit
    assert sorted(k for k, d in deviation.items() if d > 1.0) == ["terrain.forest"]


def test_palette_shape_ramps_accents_and_formats():
    palette = ip.build_palette()
    colours = palette["colors"]
    assert len(colours) == len(set(colours)) and all(c == c.lower() and len(c) == 7 and c[0] == "#" for c in colours)
    assert len(ip.ACCENTS) == 8 and len({c for c, _, _ in ip.ACCENTS}) == 8  # ticket: an accent set of at most 8
    roles = [e["role"] for e in palette["entries"]]
    assert roles.count("ramp") + sum(1 for e in palette["entries"] if "also" in e) >= 7 * 3  # every ramp contributes its three non-seed steps (the seed is a terrain colour)
    for seed in ip.RAMP_SEEDS:
        ramp = syn._ramp_order(ip.terrain_fills()[seed])
        assert len(ramp) == ip.RAMP_STEPS and ramp[ip.RAMP_BASE_INDEX] == ip.terrain_fills()[seed] and all(c in colours for c in ramp)
    assert len(colours) <= 64


# ---- I1 shape ------------------------------------------------------------------------------------------------------------------------------------------------------------------------


def _group_report(a: rule.Sprite, b: rule.Sprite, classes=None, **kw):
    return rule.evaluate_sheet({"a": a, "b": b}, {"g": classes or [["a"], ["b"]]}, {}, {}, **kw)


def test_i1_identical_silhouette_pair_fails_and_a_recoloured_only_pair_fails():
    shape = _block(8, 20)
    same = _group_report(_flat(8, "#555b73", shape), _flat(8, "#555b73", shape))
    recoloured = _group_report(_flat(8, "#555b73", shape), _flat(8, "#e8c040", shape))
    for report in (same, recoloured):
        assert not report["i1"] and report["failing"]["i1"][0]["shape_px"] == 0 and report["result"] == "FAIL"


def test_i1_a_shape_distinct_pair_passes():
    report = _group_report(_flat(16, "#555b73", _block(16, 100)), _flat(16, "#555b73", _block(16, 100) | {(15, y) for y in range(15)}), classes=[["a"], ["b"]])
    assert report["i1"] is True and report["groups"]["g"]["min_shape_px_across_classes"] == 9  # the 15-pixel column minus the 6 pixels the block already holds


@pytest.mark.parametrize(("side", "need"), [(8, 3), (16, 6)])
def test_i1_boundary_at_the_users_threshold(side, need):
    base = _block(side, 20)
    extra = [(x, y) for y in range(side) for x in range(side) if (x, y) not in base]
    ok = _group_report(_flat(side, "#555b73", base), _flat(side, "#555b73", base | set(extra[:need])))
    short = _group_report(_flat(side, "#555b73", base), _flat(side, "#555b73", base | set(extra[: need - 1])))
    assert ok["i1"] is True and short["i1"] is False and short["failing"]["i1"][0]["need"] == need


def test_i1_skips_pairs_inside_one_class_but_i2_still_separates_them():
    """E and D share a silhouette by the ladder's rule (the user's answer): I1 ignores that pair, I2 still has to separate them."""
    shape = _block(8, 30)
    e, d = _flat(8, "#555b73", shape), _flat(8, "#5a5f77", shape)  # near-identical colours
    report = _group_report(e, d, classes=[["a", "b"]])
    assert report["i1"] is True and report["i2"] is False and report["result"] == "FAIL"
    far = _group_report(_flat(8, "#28331d", shape), _flat(8, "#d9ecf3", shape), classes=[["a", "b"]])
    assert far["result"] == "PASS"


def test_an_unruled_canvas_size_raises_instead_of_passing():
    with pytest.raises(KeyError):
        _group_report(_flat(32, "#555b73", _block(32, 10)), _flat(32, "#555b73", _block(32, 300)))


# ---- I2 value ------------------------------------------------------------------------------------------------------------------------------------------------------------------------


def test_i2_boundary_between_two_greys():
    """The pair of greys closest to the threshold on each side: L* gap just under 6 fails, just over passes (the mean of a flat sprite is the colour itself)."""
    levels = [f"#{v:02x}{v:02x}{v:02x}" for v in range(256)]
    base = _flat(8, levels[100], _block(8, 40))
    gaps = {v: rule.value_distance(base, _flat(8, levels[v], _block(8, 40)), "normal") for v in range(101, 200)}
    under = max(v for v, g in gaps.items() if g < rule.RULE.value_min)
    over = min(v for v, g in gaps.items() if g >= rule.RULE.value_min)
    assert over == under + 1
    for level, expected in ((under, False), (over, True)):
        report = _group_report(base, _flat(8, levels[level], _block(8, 40) | {(7, 7)}), classes=[["a"], ["b"]])
        assert report["i2"] is expected


def test_i2_a_pair_that_collapses_only_under_one_vision_fails_there_and_only_there():
    a, b = PROTAN_COLLAPSE
    shape = _block(8, 40)
    report = _group_report(_flat(8, a, shape), _flat(8, b, shape | {(7, 7)}))
    assert report["i2"] is False and {f["vision"] for f in report["failing"]["i2"]} == {"protan"}
    assert report["groups"]["g"]["min_dL_by_vision"]["normal"] > rule.RULE.value_min  # greyscale alone would have passed it


def test_i2_measures_the_interior_not_the_outline():
    """A badge that is mostly outline: the outline would halve the gap, the interior mean does not."""
    sheet = syn.ladder_sheet({g: "#28331d" if g in ("e", "d") else "#d9ecf3" for g in syn.GRADES})
    plain = rule.mean_colour(sheet["e"])
    assert plain == pytest.approx(from_hex("#28331d"), abs=1e-9)
    assert rule.mean_colour(sheet["c"]) == pytest.approx(from_hex("#d9ecf3"), abs=1e-9)  # a pip hole changes the outline's share, not the interior colour
    assert rule.mean_colour(syn.badge(syn.OCTAGON, "#28331d")) == plain


# ---- I3 plate contrast ---------------------------------------------------------------------------------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def real_means():
    return {k: mean(t) for k, t in syn.real_tiles().items()}


def test_i3_the_proposed_rim_passes_against_every_real_terrain_tile(real_means):
    report = rule.evaluate_sheet({}, {}, {"location": syn.plate("#9ea4b6")}, real_means)
    assert report["i3"] is True and len(real_means) == 23
    worst = min(w["dL"] for w in report["plates"]["location"]["closest_by_vision"].values())
    assert 18.0 <= worst < 18.3  # measured: the closest tile is snow, in every vision


def test_i3_a_low_contrast_plate_and_a_near_black_outline_fail(real_means):
    dark = rule.evaluate_sheet({}, {}, {"p": syn.plate(syn.OUTLINE)}, real_means)
    assert dark["i3"] is False and {f["tile"] for f in dark["failing"]["i3"]} >= {"terrain.floor"}
    low = rule.evaluate_sheet({}, {}, {"p": syn.plate("#4a5060")}, real_means)
    assert low["i3"] is False and low["result"] == "FAIL"


def test_i3_a_rim_that_collapses_only_under_one_vision_fails_there_and_only_there():
    """Rim #d04030 against a tile of #2a5070: the L* gap is 15.9 in normal vision (above 12) but 6.0 under protanopia."""
    report = rule.evaluate_sheet({}, {}, {"p": syn.plate("#d04030")}, {"t": from_hex("#2a5070")})
    assert report["i3"] is False and {f["vision"] for f in report["failing"]["i3"]} == {"protan"}
    assert report["plates"]["p"]["closest_by_vision"]["normal"]["dL"] > rule.RULE.plate_min


def test_i3_boundary_of_the_threshold_on_one_planted_tile():
    tile = {"t": from_hex("#808080")}
    levels = [f"#{v:02x}{v:02x}{v:02x}" for v in range(256)]
    gap = {v: abs(rule.lightness(from_hex(levels[v]), "normal") - rule.lightness(tile["t"], "normal")) for v in range(128, 256)}
    under = max(v for v, g in gap.items() if g < rule.RULE.plate_min)
    over = under + 1
    assert gap[over] >= rule.RULE.plate_min
    for level, expected in ((under, False), (over, True)):
        assert rule.evaluate_sheet({}, {}, {"p": syn.plate(levels[level], fill=levels[level])}, tile)["i3"] is expected


# ---- the whole rule ------------------------------------------------------------------------------------------------------------------------------------------------------------------


def test_the_mock_ladder_built_from_the_best_palette_ladder_passes_and_todays_chips_fail(real_means):
    gap, picked = syn.best_ladder()
    assert gap >= 8.7 and len(picked) == 8
    sheet = syn.ladder_sheet(dict(zip(syn.GRADES, picked, strict=True)))
    ok = rule.evaluate_sheet(sheet, {"tiers": syn.LADDER_CLASSES}, {}, real_means)
    assert ok["result"] == "PASS" and ok["groups"]["tiers"]["pairs"] == 28
    chips = syn.ladder_sheet(dict(syn.TODAY_CHIPS))
    bad = rule.evaluate_sheet(chips, {"tiers": syn.LADDER_CLASSES}, {}, real_means)
    assert bad["i1"] is True and bad["i2"] is False  # today's colour-only grades have the shapes of the ladder here but differ by hue, not value


def test_buff_and_debuff_frames_of_different_shape_pass_i1_and_a_recoloured_pair_does_not():
    buff, debuff = syn.frame(syn._disc(7), "#48b858"), syn.frame(syn._triangle_down(), "#d04030")
    assert rule.evaluate_sheet({"buff": buff, "debuff": debuff}, {"status": [["buff"], ["debuff"]]}, {}, {})["i1"] is True
    twin = syn.frame(syn._disc(7), "#d04030")
    assert rule.evaluate_sheet({"buff": buff, "debuff": twin}, {"status": [["buff"], ["debuff"]]}, {}, {})["i1"] is False


def test_the_rule_is_deterministic(real_means):
    sheet = syn.ladder_sheet(dict(zip(syn.GRADES, syn.best_ladder()[1], strict=True)))
    first = rule.evaluate_sheet(sheet, {"tiers": syn.LADDER_CLASSES}, {"p": syn.plate("#9ea4b6")}, real_means)
    second = rule.evaluate_sheet(sheet, {"tiers": syn.LADDER_CLASSES}, {"p": syn.plate("#9ea4b6")}, real_means)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_the_rule_constants_are_the_users_answers():
    assert rule.RULE == rule.Thresholds(shape_min={8: 3, 16: 6, 24: 8}, value_min=6.0, plate_min=12.0) and VISIONS == ("normal", "protan", "deutan", "tritan")


def test_off_palette_pixels_are_reported_not_ruled():
    palette = rule.committed_palette(ip.PALETTE_FILE)
    sprite = _flat(8, "#123456", _block(8, 10))
    report = rule.evaluate_sheet({"x": sprite}, {}, {}, {}, palette=palette)
    assert report["off_palette_pixels"] == {"x": 10} and report["result"] == "PASS"
