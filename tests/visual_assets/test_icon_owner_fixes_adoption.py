"""The owner's adoption of seven revisions of adopted icons (`TCK-20261008-VISUAL-ASSETS-RECORD-ICON-OWNER-FIXES-ADOPTION`).

The owner ran `review` and `adopt --parent r0001` themselves for each slot, 2026-10-08T14:23:46Z to 14:24:07Z (`adopted_facts.ICON_FIX_ADOPTIONS`). Equality guards: each is `r0002` of an
existing source, parent `r0001`, from the draft of `icons-owner-fixes-v1` that the draft set still records; the two declined drafts are not adopted; no source asset was added.
"""

from __future__ import annotations

import hashlib

from tests.visual_assets import adopted_facts as af
from visual_assets.store import config, drafts, records


def _adoptions():
    return {a.adoption_id: a for a in (records.load_adoption(p.stem) for p in records.adoptions_dir().glob("*.json"))}


def test_the_fix_draft_set_still_hashes_to_the_value_the_owner_adopted_from():
    record, data = drafts.load_set(af.ICON_FIX_SET_ID)
    assert "sha256:" + hashlib.sha256(data).hexdigest() == af.ICON_FIX_DRAFT_SET_HASH and len(record.entries) == 9


def test_each_of_the_seven_revisions_is_r0002_with_parent_r0001_from_its_own_draft_by_the_owner():
    record, _ = drafts.load_set(af.ICON_FIX_SET_ID)
    by_source = {e.source_asset_id: e for e in record.entries}
    adoptions = _adoptions()
    for source, (adoption_id, intake_id, decided_at) in af.ICON_FIX_ADOPTIONS.items():
        a = adoptions[adoption_id]
        assert (a.source_asset_id, a.intake_id, a.decided_at, a.parent_revision) == (source, intake_id, decided_at, "r0001")
        assert (a.approver_name, a.approver_role) == af.ICON_FIX_APPROVER
        draft = by_source[source + "_fix"]
        assert (draft.draft_id, draft.visual_key) == (intake_id, source.replace("_", ".", 2))
        folder = config.CATALOG_ROOT / "sources" / source
        assert sorted(p.name for p in folder.iterdir()) == ["r0001.aseprite", "r0001.source.json", "r0002.aseprite", "r0002.source.json"]


def test_the_two_declined_drafts_are_not_adopted_and_no_source_asset_was_added():
    record, _ = drafts.load_set(af.ICON_FIX_SET_ID)
    adopted_intakes = {a.intake_id for a in _adoptions().values()}
    not_adopted = sorted(e.visual_key for e in record.entries if e.draft_id not in adopted_intakes)
    assert not_adopted == ["icon.marker.enemy_camp", "icon.marker.ruins"]
    assert records.list_source_ids() == af.ADOPTED_SOURCES and len(_adoptions()) == af.ADOPTION_COUNT == 77
