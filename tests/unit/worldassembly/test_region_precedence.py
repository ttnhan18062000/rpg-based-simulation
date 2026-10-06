"""LOC-08 (owner decision 13): authored region precedence, resolved into the region-list order.

``order_regions`` turns a composition's declarations into the total order the resolved world carries as its
region-list order (highest precedence first). Every consumer reads that one order: the runtime lookup
(``resolve_region_among``), terrain paint (``WorldCompiler``) and the hazard a tile applies.
"""
from __future__ import annotations

import glob
from types import SimpleNamespace

import pytest
import yaml

from src.core.state import RegionState
from src.core.region_resolution import resolve_region_among
from src.worldassembly.region_precedence import order_regions
from src.worldbuilding.schema import InvalidWorldSpecError, RegionSpec


def _r(rid, bounds):
    return RegionSpec(id=rid, type="wilderness", bounds=bounds)


def _decl(winner, *over):
    return SimpleNamespace(winner=winner, over=list(over))


def _ids(ordered):
    return [r.id for r in ordered]


# ---- 3a: an undeclared nested region beats its container ----------------------------------


def test_a_nested_region_beats_its_container_with_no_declaration():
    forest, town = _r("near_forest", (45, 10, 90, 55)), _r("trading_hometown", (45, 10, 80, 45))
    ordered, report = order_regions([forest, town], [])
    assert _ids(ordered) == ["trading_hometown", "near_forest"]
    assert report.containment_resolutions == [("trading_hometown", "near_forest")]
    assert report.undeclared_partial_overlaps == []


# ---- declared precedence ---------------------------------------------------------------------


def test_a_declared_winner_moves_ahead_of_its_losers_and_nothing_else_moves():
    road, forest, den, hometown = (_r("bandit_road", (40, 40, 100, 60)), _r("near_forest", (45, 10, 90, 55)),
                                   _r("wolf_den", (70, 30, 105, 70)), _r("hometown", (10, 10, 40, 40)))
    ordered, _ = order_regions([hometown, forest, den, road],
                               [_decl("bandit_road", "near_forest", "wolf_den"), _decl("wolf_den", "near_forest")])
    assert _ids(ordered) == ["hometown", "bandit_road", "wolf_den", "near_forest"]


def test_unconstrained_regions_keep_their_declaration_order():
    a, b, c = _r("a", (0, 0, 5, 5)), _r("b", (10, 0, 15, 5)), _r("c", (20, 0, 25, 5))
    ordered, report = order_regions([a, b, c], [])
    assert _ids(ordered) == ["a", "b", "c"] and report.undeclared_partial_overlaps == []


# ---- 3b / 3c ------------------------------------------------------------------------------------


def test_an_undeclared_partial_overlap_keeps_declaration_order_and_is_reported():
    road, den = _r("bandit_road", (40, 40, 100, 60)), _r("wolf_den", (70, 30, 105, 70))
    ordered, report = order_regions([road, den], [])
    assert _ids(ordered) == ["bandit_road", "wolf_den"]
    assert [(a, b) for a, b, _ in report.undeclared_partial_overlaps] == [("bandit_road", "wolf_den")]
    assert report.undeclared_partial_overlaps[0][2] > 0


def test_a_region_that_owns_no_tile_is_an_error():
    outer, inner = _r("outer", (0, 0, 50, 50)), _r("inner", (10, 10, 20, 20))
    with pytest.raises(InvalidWorldSpecError, match="inner"):
        order_regions([outer, inner], [_decl("outer", "inner")])  # the container declared over what it covers entirely
    with pytest.raises(InvalidWorldSpecError, match="twin_b"):
        order_regions([_r("twin_a", (0, 0, 9, 9)), _r("twin_b", (0, 0, 9, 9))], [])  # identical bounds: 3b gives all to the first


def test_owned_tiles_are_reported_so_a_thin_remainder_is_visible():
    forest, town = _r("near_forest", (45, 10, 90, 55)), _r("trading_hometown", (45, 10, 80, 45))
    _, report = order_regions([forest, town], [])
    assert report.owned_tiles["trading_hometown"] == 36 * 36  # inclusive tiles, owns all of itself
    assert report.owned_tiles["near_forest"] == 46 * 46 - 36 * 36


@pytest.mark.parametrize("bad, match", [
    ([_decl("ghost", "a")], "unknown region 'ghost'"),
    ([_decl("a", "ghost")], "unknown region 'ghost'"),
    ([_decl("a", "a")], "over itself"),
    ([_decl("a", "b"), _decl("b", "a")], "cycle"),
])
def test_bad_declarations_are_rejected(bad, match):
    with pytest.raises(InvalidWorldSpecError, match=match):
        order_regions([_r("a", (0, 0, 9, 9)), _r("b", (20, 0, 29, 9))], bad)


# ---- the order IS what the runtime lookup reads --------------------------------------------------


def test_the_lookup_reads_the_resolved_order():
    forest, town = _r("near_forest", (45, 10, 90, 55)), _r("trading_hometown", (45, 10, 80, 45))
    ordered, _ = order_regions([forest, town], [])
    states = [RegionState(id=r.id, name=r.id, bounds=tuple(r.bounds)) for r in ordered]
    assert resolve_region_among(states, 60, 20).id == "trading_hometown"  # nested town, not its container
    assert resolve_region_among(states, 85, 50).id == "near_forest"      # outside the town


# ---- the corpus: every ratified pair holds in every resolved world ----------------------------

RATIFIED = [("trading_hometown", "near_forest"), ("wolf_den", "near_forest"), ("bandit_road", "near_forest"),
            ("bandit_road", "wolf_den"), ("goblin_camp", "bandit_road"), ("goblin_camp", "wolf_den"),
            ("trading_hometown", "bandit_road"), ("trading_hometown", "wolf_den"),
            ("orc_stronghold", "swamp_border_territory"), ("survivor_outpost", "near_forest"),
            ("haunted_battlefield", "mountain_pass_zone"), ("haunted_battlefield", "river_ford"),
            ("haunted_battlefield", "goblin_camp"), ("old_mine", "sacred_grove"), ("old_mine", "deep_forest")]


def _overlap(a, b):
    w = min(a[2], b[2]) - max(a[0], b[0]) + 1
    h = min(a[3], b[3]) - max(a[1], b[1]) + 1
    return w > 0 and h > 0


def test_every_ratified_precedence_pair_holds_in_every_resolved_world():
    checked = 0
    for path in sorted(glob.glob("data/worlds/*/resolved/world.resolved.yaml")):
        regions = yaml.safe_load(open(path))["regions"]
        index = {r["id"]: i for i, r in enumerate(regions)}
        bounds = {r["id"]: r["bounds"] for r in regions}
        for win, lose in RATIFIED:
            if win in index and lose in index and _overlap(bounds[win], bounds[lose]):
                assert index[win] < index[lose], f"{path}: {win} must precede {lose}"
                checked += 1
    assert checked >= 50  # 53 declared (world, pair) instances at implementation; guards against a vacuous pass


def test_every_resolved_world_has_every_region_owning_a_tile():
    for path in sorted(glob.glob("data/worlds/*/resolved/world.resolved.yaml")):
        regions = [_r(r["id"], r["bounds"]) for r in yaml.safe_load(open(path))["regions"]]
        _, report = order_regions(regions, [])  # order is already resolved; 3c must hold on it as-is
        assert all(n > 0 for n in report.owned_tiles.values()), path
