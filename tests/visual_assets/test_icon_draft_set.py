"""The drawn icon key set `icons-key-v1` (`TCK-20261006-VISUAL-ASSETS-ICON-KEY-DRAFT-SET`): structure, palette, sizes and the arithmetic of the read-back.

Never asserts the sheet rule's VERDICT on the art (a test must not decide the result on art, as with AM5-S): the verdict is recorded by `python -m tests.visual_assets.icon_draft_set` and shown on the
preview page. What is asserted here are facts about the drawn set that the style guide and the palette make checkable.
"""

from __future__ import annotations

import json
import re

import pytest

from tests.visual_assets import icon_draft_set as ds
from tests.visual_assets import icon_palette, icon_sheet_rule as rule
from visual_assets.store.catalog.registry import load_registry


@pytest.fixture(scope="module")
def sprites():
    return ds.draft_sprites()


def test_the_set_holds_exactly_the_14_registered_icon_keys_and_nothing_adopted():
    entries = json.loads((ds.DRAFTS / ds.SET_ID / "draft_set.json").read_text())["entries"]
    assert sorted(e["visual_key"] for e in entries) == sorted(ds.SIZES) and len(entries) == 14
    registry = load_registry()
    assert sorted(k for k in registry.keys if k.startswith("icon.")) == sorted(ds.SIZES)
    assert all(registry.keys[k].optional for k in ds.SIZES)  # nothing in the registry needs these drafts; a missing image leaves today's fallback


def test_every_draft_has_the_size_its_registry_description_states(sprites):
    registry = load_registry()
    for key, size in ds.SIZES.items():
        assert (sprites[key].width, sprites[key].height) == (size, size)
        assert f"{size}x{size}" in registry.keys[key].description


def test_every_pixel_of_the_set_is_a_palette_colour(sprites):
    palette = rule.committed_palette(icon_palette.PALETTE_FILE)
    assert {k: rule.off_palette(s, palette) for k, s in sprites.items() if rule.off_palette(s, palette)} == {}


def test_lint_has_no_warning_and_the_colour_budget_holds(sprites):
    for key, report in ds.lint_summary(sprites).items():
        assert report["warnings"] == [], key
        assert report["colors"] <= report["color_budget"], key


def test_the_marker_glyph_keeps_the_12x12_live_area_and_a_2px_margin(sprites):
    """Planner ruling, 2026-10-06: the glyph's live area is 12x12 centred with a 2 px margin on its 16x16 canvas, so the plate's rim stays visible all round."""
    assert ds.glyph_live_area(sprites["icon.marker.enemy_camp"]) == {"bbox": [2, 2, 13, 13], "margin": [2, 2, 2, 2]}


def test_the_plate_fills_its_canvas_with_cut_corners_and_one_rim_colour(sprites):
    plate = sprites["icon.plate.location"]
    assert len(rule.silhouette(plate)) == 16 * 16 - 4
    assert rule.rim_colours(plate) == ["#9ea4b6"]  # I3 measures every rim colour: one mid-light colour only


def test_panel_icons_and_markers_use_the_dark_outline_and_the_plate_does_not(sprites):
    outline = "#0e1018"
    for key in ("icon.marker.enemy_camp", "icon.building.blacksmith", "icon.class.warrior", *[f"icon.tier.{t}" for t in ds.TIERS]):
        assert outline in rule.rim_colours(sprites[key]), key
    assert outline not in rule.rim_colours(sprites["icon.plate.location"])


def test_e_and_d_share_a_silhouette_and_every_other_tier_pair_differs_in_shape(sprites):
    """The user's ruling: E and D may share a silhouette. Every other pair differs by at least their own count, and the true counts are what the rule reads."""
    shapes = {t: rule.silhouette(sprites[f"icon.tier.{t}"]) for t in ds.TIERS}
    assert shapes["e"] == shapes["d"]
    others = [(a, b) for i, a in enumerate(ds.TIERS) for b in ds.TIERS[i + 1 :] if (a, b) != ("e", "d")]
    assert all(shapes[a] != shapes[b] for a, b in others)


def test_the_read_back_is_deterministic_and_the_evaluation_runs():
    first, second = ds.evaluate_draft_set(), ds.evaluate_draft_set()
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert first["set_id"] == ds.SET_ID and re.fullmatch(r"sha256:[0-9a-f]{64}", first["draft_set_hash"])
    assert first["groups"]["tiers"]["pairs"] == 28 and first["groups"]["status"]["pairs"] == 1
    assert {"i1", "i2", "i3", "result"} <= set(first)  # the verdict is read from the recorded evaluation, never asserted here


def test_a_preview_whose_size_is_not_the_declared_one_is_refused():
    good = next((ds.DRAFTS / ds.SET_ID).glob("in-*/preview.png")).read_bytes()
    with pytest.raises(AssertionError):
        ds.sprite_from_preview(good, 4)
