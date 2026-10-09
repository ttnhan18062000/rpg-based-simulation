"""The whole-set colour-vision rule (AM5-S in `docs/assets/pilot_terrain_m5_criteria.md`) on synthetic input, plus the structure of the committed inputs.
The verdict on the real set is recorded by `python -m visual_assets.review.set_colour_vision`, never asserted here (a test must not decide the result)."""

from __future__ import annotations

import pytest

from visual_assets.review import pilot_colour_vision as pilot
from visual_assets.review import set_colour_vision as sv

A, B = "terrain.a", "terrain.b"


def flat(colour: str) -> sv.Tile:
    return [pilot.from_hex(colour)] * 256


def textured(base: str, other: str) -> sv.Tile:
    return [pilot.from_hex(base) if i % 2 else pilot.from_hex(other) for i in range(256)]


def pair_row(report: dict) -> dict:
    return report["pair_table"][0]


def test_rule_constants_are_the_approved_ones():
    assert (sv.TOLERANCE, sv.FLOOR, sv.TEXTURE_MIN) == (2.0, 10.0, 2.0)


def test_tiles_equal_to_their_fills_pass_with_wording_same():
    fills = {A: "#1b3a1b", B: "#3a3420"}
    report = sv.evaluate_set({k: flat(c) for k, c in fills.items()}, fills)
    assert report["result"] == "PASS" and report["wording"] == "same" and report["tiles_below_texture"] == [A, B]
    assert (report["pairs"], report["pair_visions"]) == (1, 4)
    assert all(pair_row(report)[v]["margin"] == 0.0 for v in pilot.VISIONS)


def test_a_known_close_pair_fails_s1_and_a_known_far_pair_passes():
    fills = {A: "#1b3a1b", B: "#c8d8e8"}  # far apart as fills
    far = sv.evaluate_set({A: flat(fills[A]), B: flat(fills[B])}, fills)
    assert far["result"] == "PASS" and far["failing_pair_visions"] == []
    near = sv.evaluate_set({A: flat(fills[A]), B: flat("#1d3c1d")}, fills)  # B's tile drifted onto A's colour
    assert near["result"] == "FAIL" and near["wording"] == "worse"
    assert {f["vision"] for f in near["failing_pair_visions"]} == set(pilot.VISIONS)  # every vision is looped over, each named
    assert all(f["margin"] < -sv.TOLERANCE and f["dE_tile"] < sv.FLOOR for f in near["failing_pair_visions"])


def test_the_margin_is_two_and_not_less():
    fills = {A: "#2a2a3a", B: "#323238"}  # close fills: the 10 dE floor cannot rescue either case
    fill_a, fill_b = pilot.from_hex(fills[A]), pilot.from_hex(fills[B])
    base = pilot.delta_e(fill_a, fill_b, "normal")
    assert base < sv.FLOOR

    def drifted_to(target: float) -> pilot.Rgb:
        """B's colour moved along the line towards A until its distance from A is `target` (normal vision)."""
        left, right = 0.0, 1.0
        for _ in range(60):
            mid = (left + right) / 2
            colour = tuple(fill_b[i] + (fill_a[i] - fill_b[i]) * mid for i in range(3))
            left, right = (mid, right) if pilot.delta_e(fill_a, colour, "normal") > target else (left, mid)  # type: ignore[arg-type]
        return tuple(fill_b[i] + (fill_a[i] - fill_b[i]) * left for i in range(3))  # type: ignore[return-value]

    ok = sv.evaluate_set({A: flat(fills[A]), B: [drifted_to(base - 1.5)] * 256}, fills)
    bad = sv.evaluate_set({A: flat(fills[A]), B: [drifted_to(base - 2.5)] * 256}, fills)
    assert pair_row(ok)["normal"]["s1"] and not pair_row(bad)["normal"]["s1"]


def test_two_tiles_at_least_ten_apart_pass_even_when_the_fills_were_further_apart():
    fills = {A: "#000000", B: "#ffffff"}  # dE_fill is ~100
    report = sv.evaluate_set({A: flat("#000000"), B: flat("#808080")}, fills)  # dE_tile ~53: far more than 10, far less than 100 - 2
    row = pair_row(report)["normal"]
    assert row["dE_tile"] >= sv.FLOOR and row["dE_tile"] < row["dE_fill"] - sv.TOLERANCE and row["s1"]
    assert report["result"] == "PASS"


def test_texture_below_two_is_reported_and_above_two_is_not():
    fills = {A: "#1b3a1b", B: "#3a3420"}
    report = sv.evaluate_set({A: textured("#1b3a1b", "#2f6b2f"), B: flat(fills[B])}, fills)
    assert report["tiles_below_texture"] == [B] and not report["s2"] and report["wording"] == "same"
    both = sv.evaluate_set({A: textured("#1b3a1b", "#2f6b2f"), B: textured("#3a3420", "#6a5a30")}, fills)
    assert both["s2"] and both["tiles_below_texture"] == []


def test_the_report_is_deterministic_and_forest_variants_are_not_part_of_the_verdict():
    fills = {sv.FOREST_KEY: "#1b3a1b", B: "#3a3420"}
    tiles = {sv.FOREST_KEY: textured("#1b3a1b", "#2f6b2f"), B: textured("#3a3420", "#6a5a30")}
    variants = {"bush": flat("#3a3420")}  # identical to B: would fail S1 if it were judged
    first = sv.evaluate_set(tiles, fills, variants)
    assert first == sv.evaluate_set(tiles, fills, variants)
    assert first["result"] == "PASS" and set(first["forest_variants"]) == {"bush"}


def test_the_tile_and_fill_sets_must_match():
    with pytest.raises(AssertionError):
        sv.evaluate_set({A: flat("#101010")}, {A: "#101010", B: "#202020"})


def test_the_committed_inputs_cover_every_terrain_exactly_once_and_forest_is_read_from_its_adopted_slots():
    codes = sv.draft_keys()
    assert len(codes) == 23 and sorted(codes.values()) == list(range(23))
    drafts = sv.draft_tiles("terrain-v1")
    assert set(drafts) == set(codes) - {sv.FOREST_KEY}
    assert all(len(t) == 256 for t in drafts.values())
    forest = sv.adopted_forest()
    assert set(forest) == {"plain", "bush", "tree"} and all(len(t) == 256 for t in forest.values())
    assert set(pilot.tile_fills()) >= set(codes.values())


def test_the_live_report_has_every_pair_and_vision():
    report = sv.live_set()
    assert (report["tiles"], report["pairs"], report["pair_visions"]) == (23, 253, 1012)
    assert report["result"] in {"PASS", "FAIL"} and set(report["forest_variants"]) == {"bush", "tree"}
