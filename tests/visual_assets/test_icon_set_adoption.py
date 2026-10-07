"""The owner's adoption of draft set `icons-key-v1` (`TCK-20261006-VISUAL-ASSETS-RECORD-ICON-KEY-SET-ADOPTION`): what the catalog now holds for it, and what it does not.

The user ran `adopt-set` themselves on 2026-10-06T15:21:47Z (`adopted_facts`). These guards compare with equality; if the catalog changes again (a revocation, a build, a release), the facts change in the same
commit as that decision. The drafts stay as history.
"""

from __future__ import annotations

import hashlib
import json

from tests.visual_assets import adopted_facts as af
from visual_assets.store import config, drafts, records
from visual_assets.store.catalog.registry import load_registry


def test_the_draft_set_still_hashes_to_what_the_adoption_recorded_and_every_entry_is_adopted():
    record, data = drafts.load_set(af.ICON_SET_ID)
    assert "sha256:" + hashlib.sha256(data).hexdigest() == af.ICON_DRAFT_SET_HASH
    adoptions = {a.intake_id: a for a in (records.load_adoption(p.stem) for p in records.adoptions_dir().glob("*.json"))}
    assert len(record.entries) == 14 and [e.draft_id for e in record.entries if e.draft_id not in adoptions] == []
    for entry in record.entries:
        adoption = adoptions[entry.draft_id]
        assert (adoption.source_asset_id, adoption.detail_value) == (entry.source_asset_id, entry.detail), entry.visual_key
        assert entry.source_asset_id == entry.visual_key.replace(".", "_")
    assert sorted(a.source_asset_id for a in adoptions.values() if a.intake_id in {e.draft_id for e in record.entries}) == af.ICON_SOURCES


def test_each_icon_source_is_in_the_catalog_with_its_own_source_and_the_icon_keys_stay_optional():
    sources = sorted(p.name for p in (config.CATALOG_ROOT / "sources").iterdir() if p.name != ".gitkeep")
    assert [s for s in sources if s.startswith("icon_")] == af.ICON_SOURCES
    registry = load_registry()
    icon_keys = sorted(k for k in registry.keys if k.startswith("icon."))
    assert [k.replace(".", "_") for k in icon_keys] == af.ICON_SOURCES
    assert all(registry.keys[k].optional and registry.keys[k].variant_axes == () for k in icon_keys)  # nothing requires them: a missing image leaves today's fallback


def test_no_artifact_and_no_release_candidate_covers_an_icon_slot():
    """The adoption is a record of the owner's decision, not a build or a release: `generated` holds the 34 terrain-era artifacts, and every candidate lists only terrain and border slots (rc-0006: 34)."""
    generated = sorted(p.name for p in (config.CATALOG_ROOT / "generated").iterdir() if p.name != ".gitkeep")
    assert generated == af.GENERATED and not [g for g in generated if g.startswith("icon_")]
    candidates = config.CATALOG_ROOT / "manifests" / "candidates" / "pilot"
    for path in sorted(candidates.glob("rc-*.json")):
        keys = {e["visual_key"] for e in json.loads(path.read_text())["entries"]}
        assert not [k for k in keys if k.startswith("icon.")], path.name
    assert len(json.loads((candidates / "rc-0006.json").read_text())["entries"]) == 34


def test_the_adoption_names_no_detail_value_and_no_revocation_exists():
    for adoption in (records.load_adoption(p.stem) for p in records.adoptions_dir().glob("*.json")):
        if adoption.source_asset_id.startswith("icon_"):
            assert adoption.detail_value is None, adoption.source_asset_id
    revocations = config.CATALOG_ROOT / "provenance" / "revocations"
    assert not revocations.exists() or [p for p in revocations.iterdir() if p.name != ".gitkeep"] == []
