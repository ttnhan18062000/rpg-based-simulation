"""The frontend's committed copy of the pilot terrain export equals a fresh `export-runtime` of `pilot/rc-0003` (pure Python, no Aseprite).

The only link between `visual_assets` and `frontend/` is this file-level copy (`TCK-20261004-VISUAL-ASSETS-M5-GAP-CLOSURE`): no import either way.
"""

from __future__ import annotations

import filecmp
import json
from pathlib import Path

from visual_assets.store.runtime_export import export_runtime

REPO = Path(__file__).resolve().parents[2]
COMMITTED = REPO / "frontend" / "src" / "visualAssets" / "__fixtures__" / "pilot"
REGENERATE = (
    "regenerate the committed pilot export: `python -m visual_assets.store export-runtime --catalog-id pilot --release-id rc-0003 --out /tmp/pilot_export`, "
    "then replace the files in frontend/src/visualAssets/__fixtures__/pilot/ with its content"
)


def test_the_committed_pilot_export_equals_a_fresh_export_of_the_release(tmp_path):
    fresh = tmp_path / "export"
    export_runtime("pilot", "rc-0003", fresh)
    names = sorted(p.name for p in fresh.iterdir())
    committed = sorted(p.name for p in COMMITTED.iterdir())
    assert committed == names, f"the pilot fixture's files differ from a fresh export ({committed} vs {names}); {REGENERATE}"
    for name in names:
        assert filecmp.cmp(fresh / name, COMMITTED / name, shallow=False), f"{name} differs from a fresh export; {REGENERATE}"


def test_the_pilot_export_holds_the_three_declared_slots_of_terrain_forest():
    manifest = json.loads((COMMITTED / "runtime_manifest.json").read_text())
    assert [(e["visual_key"], e["detail"], e["family"], e["width"], e["height"]) for e in manifest["entries"]] == [
        ("terrain.forest", "bush", "terrain", 16, 16), ("terrain.forest", "plain", "terrain", 16, 16), ("terrain.forest", "tree", "terrain", 16, 16),
    ]
    # the declared order is what the client picks over (the approved 64 x 64 spread was computed for [plain, bush, tree])
    assert manifest["details"] == [{"visual_key": "terrain.forest", "values": ["plain", "bush", "tree"], "default": "plain"}]
    assert manifest["catalog_id"] == "pilot" and manifest["release_id"] == "rc-0003"


def test_rc_0003_lists_exactly_the_entries_of_rc_0002_so_only_the_registry_moved():
    """`pilot/rc-0003` was assembled only because registering the other 22 terrain keys changed the registry hash (`TCK-20261004-VISUAL-ASSETS-TERRAIN-DRAFT-SET`,
    planner decision A). Its entries must be the same slots, artifact ids and pixel hashes as rc-0002's, so "the release content is unchanged" is a checked fact."""
    base = REPO / "visual_assets" / "catalog" / "manifests" / "candidates" / "pilot"
    old, new = (json.loads((base / f"{rc}.json").read_text()) for rc in ("rc-0002", "rc-0003"))
    assert new["entries"] == old["entries"] and len(new["entries"]) == 3
    assert new["registry_hash"] != old["registry_hash"] and new["release_id"] == "rc-0003" and new["catalog_id"] == old["catalog_id"]
