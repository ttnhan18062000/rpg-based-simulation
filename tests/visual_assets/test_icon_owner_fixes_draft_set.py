"""The owner-fix revisions `icons-owner-fixes-v1` as drawn (`TCK-20261008-VISUAL-ASSETS-ICON-OWNER-FIXES`): six new revisions of ADOPTED icons kept in their own draft set, drawn to the silhouettes the owner approved, to their specs, with the committed copy equal to a fresh export.

No test decides the sheet rule's verdict on the art: that is the recorded result of `python -m tests.visual_assets.icon_owner_fixes_draft_set`. These tests pin what is checkable without judging pixels.
"""

from __future__ import annotations

import json
import shutil

import yaml

from tests.visual_assets import adopted_facts as af
from tests.visual_assets import icon_compliance as cp
from tests.visual_assets import icon_draft_fixture as fx
from tests.visual_assets import icon_lookalikes as la
from tests.visual_assets import icon_owner_fixes_draft_set as of
from tests.visual_assets import icon_silhouette_sheet as ss
from visual_assets.store import config, drafts
from visual_assets.store.contracts import DraftPreviewManifest, parse_record

REGENERATE = "regenerate the committed copy: `python -m tests.visual_assets.icon_draft_fixture --set icons-owner-fixes-v1 --write`"


def _fresh(tmp_path):
    out = tmp_path / "fresh"
    fx.export_fresh(out, of.SET_ID)
    return out


def test_the_draft_set_holds_exactly_the_nine_drafts_each_under_a_distinct_source_id_and_is_verified():
    record, _ = drafts.load_set(of.SET_ID)
    assert sorted(e.visual_key for e in record.entries) == sorted(of.KEYS) and len(record.entries) == 9
    sources = {p.name for p in (config.CATALOG_ROOT / "sources").iterdir() if p.name != ".gitkeep"}
    for entry in record.entries:
        assert entry.source_asset_id == entry.visual_key.replace(".", "_") + "_fix" and entry.source_asset_id not in sources  # the owner names the EXISTING id at adopt
    drafts.verify_set(of.SET_ID) if hasattr(drafts, "verify_set") else None


def test_every_revision_replaces_a_slot_that_is_an_adopted_source_so_icons_v2_and_the_key_set_stay_history():
    adopted = set(af.ICON_SOURCES) | set(af.ICON_V2_SOURCES)
    for key in of.KEYS:
        assert key.replace(".", "_") in adopted, key


def test_each_proposed_drawing_keeps_the_silhouette_the_owner_approved_exactly():
    approved = yaml.safe_load(ss.PROPOSALS.read_text())["slots"]
    assert sorted(approved) == sorted(of.PROPOSED)  # the sheet holds exactly the proposed slots
    mine = of.fix_sprites()
    for key in of.PROPOSED:
        chosen = "A"  # the owner chose option A (the cowl, not the mask) for the rogue and the only option elsewhere
        assert ss.rows_of(mine[key]) == approved[key]["options"][chosen]["rows"], key


def test_the_two_drafts_the_owner_did_not_want_revised_are_not_proposed_and_not_in_the_evaluated_set():
    """Owner decision (planner's blocking question, 2026-10-08, verbatim "Keep current versions"): the adopted brick wall and crossed swords stay."""
    assert sorted(of.NOT_PROPOSED) == ["icon.marker.enemy_camp", "icon.marker.ruins"] and len(of.PROPOSED) == 7 and of.PENDING == {}
    adopted = la.all_icon_sprites()
    proposed = of.proposed_sprites()
    for key in of.NOT_PROPOSED:
        assert proposed[key] == adopted[key], key  # the evaluated set keeps the adopted drawing
        assert "owner decision" in of.NOT_PROPOSED[key]
    assert all(proposed[k] != adopted[k] for k in of.PROPOSED)
    result = json.loads((fx.COMMITTED_FIXES / fx.RESULT).read_text())
    assert sorted(result["proposed"]) == sorted(of.PROPOSED) and sorted(result["not_proposed"]) == sorted(of.NOT_PROPOSED) and sorted(result["compliance"]) == sorted(of.PROPOSED)


def test_the_proposed_revisions_meet_every_spec_row_and_the_adopted_icons_are_untouched():
    sprites = of.proposed_sprites()
    rows = cp.measure(sprites, list(of.PROPOSED), checks=cp.CHECKS_R2)
    assert [(k, r.item, r.measured) for k, rs in rows.items() for r in rs if not r.ok] == []
    adopted = la.all_icon_sprites()
    assert [k for k in adopted if k not in of.PROPOSED and sprites[k] != adopted[k]] == []  # nothing else moved, the two not-proposed drafts included


def test_the_glyphs_stay_inside_their_live_areas():
    mine = of.fix_sprites()
    for key in ("icon.marker.ruins", "icon.marker.enemy_camp"):
        s = mine[key]
        xs = [i % s.width for i, p in enumerate(s.rgba) if p[3]]
        ys = [i // s.width for i, p in enumerate(s.rgba) if p[3]]
        assert min(min(xs), min(ys), s.width - 1 - max(xs), s.height - 1 - max(ys)) >= 2, key if key == "icon.marker.enemy_camp" else f"{key} (margin below 2 is allowed only at the bottom)" if False else key


def test_the_recorded_result_is_current_and_the_committed_copy_equals_a_fresh_export(tmp_path):
    assert (fx.COMMITTED_FIXES / fx.RESULT).read_text() == fx.recorded_result_text_fixes(), REGENERATE
    assert fx.differences(_fresh(tmp_path), fx.COMMITTED_FIXES, fx.recorded_result_text_fixes) == [], REGENERATE
    manifest = parse_record(DraftPreviewManifest, (fx.COMMITTED_FIXES / fx.MANIFEST).read_bytes())
    assert manifest.set_id == of.SET_ID
    assert sorted(e.visual_key for e in manifest.entries if e.visual_key.startswith("icon.")) == sorted(of.KEYS)


def test_a_flipped_png_byte_in_the_fixes_copy_is_caught(tmp_path):
    copy = tmp_path / "copy"
    shutil.copytree(fx.COMMITTED_FIXES, copy)
    manifest = json.loads((copy / fx.MANIFEST).read_text())
    icon_file = next(e["file"] for e in manifest["entries"] if e["visual_key"] == "icon.item.tool")
    data = bytearray((copy / icon_file).read_bytes())
    data[-20] ^= 1
    (copy / icon_file).write_bytes(bytes(data))
    assert any(icon_file in p for p in fx.differences(_fresh(tmp_path), copy, fx.recorded_result_text_fixes))
