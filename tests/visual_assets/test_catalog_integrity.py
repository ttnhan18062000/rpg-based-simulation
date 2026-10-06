"""The COMMITTED catalog verifies clean in CI (pure Python; no Aseprite). It holds exactly the pilot forest (`terrain.forest`) and the owner's adoption of draft set `terrain-v1` (2026-10-05T18:17:03Z), plus layout, rules and fixtures."""

from __future__ import annotations

import json

from tests.visual_assets import adopted_facts as af
from visual_assets.store import config, records
from visual_assets.store.verify import verify


def test_the_committed_catalog_has_no_findings():
    assert verify() == [], [f"{f.code} {f.path}: {f.detail}" for f in verify()]


def test_the_committed_catalog_holds_exactly_the_pilot_forest_and_the_adopted_terrain_v1_set():
    # TCK-20261004-VISUAL-ASSETS-PILOT-TERRAIN-TILE (plain) + TCK-20261004-VISUAL-ASSETS-FOREST-DETAIL-TILES (bush, tree): three adopted tiles of one key,
    # one artifact each (+ its record), four release candidates (rc-0001 and rc-0002 are retained history; rc-0003 follows the registry change that added the other terrain keys, rc-0004 the one that added the border mask keys)
    # The owner adopted draft set terrain-v1 on 2026-10-05T18:17:03Z (`adopted_facts`): 31 more sources (22 terrain tiles, 9 border masks) next to the forest's three. No `build` or `release` has covered them yet, so
    # the generated artifacts and the release candidates were forest-only until `build` and the candidate pilot/rc-0005 covered all 34 slots (the user approved both on 2026-10-06).
    assert records.list_source_ids() == af.ADOPTED_SOURCES
    generated = sorted(p.name for p in (config.CATALOG_ROOT / "generated").iterdir() if p.name != ".gitkeep")
    assert generated == af.GENERATED
    for directory in generated:
        assert len([p for p in (config.CATALOG_ROOT / "generated" / directory).iterdir() if p.suffix == ".png"]) == 1
    candidates = sorted(p.name for p in (config.CATALOG_ROOT / "manifests" / "candidates").iterdir() if p.name != ".gitkeep")
    assert candidates == ["pilot"]
    assert sorted(p.name for p in (config.CATALOG_ROOT / "manifests" / "candidates" / "pilot").iterdir()) == af.RELEASE_CANDIDATES


def test_the_committed_catalog_holds_exactly_one_set_adoption_and_it_is_the_owners_terrain_v1_decision():
    """The user ran `adopt-set` on terrain-v1 themselves; this pins that record's exact facts and that every entry points at a draft of the committed set (the drafts stay as history)."""
    folder = config.CATALOG_ROOT / "provenance" / "set-adoptions"
    assert sorted(p.name for p in folder.iterdir() if p.name != ".gitkeep") == [f"{af.SET_ADOPTION_ID}.json"]
    record = json.loads((folder / f"{af.SET_ADOPTION_ID}.json").read_text())
    assert (record["set_adoption_id"], record["set_id"], record["draft_set_hash"], record["decided_at"]) == (af.SET_ADOPTION_ID, af.SET_ID, af.DRAFT_SET_HASH, af.DECIDED_AT)
    assert (record["approver_name"], record["approver_role"]) == af.APPROVER
    assert len(record["entries"]) == 31
    draft_set = json.loads((config.DRAFTS_ROOT / af.SET_ID / "draft_set.json").read_text())
    drafts = {e["draft_id"]: e for e in draft_set["entries"]}
    assert sorted(e["intake_id"] for e in record["entries"]) == sorted(drafts)
    for entry in record["entries"]:
        adoption = records.load_adoption(entry["adoption_id"])
        assert (adoption.source_asset_id, adoption.intake_id) == (drafts[entry["intake_id"]]["source_asset_id"], entry["intake_id"])
        assert (entry["visual_key"], entry.get("detail")) == (drafts[entry["intake_id"]]["visual_key"], drafts[entry["intake_id"]].get("detail"))
    assert sorted(a.source_asset_id for a in (records.load_adoption(p.stem) for p in records.adoptions_dir().glob("*.json"))) == af.ADOPTED_SOURCES
