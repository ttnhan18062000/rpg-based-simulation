"""The COMMITTED catalog verifies clean in CI (pure Python; no Aseprite). It holds zero keys, sources and artifacts, only layout, rules and fixtures."""

from __future__ import annotations

from visual_assets.store import config, records
from visual_assets.store.verify import verify


def test_the_committed_catalog_has_no_findings():
    assert verify() == [], [f"{f.code} {f.path}: {f.detail}" for f in verify()]


def test_the_committed_catalog_holds_no_real_asset():
    assert records.list_source_ids() == []
    assert [p for p in (config.CATALOG_ROOT / "generated").iterdir() if p.name != ".gitkeep"] == []
    assert [p for p in (config.CATALOG_ROOT / "manifests" / "candidates").iterdir() if p.name != ".gitkeep"] == []
