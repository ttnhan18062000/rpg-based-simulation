"""rc-0009 is rc-0008 plus the three real-art proof keys (`TCK-20261011-VISUAL-ASSETS-REAL-ART-RELEASE-PROOF`, the owner's answer of 2026-10-11)."""

from __future__ import annotations

import json

from tests.visual_assets import adopted_facts as af
from visual_assets.store import config


def _entries(release_id: str) -> dict[tuple, dict]:
    path = config.CATALOG_ROOT / "manifests" / "candidates" / "pilot" / f"{release_id}.json"
    return {(e["visual_key"], e.get("detail")): e for e in json.loads(path.read_text())["entries"]}


def test_rc_0009_holds_every_rc_0008_entry_unchanged_plus_exactly_the_three_proof_keys():
    old, new = _entries("rc-0008"), _entries("rc-0009")
    assert len(old) == 70 and len(new) == af.RC_0009_ENTRIES == 73
    assert all(new[key] == entry for key, entry in old.items())  # byte-identical entries: same artifact, pixel hash and adoption chain
    assert sorted(k for k in new if k not in old) == sorted((key, None) for key in af.PROOF_KEYS)
