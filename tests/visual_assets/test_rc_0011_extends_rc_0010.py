"""rc-0011 is rc-0010 plus the 18 object markers (`TCK-20261013-VISUAL-ASSETS-MARKERS-RC-AND-CLOSE`, the owner's answer of 2026-10-14: "Assemble rc-0011 (105)").

The rule, by equality: all 87 rc-0010 entries are byte-identical; the 18 object markers (13 `icon.node.*`, `icon.marker.nest`, 4 `icon.building.*`) are new, one entry each, no detail axis; nothing else. The five registry aliases are not
entries (registry-only, Known gap in `docs/assets/store_contract.md`)."""

from __future__ import annotations

import json

from tests.visual_assets import adopted_facts as af
from visual_assets.store import config


def _entries(release_id: str) -> list[dict]:
    path = config.CATALOG_ROOT / "manifests" / "candidates" / "pilot" / f"{release_id}.json"
    return json.loads(path.read_text())["entries"]


def test_rc_0011_is_rc_0010_byte_identical_plus_the_eighteen_object_markers_and_nothing_more():
    old = {(e["visual_key"], e.get("detail")): e for e in _entries("rc-0010")}
    new = {(e["visual_key"], e.get("detail")): e for e in _entries("rc-0011")}
    assert len(old) == af.RC_0010_ENTRIES == 87 and len(new) == af.RC_0011_ENTRIES == 105
    assert all(new[slot] == entry for slot, entry in old.items())  # byte-identical entries
    added = {slot for slot in new if slot not in old}
    assert added == {(key, None) for key in af.OBJECT_KEYS} and len(added) == 18  # nothing else
    for key in af.OBJECT_KEYS:
        assert new[(key, None)]["artifact_id"] == key.replace(".", "_") + "--x1" and "detail" not in new[(key, None)]


def test_no_alias_is_an_entry_and_rc_0010_is_untouched():
    keys = {e["visual_key"] for e in _entries("rc-0011")}
    assert not keys & {"icon.building.shop", "icon.marker.camp", "icon.marker.ruin", "icon.marker.dungeon", "icon.marker.lair"}
    assert len(_entries("rc-0010")) == 87
