"""The COMMITTED catalog verifies clean in CI (pure Python; no Aseprite). It holds exactly the pilot terrain asset (`terrain.forest`, adopted by the owner), plus layout, rules and fixtures."""

from __future__ import annotations

from visual_assets.store import config, records
from visual_assets.store.verify import verify


def test_the_committed_catalog_has_no_findings():
    assert verify() == [], [f"{f.code} {f.path}: {f.detail}" for f in verify()]


def test_the_committed_catalog_holds_exactly_the_pilot_asset():
    # TCK-20261004-VISUAL-ASSETS-PILOT-TERRAIN-TILE: one adopted terrain tile, one artifact (+ its record), one release candidate
    assert records.list_source_ids() == ["terrain_forest"]
    generated = sorted(p.name for p in (config.CATALOG_ROOT / "generated").iterdir() if p.name != ".gitkeep")
    assert generated == ["terrain_forest--x1"]
    assert len([p for p in (config.CATALOG_ROOT / "generated" / "terrain_forest--x1").iterdir() if p.suffix == ".png"]) == 1
    candidates = sorted(p.name for p in (config.CATALOG_ROOT / "manifests" / "candidates").iterdir() if p.name != ".gitkeep")
    assert candidates == ["pilot"]
    assert [p.name for p in (config.CATALOG_ROOT / "manifests" / "candidates" / "pilot").iterdir()] == ["rc-0001.json"]
