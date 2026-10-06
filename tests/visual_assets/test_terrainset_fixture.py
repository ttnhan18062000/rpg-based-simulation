"""The frontend's committed copy of the whole-set terrain export equals a fresh `export-runtime` of `pilot/rc-0005` (pure Python, no Aseprite), and rc-0005 is what the user approved on 2026-10-06
(`TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN`): the 34 adopted slots (forest's plain/bush/tree + 22 terrain tiles + 9 border masks) on the same registry as rc-0004.

The pilot fixture (`__fixtures__/pilot`, rc-0004, forest only) is deliberately NOT touched: `pilot_colour_vision.tile_pixels()` takes the first PNG of the pilot export (a known fragility), so the pilot's
forest rule keeps its input. The link between `visual_assets` and `frontend/` is this file-level copy: no import either way."""

from __future__ import annotations

import filecmp
import json
from pathlib import Path

from tests.visual_assets import adopted_facts as af
from visual_assets.store.runtime_export import export_runtime

REPO = Path(__file__).resolve().parents[2]
COMMITTED = REPO / "frontend" / "src" / "visualAssets" / "__fixtures__" / "terrainset"
PILOT = REPO / "frontend" / "src" / "visualAssets" / "__fixtures__" / "pilot"
CANDIDATES = REPO / "visual_assets" / "catalog" / "manifests" / "candidates" / "pilot"
REGENERATE = (
    "regenerate the committed export: `python -m visual_assets.store export-runtime --catalog-id pilot --release-id rc-0005 --out /tmp/terrainset_export`, "
    "then replace the files in frontend/src/visualAssets/__fixtures__/terrainset/ with its content"
)


def test_the_committed_terrainset_export_equals_a_fresh_export_of_rc_0005(tmp_path):
    fresh = tmp_path / "export"
    export_runtime("pilot", "rc-0005", fresh)
    names = sorted(p.name for p in fresh.iterdir())
    assert sorted(p.name for p in COMMITTED.iterdir()) == names, REGENERATE
    for name in names:
        assert filecmp.cmp(fresh / name, COMMITTED / name, shallow=False), f"{name} differs from a fresh export; {REGENERATE}"


def test_the_export_holds_exactly_the_34_adopted_slots_and_the_declared_detail_axes():
    manifest = json.loads((COMMITTED / "runtime_manifest.json").read_text())
    assert manifest["catalog_id"] == "pilot" and manifest["release_id"] == "rc-0005" and len(manifest["entries"]) == 34
    got = sorted((e["visual_key"], e.get("detail")) for e in manifest["entries"])
    expected = [("terrain.forest", d) for d in ("bush", "plain", "tree")]
    expected += [(f"terrain.{s.removeprefix('terrain_')}", None) for s in af.TERRAIN_SOURCES]
    expected += [(f"border.{kind}", v) for kind in ("edge", "inner_corner", "outer_corner") for v in ("v1", "v2", "v3")]
    assert got == sorted(expected, key=lambda p: (p[0], p[1] or ""))
    assert all((e["width"], e["height"]) == (16, 16) for e in manifest["entries"])
    assert [(d["visual_key"], d["values"], d["default"]) for d in manifest["details"]] == [
        ("border.edge", ["v1", "v2", "v3"], "v1"), ("border.inner_corner", ["v1", "v2", "v3"], "v1"), ("border.outer_corner", ["v1", "v2", "v3"], "v1"),
        ("terrain.forest", ["plain", "bush", "tree"], "plain"),
    ]


def test_rc_0005_is_rc_0004_plus_the_31_adopted_slots_on_the_same_registry():
    old, new = (json.loads((CANDIDATES / f"{rc}.json").read_text()) for rc in ("rc-0004", "rc-0005"))
    assert new["registry_hash"] == old["registry_hash"] and new["release_id"] == "rc-0005" and new["catalog_id"] == old["catalog_id"]
    assert all(entry in new["entries"] for entry in old["entries"]) and len(old["entries"]) == 3 and len(new["entries"]) == 34


def test_the_forest_slots_are_byte_identical_to_the_pilot_fixtures():
    pilot = json.loads((PILOT / "runtime_manifest.json").read_text())["entries"]
    now = json.loads((COMMITTED / "runtime_manifest.json").read_text())["entries"]
    for entry in pilot:
        match = [e for e in now if (e["visual_key"], e.get("detail")) == (entry["visual_key"], entry.get("detail"))]
        assert len(match) == 1 and match[0]["file"] == entry["file"] and match[0]["pixel_hash"] == entry["pixel_hash"]
        assert (COMMITTED / entry["file"]).read_bytes() == (PILOT / entry["file"]).read_bytes()
