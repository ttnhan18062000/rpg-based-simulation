"""`pilot/rc-0008` is rc-0007 plus exactly the 36 adopted icons (`TCK-20261009-VISUAL-ASSETS-ICON-RELEASE-CANDIDATE`; the owner's answer, 2026-10-09: "Assemble rc-0008").

Equality guards, rc-0007 precedent: the 34 terrain and border entries are rc-0007's, entry for entry; the other 36 are one `icon.*` entry per icon key at the newest revision of its source, whose artifact the entry names by
id and pixel hash; nothing activates (a candidate is not a release). The registry hash is the live one, so a registry change is a deliberate new candidate. Pure Python, no Aseprite.
"""

from __future__ import annotations

import json

import pytest

from tests.visual_assets import adopted_facts as af
from visual_assets.store import config, records
from visual_assets.store.catalog.registry import load_registry

PILOT = config.CATALOG_ROOT / "manifests" / "candidates" / "pilot"


def _entries(name: str) -> list[dict]:
    return json.loads((PILOT / name).read_text())["entries"]


def _verdict(rc7: list[dict], rc8: list[dict]) -> list[str]:
    """What is wrong with `rc8` as 'rc7 + exactly the icon entries' (empty = right). The mutation proofs call it on altered copies."""
    problems = []
    if [e for e in rc8 if not e["visual_key"].startswith("icon.")] != rc7:
        problems.append("the non-icon entries are not rc-0007's")
    icons = [e for e in rc8 if e["visual_key"].startswith("icon.")]
    keys = sorted(k for k in load_registry().keys if k.startswith("icon."))
    if sorted(e["visual_key"] for e in icons) != keys or len(icons) != af.RC_0008_ICON_ENTRIES:
        problems.append("the icon entries are not exactly one per icon key")
    for entry in icons:
        sid = entry["visual_key"].split(".", 1)[0] + "_" + entry["visual_key"].split(".", 1)[1].replace(".", "_")
        eligible = [r for r in records.list_revisions(sid) if records.is_eligible(sid, r)]
        if not eligible:
            problems.append(f"{entry['visual_key']} names no adopted source {sid}")
            continue
        newest = eligible[-1]
        found = records.load_artifact_for(sid, newest, "x1")
        if found is None or (entry["artifact_id"], entry["pixel_hash"]) != (found[0].artifact_id, found[0].pixel_hash):
            problems.append(f"{entry['visual_key']} does not name the x1 artifact of the newest revision {newest} of {sid}")
    return problems


def test_rc_0008_is_rc_0007_plus_exactly_the_36_icon_entries():
    rc8 = _entries("rc-0008.json")
    assert len(rc8) == 70 and len(_entries("rc-0007.json")) == 34
    assert _verdict(_entries("rc-0007.json"), rc8) == []


def test_rc_0008_is_a_candidate_on_the_live_registry_and_names_every_artifact_it_lists():
    body = json.loads((PILOT / "rc-0008.json").read_text())
    assert (body["catalog_id"], body["release_id"], body["status"]) == ("pilot", "rc-0008", json.loads((PILOT / "rc-0007.json").read_text())["status"])
    assert body["registry_hash"] != json.loads((PILOT / "rc-0007.json").read_text())["registry_hash"]  # the registry carries the structured fallbacks since #471
    for entry in body["entries"]:
        assert (config.CATALOG_ROOT / "generated" / entry["artifact_id"]).is_dir(), entry["artifact_id"]


def _mutants():
    rc7 = _entries("rc-0007.json")
    rc8 = _entries("rc-0008.json")
    icon_sites = [i for i, e in enumerate(rc8) if e["visual_key"].startswith("icon.")]
    terrain_sites = [i for i, e in enumerate(rc8) if not e["visual_key"].startswith("icon.")]
    dropped = [e for i, e in enumerate(rc8) if i != icon_sites[0]]
    altered = [dict(e, pixel_hash="pixels-v1:" + "0" * 64) if i == terrain_sites[0] else e for i, e in enumerate(rc8)]
    swapped = [dict(e, artifact_id=rc8[icon_sites[1]]["artifact_id"], pixel_hash=rc8[icon_sites[1]]["pixel_hash"]) if i == icon_sites[0] else e for i, e in enumerate(rc8)]
    extra = rc8 + [dict(rc8[icon_sites[0]], visual_key="icon.stray.key")]
    return rc7, {"a dropped icon entry": dropped, "one altered terrain entry": altered, "an icon naming another icon's artifact": swapped, "a stray icon entry": extra}


SITES = {"a dropped icon entry": 1, "one altered terrain entry": 2, "an icon naming another icon's artifact": 2, "a stray icon entry": 1}  # entries removed + added versus rc-0008


@pytest.mark.parametrize("name", sorted(SITES))
def test_mutant_each_alteration_of_rc_0008_is_caught(name):
    rc7, mutants = _mutants()
    rc8 = _entries("rc-0008.json")
    mutant = mutants[name]
    dump = lambda entries: {json.dumps(e, sort_keys=True) for e in entries}  # noqa: E731
    assert len(dump(mutant) ^ dump(rc8)) == SITES[name], "the mutant must apply at exactly one site"
    assert _verdict(rc7, mutant) != [], name


def test_older_candidates_still_list_no_icon_slot_and_rc_0007_keeps_34_entries():
    for path in sorted(PILOT.glob("rc-000[1-7].json")):
        assert not [e for e in _entries(path.name) if e["visual_key"].startswith("icon.")], path.name
    assert len(_entries("rc-0007.json")) == 34
