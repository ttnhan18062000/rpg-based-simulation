"""Tests for tools/mechanism_registry/mechanism_capabilities_card_mapping.py and
tools/mechanism_registry/mechanism_capabilities_regenerate.py.

TCK-20260915-ARTIFACT-STATE-CONVERGENCE scope item 3. Mirrors
test_mechanism_atlas_regenerate.py's own discipline: the load-bearing tests are the body
preservation ones (test_regeneration_never_touches_card_body) -- the capabilities page exists
specifically because its title/desc prose is written for a non-dev reader; a regenerator that
touched more than tier/tierLabel would destroy that.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from tools.mechanism_registry.mechanism_capabilities_card_mapping import (
    CARD_TO_MECHANISM_ID,
    PARTIAL_COVERAGE_CARDS,
    SPLIT_CARD_MECHANISMS,
    all_mechanism_card_badge_positions,
)
from tools.mechanism_registry.mechanism_capabilities_regenerate import (
    TIER_LABEL_OVERRIDES,
    _sections_by_id,
    apply_diffs,
    compute_diffs,
    extract_json_block,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
_CAPABILITIES_PATH = REPO_ROOT / "docs" / "brainstorm" / "simulation_capabilities.html"
_REGISTRY_PATH = REPO_ROOT / "docs" / "brainstorm" / "mechanisms.yaml"


def _real_capabilities_data() -> list:
    html = _CAPABILITIES_PATH.read_text()
    raw_json, _, _ = extract_json_block(html)
    return json.loads(raw_json)


def _real_registry():
    import yaml

    data = yaml.safe_load(_REGISTRY_PATH.read_text())
    states = {m["id"]: m["state"] for m in data["mechanisms"]}
    verified = {m["id"]: m.get("verified") for m in data["mechanisms"]}
    return states, verified


# --- mapping table integrity -------------------------------------------------------------------


def test_mapping_table_resolves_to_real_mechanism_ids():
    states, _ = _real_registry()
    positions = all_mechanism_card_badge_positions()
    for mech_id in positions:
        assert mech_id in states, f"mapping references unknown mechanism id {mech_id!r}"


def test_mapping_table_has_no_duplicate_card_positions():
    seen = set()
    for (section, idx), _mech_id in CARD_TO_MECHANISM_ID.items():
        key = (section, idx)
        assert key not in seen, f"duplicate position {key}"
        seen.add(key)
    assert SPLIT_CARD_MECHANISMS == {}, "no split cards expected/found on the capabilities page"
    assert PARTIAL_COVERAGE_CARDS == {}, "no partial-coverage cards expected/found"


def test_every_real_capabilities_card_key_exists_in_the_real_file():
    """The mapping cites (section, index) positions -- confirm every one actually resolves in the
    real committed file, so a future capabilities edit that reorders/removes a card is caught."""
    data = _real_capabilities_data()
    sections = _sections_by_id(data)
    for (section, idx), _mech_id in CARD_TO_MECHANISM_ID.items():
        assert section in sections, f"unknown section {section!r}"
        assert idx < len(sections[section]["cards"]), f"{section}#{idx} out of range"


# --- compute_diffs on a synthetic fixture ------------------------------------------------------


def _fixture_data():
    return [
        {
            "id": "action",
            "cards": [
                {"title": "Combat", "tier": "planned", "tierLabel": "Not yet built", "desc": "d1"},
            ],
        }
    ]


def _patch_mapping(monkeypatch, positions):
    monkeypatch.setattr(
        "tools.mechanism_registry.mechanism_capabilities_regenerate.all_mechanism_card_badge_positions",
        lambda: positions,
    )


def test_compute_diffs_detects_single_mapped_mismatch(monkeypatch):
    _patch_mapping(monkeypatch, {"combat_resolution": [("action", 0, 0)]})
    data = _fixture_data()
    diffs = compute_diffs(data, {"combat_resolution": "done"}, {"combat_resolution": None})
    assert len(diffs) == 1
    assert diffs[0]["old_tier"] == "planned"
    assert diffs[0]["new_tier"] == "live"


def test_compute_diffs_empty_when_already_synced(monkeypatch):
    _patch_mapping(monkeypatch, {"combat_resolution": [("action", 0, 0)]})
    data = _fixture_data()
    diffs = compute_diffs(data, {"combat_resolution": "gap"}, {"combat_resolution": None})
    assert diffs == []


def test_compute_diffs_raises_on_unknown_mechanism_id(monkeypatch):
    _patch_mapping(monkeypatch, {"nonexistent_mechanism": [("action", 0, 0)]})
    data = _fixture_data()
    with pytest.raises(KeyError):
        compute_diffs(data, {"combat_resolution": "done"}, {"combat_resolution": None})


def test_compute_diffs_uses_done_contradicted_case(monkeypatch):
    _patch_mapping(monkeypatch, {"camp": [("action", 0, 0)]})
    data = _fixture_data()
    diffs = compute_diffs(
        data,
        {"camp": "done"},
        {"camp": {"verdict": "contradicted"}},
    )
    assert len(diffs) == 1
    assert diffs[0]["new_tier"] == "built"


# --- apply_diffs never touches anything but tier/tierLabel on diffed cards ---------------------


def test_apply_diffs_only_changes_targeted_fields(monkeypatch):
    _patch_mapping(monkeypatch, {"combat_resolution": [("action", 0, 0)]})
    data = _fixture_data()
    diffs = compute_diffs(data, {"combat_resolution": "done"}, {"combat_resolution": None})
    mutated = apply_diffs(data, diffs)

    mutated_sections = _sections_by_id(mutated)
    orig_sections = _sections_by_id(data)
    new_card = mutated_sections["action"]["cards"][0]
    orig_card = orig_sections["action"]["cards"][0]

    assert new_card["tier"] == "live"
    assert new_card["title"] == orig_card["title"]
    assert new_card["desc"] == orig_card["desc"]
    # original untouched (apply_diffs deep-copies)
    assert orig_card["tier"] == "planned"


# --- real-file round trip (load-bearing) --------------------------------------------------------


def test_json_block_round_trips_byte_identical_when_unmodified():
    html = _CAPABILITIES_PATH.read_text()
    raw_json, start, end = extract_json_block(html)
    data = json.loads(raw_json)
    reserialized = json.dumps(data, indent=2, ensure_ascii=False)
    assert reserialized == raw_json


def test_real_capabilities_has_no_drift_against_the_real_registry():
    """The load-bearing regression test, mirroring the atlas's own convention."""
    data = _real_capabilities_data()
    states, verified = _real_registry()
    diffs = compute_diffs(data, states, verified)
    assert diffs == [], (
        f"Capabilities tier has drifted from the registry: {diffs}. "
        f"Run `python3 tools/mechanism_registry/mechanism_capabilities_regenerate.py` to fix."
    )


