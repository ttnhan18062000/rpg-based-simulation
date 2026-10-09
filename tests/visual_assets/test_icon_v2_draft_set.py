"""Icon set v2 as drawn (`TCK-20261007-VISUAL-ASSETS-ICON-V2-DRAFT-SET`): the draft set `icons-v2` is complete, in the style the owner adopted, and the page's committed copy equals a fresh export.

No test decides the sheet rule's verdict on the art (that is the recorded result of `python -m visual_assets.review.icon_v2_draft_set`): these tests pin what is checkable without judging pixels
(every key drawn at its registered size, own palette only, lint clean, live areas, a result file equal to a fresh evaluation, a copy equal to a fresh export modulo `registry_hash`).
"""

from __future__ import annotations

import json
import shutil

from tests.visual_assets import closed_draft_fixture as cdf
from visual_assets.review import icon_draft_fixture as fx
from visual_assets.review import icon_v2_draft_set as d2
from visual_assets.review import icon_v2_groups as groups
from visual_assets.review import icon_v2_keys as v2
from visual_assets.store.contracts import DraftPreviewManifest, parse_record

REGENERATE = "regenerate the committed copy: `python -m visual_assets.review.icon_draft_fixture --set icons-v2 --write`"


def _fresh(tmp_path):
    out = tmp_path / "fresh"
    fx.export_fresh(out, d2.SET_ID)
    return out


def test_every_v2_key_is_drawn_once_at_its_registered_size():
    sprites = d2.v2_sprites()
    assert sorted(sprites) == sorted(v2.KEYS) and len(sprites) == 22
    for key, sprite in sprites.items():
        assert (sprite.width, sprite.height) == (v2.SIZES[key], v2.SIZES[key]), key


def test_lint_has_no_warning_no_pixel_leaves_the_icons_palette_and_colour_budgets_hold():
    result = d2.evaluate()
    assert not result.get("off_palette_pixels")
    for key, lint in result["lint"].items():
        assert lint["warnings"] == [], key
        assert lint["colors"] <= lint["color_budget"], key


def test_glyphs_and_panel_icons_stay_inside_their_live_areas():
    result = d2.evaluate()
    for key, area in result["glyph_live_area"].items():
        assert min(area["margin"]) >= 2, key
    for key, (x0, y0, x1, y1) in result["panel_live_area"].items():
        assert min(x0, y0, 23 - x1, 23 - y1) >= 2, key


def test_the_recorded_result_covers_every_group_the_owner_asked_for_and_is_current():
    recorded = json.loads((fx.COMMITTED_V2 / fx.RESULT).read_text())
    assert (fx.COMMITTED_V2 / fx.RESULT).read_text() == fx.recorded_result_text_v2()
    assert recorded["set_id"] == "icons-v2" and set(recorded["groups"]) == set(groups.GROUPS)
    assert {g for g, row in recorded["groups"].items() if row["value_checked"]} == {"rarity"}


def test_rarity_badges_keep_their_distance_from_every_tier_silhouette():
    result = d2.evaluate()
    assert set(result["rarity_vs_tier_min_shape_px"]) == set(groups.RARITY_KEYS)
    assert all(d >= 3 for d in result["rarity_vs_tier_min_shape_px"].values())  # the planner's floor of 3 px, measured on the real art


def test_the_committed_copy_equals_a_fresh_export_modulo_the_registry_hash(tmp_path):
    assert cdf.differences(d2.SET_ID, _fresh(tmp_path), fx.COMMITTED_V2, fx.recorded_result_text_v2) == [], REGENERATE


def test_the_manifest_holds_the_22_icons_and_only_adopted_terrain_references():
    manifest = parse_record(DraftPreviewManifest, (fx.COMMITTED_V2 / fx.MANIFEST).read_bytes())
    assert manifest.set_id == "icons-v2"
    icons = [e for e in manifest.entries if e.visual_key.startswith("icon.")]
    assert sorted(e.visual_key for e in icons) == sorted(v2.KEYS) and all(not getattr(e, "adopted", False) for e in icons)
    assert {e.visual_key.split(".")[0] for e in manifest.entries if getattr(e, "adopted", False)} == {"terrain", "border"}


def test_a_flipped_png_byte_in_the_v2_copy_is_caught(tmp_path):
    copy = tmp_path / "copy"
    shutil.copytree(fx.COMMITTED_V2, copy)
    manifest = json.loads((copy / fx.MANIFEST).read_text())
    icon_file = next(e["file"] for e in manifest["entries"] if e["visual_key"] == "icon.rarity.common")
    data = bytearray((copy / icon_file).read_bytes())
    data[-20] ^= 1
    (copy / icon_file).write_bytes(bytes(data))
    assert any(icon_file in p for p in cdf.differences(d2.SET_ID, _fresh(tmp_path), copy, fx.recorded_result_text_v2))
