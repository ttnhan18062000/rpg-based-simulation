"""The icon set v2 groups and the 24x24 shape threshold (`TCK-20261007-VISUAL-ASSETS-ICON-V2-SHEET-RULE-GROUPS`), on planted sprites: arithmetic only, never a verdict on art (there is none yet)."""

from __future__ import annotations

import pytest

from tests.visual_assets import icon_sheet_rule as rule
from tests.visual_assets import icon_v2_groups as g
from tests.visual_assets import icon_v2_keys as v2
from tests.visual_assets.icon_draft_set import SIZES as V1_SIZES
from tests.visual_assets.pilot_colour_vision import from_hex


def _flat(side: int, colour: str, shape: set) -> rule.Sprite:
    r, gr, b = (round(c * 255) for c in from_hex(colour))
    return rule.Sprite(side, side, tuple((r, gr, b, 255) if (i % side, i // side) in shape else (0, 0, 0, 0) for i in range(side * side)))


def _block(side: int, n: int) -> set:
    return {(i % side, i // side) for i in range(n)}


def _pair_report(side: int, a_shape: set, b_shape: set, group: str, colours=("#555b73", "#555b73")):
    icons = {"a": _flat(side, colours[0], a_shape), "b": _flat(side, colours[1], b_shape)}
    return rule.evaluate_sheet(icons, {group: [["a"], ["b"]]}, {}, {}, shape_only=g.SHAPE_ONLY)


def test_the_groups_are_well_formed_and_cover_every_v2_key_once():
    assert {k: sum(len(c) for c in v) for k, v in g.GROUPS.items()} == {"rarity": 3, "badges": 11, "locations": 6, "buildings": 6, "classes": 4, "items": 6}
    sizes = {**V1_SIZES, **v2.SIZES}
    for name, classes in g.GROUPS.items():
        members = [k for c in classes for k in c]
        assert len(set(members)) == len(members), name
        assert {sizes[k] for k in members} == {g.SIZE[name]}, name  # one size per group
    placed = [k for name in ("rarity", "locations", "buildings", "classes", "items") for c in g.GROUPS[name] for k in c if k in v2.SIZES]
    assert sorted(placed) == v2.KEYS  # every v2 key is in exactly one of the five subject and rarity groups
    assert g.SHAPE_ONLY == {"badges", "locations", "buildings", "classes", "items"} and "rarity" not in g.SHAPE_ONLY


def test_the_tier_classes_keep_e_and_d_together_inside_the_badge_group():
    classes = g.GROUPS["badges"]
    assert ["icon.tier.e", "icon.tier.d"] in classes and len(classes) == 7 + 3


@pytest.mark.parametrize("group", ["rarity", "badges", "locations", "buildings", "classes", "items"])
def test_a_recoloured_only_pair_fails_i1_in_every_group_size(group):
    side = g.SIZE[group]
    shape = _block(side, side * 3)
    report = _pair_report(side, shape, shape, group, ("#555b73", "#e8c040"))
    assert report["i1"] is False and report["failing"]["i1"][0]["shape_px"] == 0


@pytest.mark.parametrize(("need", "ok"), [(8, True), (7, False)])
def test_i1_boundary_at_24x24_is_the_users_8_px(need, ok):
    base = _block(24, 100)
    extra = [(x, y) for y in range(24) for x in range(24) if (x, y) not in base][:need]
    report = _pair_report(24, base, base | set(extra), "buildings")
    assert report["i1"] is ok and rule.RULE.shape_min[24] == 8


def test_a_canvas_size_without_a_threshold_still_raises():
    with pytest.raises(KeyError):
        _pair_report(32, _block(32, 10), _block(32, 300), "buildings")


def test_shape_only_groups_skip_i2_and_say_so_while_the_rarity_group_keeps_i2():
    side = 24
    a, b = _block(side, 100), _block(side, 300)  # clearly different silhouettes, identical colour (zero value gap)
    shape_only = _pair_report(side, a, b, "buildings")
    assert shape_only["i1"] and shape_only["i2"] and shape_only["result"] == "PASS"
    assert shape_only["groups"]["buildings"]["value_checked"] is False and shape_only["groups"]["buildings"]["min_dL_by_vision"] == {}
    # the same pair in a group that is NOT shape-only fails I2 in every vision
    icons = {"a": _flat(side, "#555b73", a), "b": _flat(side, "#555b73", b)}
    full = rule.evaluate_sheet(icons, {"rarity": [["a"], ["b"]]}, {}, {}, shape_only=g.SHAPE_ONLY)
    assert full["i2"] is False and full["groups"]["rarity"]["value_checked"] is True and {f["vision"] for f in full["failing"]["i2"]} == set(rule.VISIONS)


def test_a_rarity_badge_with_a_tier_silhouette_fails_i1_in_the_badge_group_and_a_distinct_one_passes():
    from tests.visual_assets.icon_sheet_synthetic import LADDER_SHAPES

    tier = LADDER_SHAPES["s"]
    icons = {"icon.tier.s": _flat(8, "#9ea4b6", tier), "icon.rarity.rare": _flat(8, "#a78bfa", tier)}
    groups = {"badges": [["icon.tier.s"], ["icon.rarity.rare"]]}
    assert rule.evaluate_sheet(icons, groups, {}, {}, shape_only=g.SHAPE_ONLY)["i1"] is False
    icons["icon.rarity.rare"] = _flat(8, "#a78bfa", LADDER_SHAPES["e"])
    assert rule.evaluate_sheet(icons, groups, {}, {}, shape_only=g.SHAPE_ONLY)["i1"] is True


def test_the_existing_key_set_thresholds_are_unchanged_for_8_and_16():
    assert (rule.RULE.shape_min[8], rule.RULE.shape_min[16], rule.RULE.value_min, rule.RULE.plate_min) == (3, 6, 6.0, 12.0)
