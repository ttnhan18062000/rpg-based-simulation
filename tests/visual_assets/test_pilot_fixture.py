"""The frontend's committed copy of the pilot terrain export equals a fresh `export-runtime` of `pilot/rc-0001` (pure Python, no Aseprite).

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
    "regenerate the committed pilot export: `python -m visual_assets.store export-runtime --catalog-id pilot --release-id rc-0001 --out /tmp/pilot_export`, "
    "then replace the files in frontend/src/visualAssets/__fixtures__/pilot/ with its content"
)


def test_the_committed_pilot_export_equals_a_fresh_export_of_the_release(tmp_path):
    fresh = tmp_path / "export"
    export_runtime("pilot", "rc-0001", fresh)
    names = sorted(p.name for p in fresh.iterdir())
    committed = sorted(p.name for p in COMMITTED.iterdir())
    assert committed == names, f"the pilot fixture's files differ from a fresh export ({committed} vs {names}); {REGENERATE}"
    for name in names:
        assert filecmp.cmp(fresh / name, COMMITTED / name, shallow=False), f"{name} differs from a fresh export; {REGENERATE}"


def test_the_pilot_export_holds_exactly_the_terrain_forest_entry():
    manifest = json.loads((COMMITTED / "runtime_manifest.json").read_text())
    assert [(e["visual_key"], e["family"], e["width"], e["height"]) for e in manifest["entries"]] == [("terrain.forest", "terrain", 16, 16)]
    assert manifest["catalog_id"] == "pilot" and manifest["release_id"] == "rc-0001"
