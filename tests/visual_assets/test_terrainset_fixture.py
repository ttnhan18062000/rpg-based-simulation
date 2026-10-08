"""The frontend's committed copy of the whole-set terrain export equals a fresh `export-runtime` of `pilot/rc-0007` (pure Python, no Aseprite), and rc-0006 is what the user approved on 2026-10-06
(`TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN`): the 34 adopted slots (forest's plain/bush/tree + 22 terrain tiles + 9 border masks) on the registry that holds the 14 `icon.*` keys (rc-0005's slots, re-assembled by `TCK-20261006-VISUAL-ASSETS-ICON-KEY-FAMILIES` as rc-0006 and again by `TCK-20261007-VISUAL-ASSETS-ICON-V2-KEYS-AND-RC` as rc-0007 after the 22 icon set v2 keys; the user approved both).

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
    "regenerate the committed export: `python -m visual_assets.store export-runtime --catalog-id pilot --release-id rc-0007 --out /tmp/terrainset_export`, "
    "then replace the files in frontend/src/visualAssets/__fixtures__/terrainset/ with its content"
)


def test_the_committed_terrainset_export_equals_a_fresh_export_of_the_current_release(tmp_path):
    fresh = tmp_path / "export"
    export_runtime("pilot", "rc-0007", fresh)
    names = sorted(p.name for p in fresh.iterdir())
    assert sorted(p.name for p in COMMITTED.iterdir()) == names, REGENERATE
    for name in names:
        assert filecmp.cmp(fresh / name, COMMITTED / name, shallow=False), f"{name} differs from a fresh export; {REGENERATE}"


def test_the_export_holds_exactly_the_34_adopted_slots_and_the_declared_detail_axes():
    manifest = json.loads((COMMITTED / "runtime_manifest.json").read_text())
    assert manifest["catalog_id"] == "pilot" and manifest["release_id"] == "rc-0007" and len(manifest["entries"]) == 34
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


def test_rc_0006_lists_exactly_the_entries_of_rc_0005_so_only_the_registry_moved():
    """`pilot/rc-0006` was assembled only because registering the 14 `icon.*` keys changed the registry hash (`TCK-20261006-VISUAL-ASSETS-ICON-KEY-FAMILIES`, D20; the user approved it on
    2026-10-06). Same 34 slots, artifact ids and pixel hashes as rc-0005's, so "the release content is unchanged" is a checked fact."""
    old, new = (json.loads((CANDIDATES / f"{rc}.json").read_text()) for rc in ("rc-0005", "rc-0006"))
    assert new["entries"] == old["entries"] and len(new["entries"]) == 34
    assert new["registry_hash"] != old["registry_hash"] and new["release_id"] == "rc-0006" and new["catalog_id"] == old["catalog_id"]


def test_the_forest_slots_are_byte_identical_to_the_pilot_fixtures():
    pilot = json.loads((PILOT / "runtime_manifest.json").read_text())["entries"]
    now = json.loads((COMMITTED / "runtime_manifest.json").read_text())["entries"]
    for entry in pilot:
        match = [e for e in now if (e["visual_key"], e.get("detail")) == (entry["visual_key"], entry.get("detail"))]
        assert len(match) == 1 and match[0]["file"] == entry["file"] and match[0]["pixel_hash"] == entry["pixel_hash"]
        assert (COMMITTED / entry["file"]).read_bytes() == (PILOT / entry["file"]).read_bytes()


def test_rc_0007_lists_exactly_the_entries_of_rc_0006_so_only_the_registry_moved():
    """`pilot/rc-0007` was assembled only because registering the 22 icon set v2 keys changed the registry hash (`TCK-20261007-VISUAL-ASSETS-ICON-V2-KEYS-AND-RC`; the user approved it on
    2026-10-07). Same 34 slots, artifact ids and pixel hashes as rc-0006's (no icon is built, so none is in any release), so "the release content is unchanged" is a checked fact."""
    old, new = (json.loads((CANDIDATES / f"{rc}.json").read_text()) for rc in ("rc-0006", "rc-0007"))
    assert new["entries"] == old["entries"] and len(new["entries"]) == 34
    assert new["registry_hash"] != old["registry_hash"] and new["release_id"] == "rc-0007" and new["catalog_id"] == old["catalog_id"]