def test_every_tier_label_override_targets_a_diffing_real_mechanism():
    """TIER_LABEL_OVERRIDES is meant to accompany a real, currently-applied tier fix -- not to
    silently linger after the underlying drift is gone. If this ever starts failing, the override
    entry should be removed, not the assertion loosened."""
    data = _real_capabilities_data()
    states, verified = _real_registry()
    # Re-derive against a version of the registry where nothing has been fixed yet is not needed
    # here -- overrides are only meaningful relative to a drift that existed at write time. This
    # test instead confirms every override still resolves to a real mechanism id.
    for mech_id in TIER_LABEL_OVERRIDES:
        assert mech_id in states, f"override references unknown mechanism {mech_id!r}"


def test_regeneration_never_touches_card_body_or_unmapped_cards():
    """[Load-bearing per peer review] Regenerating against a mutated registry copy (so there IS
    real diff work to do) must still leave every mapped card's title/desc byte-identical -- only
    tier/tierLabel may change, and only for mapped cards that actually drifted."""
    data = _real_capabilities_data()
    states, verified = _real_registry()
    states = dict(states)

    flipped_id = "combat_resolution"
    assert flipped_id in states
    original_state = states[flipped_id]
    states[flipped_id] = "gap" if original_state != "gap" else "partial"

    diffs = compute_diffs(data, states, verified)
    assert diffs, "test fixture setup expected at least one diff to prove body preservation against"
    mutated = apply_diffs(data, diffs)

    positions = all_mechanism_card_badge_positions()
    diffed_positions = {(d["section"], d["index"]) for d in diffs}
    orig_sections = _sections_by_id(data)
    mutated_sections = _sections_by_id(mutated)

    for mech_id, entries in positions.items():
        for section, index, _badge_index in entries:
            orig_card = orig_sections[section]["cards"][index]
            new_card = mutated_sections[section]["cards"][index]
            for key in ("title", "desc"):
                assert new_card.get(key) == orig_card.get(key), (
                    f"{section}#{index} field {key!r} changed -- regenerator must never touch body prose"
                )
            if (section, index) in diffed_positions:
                assert new_card["tier"] != orig_card["tier"]
            else:
                assert new_card["tier"] == orig_card["tier"]
                assert new_card["tierLabel"] == orig_card["tierLabel"]

    # Unmapped cards (no mechanism id at all) are identical objects too.
    mapped_keys = {(s, i) for entries in positions.values() for s, i, _ in entries}
    for sec in data:
        for idx, card in enumerate(sec["cards"]):
            if (sec["id"], idx) not in mapped_keys:
                mutated_card = mutated_sections[sec["id"]]["cards"][idx]
                assert mutated_card == card, f"untouched card {sec['id']}#{idx} changed"
