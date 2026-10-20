"""rc-0012 is rc-0011 plus the 11 entity markers (`TCK-20261013-VISUAL-ASSETS-ENTITY-MARKER-DRAFTS`, the owner's answer of 2026-10-19: "Assemble rc-0012 now").

The rule, by equality: all 105 rc-0011 entries are byte-identical; the 11 entity markers (`icon.entity.<kind>`) are new, one entry each, no detail axis; nothing else. Registry aliases are not entries
(registry-only, Known gap in `docs/assets/store_contract.md`)."""

from __future__ import annotations

import json

from tests.visual_assets import adopted_facts as af
from visual_assets.store import config


def _entries(release_id: str) -> list[dict]:
    path = config.CATALOG_ROOT / "manifests" / "candidates" / "pilot" / f"{release_id}.json"
    return json.loads(path.read_text())["entries"]


def test_rc_0012_is_rc_0011_byte_identical_plus_the_eleven_entity_markers_and_nothing_more():
    old = {(e["visual_key"], e.get("detail")): e for e in _entries("rc-0011")}
    new = {(e["visual_key"], e.get("detail")): e for e in _entries("rc-0012")}
    assert len(old) == af.RC_0011_ENTRIES == 105 and len(new) == af.RC_0012_ENTRIES == 116
    assert all(new[slot] == entry for slot, entry in old.items())  # byte-identical entries
    added = {slot for slot in new if slot not in old}
    assert added == {(key, None) for key in af.ENTITY_KEYS} and len(added) == 11  # nothing else
    for key in af.ENTITY_KEYS:
        assert new[(key, None)]["artifact_id"] == key.replace(".", "_") + "--x1" and "detail" not in new[(key, None)]


def test_no_alias_is_an_entry_and_rc_0011_is_untouched():
    keys = {e["visual_key"] for e in _entries("rc-0012")}
    assert not keys & set(af.REGISTRY_ALIASES)
    assert len(_entries("rc-0011")) == 105
