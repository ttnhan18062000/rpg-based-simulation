"""rc-0010 is rc-0009 plus the 14 terrain variants (`TCK-20261012-VISUAL-ASSETS-TERRAIN-VARIANTS-RC-AND-CLOSE`, the owner's answers of 2026-10-12 and 2026-10-13).

The rule, by equality: 67 rc-0009 entries are byte-identical; the six keys that gained a detail axis (grassland, mountain, cave, ruins, swamp, shallow_water) have their rc-0009 entry re-anchored, i.e. equal to
it PLUS `detail: base` (the same artifact and pixel hash), the owner's "Accept detail: base"; the 14 variants are new; nothing else (the forest rc-0001 -> rc-0002 precedent)."""

from __future__ import annotations

import json

from tests.visual_assets import adopted_facts as af
from visual_assets.store import config


def _entries(release_id: str) -> list[dict]:
    path = config.CATALOG_ROOT / "manifests" / "candidates" / "pilot" / f"{release_id}.json"
    return json.loads(path.read_text())["entries"]


def test_rc_0010_is_rc_0009_with_six_re_anchored_entries_and_the_fourteen_variants_and_nothing_more():
    old = {(e["visual_key"], e.get("detail")): e for e in _entries("rc-0009")}
    new = {(e["visual_key"], e.get("detail")): e for e in _entries("rc-0010")}
    assert len(old) == af.RC_0009_ENTRIES == 73 and len(new) == af.RC_0010_ENTRIES == 87
    re_anchored = {(key, None) for key in af.RC_0010_RE_ANCHORED}
    assert re_anchored <= set(old) and not re_anchored & set(new)  # the slot (key, none) is gone from rc-0010
    identical = set(old) - re_anchored
    assert len(identical) == 67 and all(new[slot] == old[slot] for slot in identical)  # byte-identical entries
    for key, _ in re_anchored:
        assert new[(key, "base")] == {**old[(key, None)], "detail": "base"}  # the same artifact and pixel hash, plus detail base, no more
    variants = {slot for slot in new if slot not in old and slot[1] != "base"}
    assert variants == {(key, detail) for key, detail in af.VARIANT_DETAILS.values()} and len(variants) == 14
    assert set(new) == identical | {(key, "base") for key in af.RC_0010_RE_ANCHORED} | variants  # nothing else


def test_rc_0009_is_untouched_and_forest_keeps_its_three_slots():
    assert len(_entries("rc-0009")) == 73
    forest = sorted(e["detail"] for e in _entries("rc-0010") if e["visual_key"] == "terrain.forest")
    assert forest == ["bush", "plain", "tree"]
