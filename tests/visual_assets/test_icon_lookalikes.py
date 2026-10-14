"""The whole-sheet look-alike report finds planted twins across families and is deterministic (`TCK-20261008-VISUAL-ASSETS-ICON-RECOGNISABILITY-CHECKS`). It decides nothing about the art."""

from __future__ import annotations

from visual_assets.review import icon_lookalikes as la
from visual_assets.review import icon_sheet_rule as rule

INK = {"#": "#102030"}


def sprite(rows: list[str]) -> rule.Sprite:
    return rule.from_rows(rows, INK)


BLADE = [
    "..........#.",
    ".........##.",
    "........##..",
    ".......##...",
    "......##....",
    ".#...##.....",
    "..#.##......",
    "...##.......",
    "..####......",
    ".##..#......",
    "##....#.....",
    "............",
]
BLOCK = ["############"] * 12


def test_the_same_shape_at_another_size_and_family_is_a_zero_distance_twin():
    big = rule.Sprite(24, 24, tuple(p for row in range(24) for p in sprite(BLADE).rgba[(row // 2) * 12 : (row // 2) * 12 + 12] for _ in (0, 1)))
    out = la.report({"icon.item.weapon": big, "icon.class.rogue": sprite(BLADE), "icon.building.inn": sprite(BLOCK)})
    pair = next(p for p in out["close_pairs"] if {p["a"], p["b"]} == {"icon.item.weapon", "icon.class.rogue"})
    assert pair["xor_px"] == 0 and pair["cross_family"] is True
    assert out["closest_cross_family_pairs"][0]["xor_px"] == 0


def test_a_different_shape_is_not_close_and_the_nearest_list_is_ordered():
    out = la.report({"icon.item.weapon": sprite(BLADE), "icon.building.inn": sprite(BLOCK), "icon.class.rogue": sprite(BLADE)})
    assert all({p["a"], p["b"]} != {"icon.building.inn", "icon.item.weapon"} for p in out["close_pairs"])
    near = out["nearest"]["icon.item.weapon"]
    assert [n["key"] for n in near] == ["icon.class.rogue", "icon.building.inn"] and near[0]["xor_px"] <= near[1]["xor_px"]


def test_a_planted_near_twin_one_blade_pixel_off_is_still_close():
    nudged = list(BLADE)
    nudged[3] = ".......###.."  # one extra pixel inside the bounding box, so the shape is the same but for that pixel
    out = la.report({"icon.item.weapon": sprite(BLADE), "icon.class.rogue": sprite(nudged)})
    assert 0 < out["close_pairs"][0]["xor_px"] <= la.CLOSE


def test_the_report_is_deterministic_and_covers_all_36_icons():
    sprites = la.all_icon_sprites()
    assert len(sprites) == 36
    assert la.report(sprites) == la.report(sprites)
    assert set(la.report(sprites)["nearest"]) == set(sprites)


def test_an_empty_sprite_has_an_empty_silhouette_and_does_not_crash():
    empty = rule.Sprite(4, 4, tuple((0, 0, 0, 0) for _ in range(16)))
    assert la.normalised(empty) == frozenset()
