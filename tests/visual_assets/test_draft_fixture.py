"""The frontend's committed fixture draft set export equals a fresh `draft export` of the fixture set (pure Python, no Aseprite).

The only link between `visual_assets` and `frontend/` is this file-level copy: no import either way. The page shows `draft_set_hash`, so its exactness matters.
"""

from __future__ import annotations

import json

from tests.visual_assets.store import draft_fixture as fx
from visual_assets.store.contracts import DraftPreviewManifest, parse_record

REGENERATE = "regenerate the committed copy: `python -m tests.visual_assets.store.draft_fixture --write`"


def test_the_committed_fixture_equals_a_fresh_export_of_the_fixture_set(tmp_path):
    fresh = tmp_path / "draft"
    fx.export_fixture(fresh)
    assert fx.COMMITTED.is_dir() and fx.same_tree(fresh, fx.COMMITTED), f"the draft fixture differs from a fresh export; {REGENERATE}"


def test_the_committed_manifest_is_a_draft_preview_manifest_for_the_fixture_set_with_the_three_real_forest_slots():
    data = (fx.COMMITTED / "draft_preview_manifest.json").read_bytes()
    manifest = parse_record(DraftPreviewManifest, data)
    assert manifest.set_id == fx.SET_ID and manifest.draft_set_hash.startswith("sha256:")
    assert [(e.visual_key, e.detail) for e in manifest.entries] == [
        ("terrain.desert", None), ("terrain.forest", None), ("terrain.forest", "bush"), ("terrain.forest", "tree"),
        ("terrain.grassland", None), ("terrain.mountain", None), ("terrain.swamp", None),
    ]
    assert json.loads(data)["details"] == [{"default": "plain", "values": ["plain", "bush", "tree"], "visual_key": "terrain.forest"}]
