"""The COMMITTED catalog verifies clean in CI (pure Python; no Aseprite). It holds exactly the pilot terrain asset (`terrain.forest`, adopted by the owner), plus layout, rules and fixtures."""

from __future__ import annotations

from visual_assets.store import config, records
from visual_assets.store.verify import verify


def test_the_committed_catalog_has_no_findings():
    assert verify() == [], [f"{f.code} {f.path}: {f.detail}" for f in verify()]


def test_the_committed_catalog_holds_exactly_the_pilot_asset():
    # TCK-20261004-VISUAL-ASSETS-PILOT-TERRAIN-TILE (plain) + TCK-20261004-VISUAL-ASSETS-FOREST-DETAIL-TILES (bush, tree): three adopted tiles of one key,
    # one artifact each (+ its record), two release candidates (rc-0001 is the retained previous release)
    assert records.list_source_ids() == ["terrain_forest", "terrain_forest_bush", "terrain_forest_tree"]
    generated = sorted(p.name for p in (config.CATALOG_ROOT / "generated").iterdir() if p.name != ".gitkeep")
    assert generated == ["terrain_forest--x1", "terrain_forest_bush--x1", "terrain_forest_tree--x1"]
    for directory in generated:
        assert len([p for p in (config.CATALOG_ROOT / "generated" / directory).iterdir() if p.suffix == ".png"]) == 1
    candidates = sorted(p.name for p in (config.CATALOG_ROOT / "manifests" / "candidates").iterdir() if p.name != ".gitkeep")
    assert candidates == ["pilot"]
    assert sorted(p.name for p in (config.CATALOG_ROOT / "manifests" / "candidates" / "pilot").iterdir()) == ["rc-0001.json", "rc-0002.json"]
