"""Tests for tools/mechanism_registry/mechanism_atlas_card_mapping.py and tools/mechanism_registry/mechanism_atlas_regenerate.py.

TCK-20260915-ARTIFACT-STATE-CONVERGENCE scope item 1. The load-bearing tests are the prose
preservation ones (test_regeneration_never_touches_card_prose*): a regenerator that emitted whole
cards from a template would silently destroy hand-written atlas prose, and a diff showing many
cards "changed" would look identical to a correct cls-only diff at a glance without this check --
see the module docstring for why this is treated as the sharpest risk in the ticket, not a general
caution.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from tools.mechanism_registry.mechanism_atlas_card_mapping import (
    CARD_TO_MECHANISM_ID,
    PARTIAL_COVERAGE_CARDS,
    SPLIT_CARD_MECHANISMS,
    all_mechanism_card_badge_positions,
)
from tools.mechanism_registry.mechanism_atlas_regenerate import (
    apply_diffs,
    compute_diffs,
    extract_json_block,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
_ATLAS_PATH = REPO_ROOT / "docs" / "brainstorm" / "rpg_feature_atlas.html"
_REGISTRY_PATH = REPO_ROOT / "registries" / "mechanisms.yaml"


def _real_atlas_data() -> dict:
    html = _ATLAS_PATH.read_text()
    raw_json, _, _ = extract_json_block(html)
    return json.loads(raw_json)


def _real_registry_states() -> dict:
    import yaml

    data = yaml.safe_load(_REGISTRY_PATH.read_text())
    return {m["id"]: m["state"] for m in data["mechanisms"]}


# --- mapping table integrity -------------------------------------------------------------------


def test_mapping_table_resolves_to_real_mechanism_ids():
    real_ids = set(_real_registry_states().keys())
    positions = all_mechanism_card_badge_positions()
    for mech_id in positions:
        assert mech_id in real_ids, f"mapping references unknown mechanism id {mech_id!r}"


def test_mapping_table_has_no_duplicate_card_badge_positions():
    seen = set()
    for (section, idx), _mech_id in CARD_TO_MECHANISM_ID.items():
        key = (section, idx, 0)
        assert key not in seen, f"duplicate position {key}"
        seen.add(key)
    for (section, idx), mech_ids in SPLIT_CARD_MECHANISMS.items():
        for badge_idx in range(len(mech_ids)):
            key = (section, idx, badge_idx)
            assert key not in seen, f"duplicate position {key}"
            seen.add(key)
    for (section, idx), badge_map in PARTIAL_COVERAGE_CARDS.items():
        for badge_idx in badge_map:
            key = (section, idx, badge_idx)
            assert key not in seen, f"duplicate position {key}"
            seen.add(key)


def test_mapping_covers_exactly_73_of_the_atlas_carded_mechanisms():
    """73 remains the number of REGISTERED mechanisms with a real atlas card -- unchanged by
    TCK-20260916-MECHANISM-REGISTRY-COMPLETENESS-PASS and TCK-20260916-MECHANISM-IMPLEMENTED-BY-
    BINDING, both of which added mechanisms found by enumerating src/domains/ and src/systems/
    directly, none of which have an atlas card at all (no card was ever written for them, since
    Foundation's original seed only read the atlas). That's expected, not a defect -- distinct
    from nest/lair, which are real mechanisms the wiring map documents but the atlas simply never
    carded either."""
    real_ids = set(_real_registry_states().keys())
    positions = all_mechanism_card_badge_positions()
    mapped = set(positions.keys())
    unmapped = real_ids - mapped
    assert unmapped == {
        "nest", "lair", "cooperation", "progression_conversion", "resource_harvesting",
        "fame", "fidelity_drift", "belief_institution", "strategic_learning_bias",
        "strategic_redirection", "concern_intake", "event_interpretation", "narrative_memory",
        "group_coordination", "quest_reward_distribution", "commitment_pressure_consequences",
    }, f"expected exactly these 16 to be unmapped (no atlas card), got {unmapped}"
    assert len(mapped) == 73


# --- compute_diffs on a synthetic fixture ------------------------------------------------------


def _fixture_atlas():
    return {
        "entity-action": [
            {"title": "Combat", "badges": [{"cls": "gap", "text": "Gap"}], "desc": "d1"},
        ],
        "entity-profile": [None] * 7,
    }


def _patch_mapping(monkeypatch, positions):
    monkeypatch.setattr(
        "tools.mechanism_registry.mechanism_atlas_regenerate.all_mechanism_card_badge_positions",
        lambda: positions,
    )


def test_compute_diffs_detects_single_mapped_mismatch(monkeypatch):
    _patch_mapping(monkeypatch, {"combat_resolution": [("entity-action", 0, 0)]})
    atlas = _fixture_atlas()
    diffs = compute_diffs(atlas, {"combat_resolution": "done"})
    assert len(diffs) == 1
    assert diffs[0]["old_cls"] == "gap"
    assert diffs[0]["new_cls"] == "done"


def test_compute_diffs_empty_when_already_synced(monkeypatch):
    _patch_mapping(monkeypatch, {"combat_resolution": [("entity-action", 0, 0)]})
    atlas = _fixture_atlas()
    diffs = compute_diffs(atlas, {"combat_resolution": "gap"})
    assert diffs == []


def test_compute_diffs_raises_on_unknown_mechanism_id(monkeypatch):
    _patch_mapping(monkeypatch, {"nonexistent_mechanism": [("entity-action", 0, 0)]})
    atlas = _fixture_atlas()
    with pytest.raises(KeyError):
        compute_diffs(atlas, {"combat_resolution": "done"})


def test_split_card_badges_resolve_independently(monkeypatch):
    fixture = {
        "entity-profile": [
            {
                "title": "Aging & Succession",
                "badges": [
                    {"cls": "done", "text": "Aging/death live"},
                    {"cls": "partial", "text": "Succession never triggers"},
                ],
                "desc": "d",
            }
        ]
    }
    _patch_mapping(
        monkeypatch,
        {
            "aging_death": [("entity-profile", 0, 0)],
            "succession": [("entity-profile", 0, 1)],
        },
    )
    diffs = compute_diffs(fixture, {"aging_death": "done", "succession": "orphan"})
    assert len(diffs) == 1
    assert diffs[0]["mechanism_id"] == "succession"
    assert diffs[0]["new_cls"] == "orphan"


# --- apply_diffs never touches anything but the diffed cls values ------------------------------


def test_apply_diffs_only_changes_targeted_cls(monkeypatch):
    _patch_mapping(monkeypatch, {"combat_resolution": [("entity-action", 0, 0)]})
    atlas = _fixture_atlas()
    diffs = compute_diffs(atlas, {"combat_resolution": "done"})
    mutated = apply_diffs(atlas, diffs)

    assert mutated["entity-action"][0]["badges"][0]["cls"] == "done"
    # everything else byte-identical
    assert mutated["entity-action"][0]["title"] == atlas["entity-action"][0]["title"]
    assert mutated["entity-action"][0]["desc"] == atlas["entity-action"][0]["desc"]
    assert mutated["entity-action"][0]["badges"][0]["text"] == atlas["entity-action"][0]["badges"][0]["text"]
    # original untouched (apply_diffs deep-copies)
    assert atlas["entity-action"][0]["badges"][0]["cls"] == "gap"


# --- real-file round trip (load-bearing) --------------------------------------------------------


def test_json_block_round_trips_byte_identical_when_unmodified():
    """Proves the reserialize strategy itself is safe: parsing the real file's JSON and dumping it
    back with json.dumps(indent=2, ensure_ascii=False) reproduces it exactly, so any diff the
    regenerator ever produces is attributable only to intentional cls changes."""
    html = _ATLAS_PATH.read_text()
    raw_json, start, end = extract_json_block(html)
    data = json.loads(raw_json)
    reserialized = json.dumps(data, indent=2, ensure_ascii=False)
    assert reserialized == raw_json


def test_real_atlas_has_no_drift_against_the_real_registry():
    """The load-bearing regression test, mirroring the wiring map's own convention: the real
    committed atlas must stay in sync with the real registry going forward."""
    atlas_data = _real_atlas_data()
    states = _real_registry_states()
    diffs = compute_diffs(atlas_data, states)
    assert diffs == [], (
        f"Atlas badge cls has drifted from the registry: {diffs}. "
        f"Run `python3 tools/mechanism_registry/mechanism_atlas_regenerate.py` to fix."
    )


def test_regeneration_never_touches_card_prose_or_idea_level_cards():
    """[Load-bearing per peer review] Regenerating against a mutated registry copy (so there IS
    real diff work to do) must still leave every mapped card's title/fromNote/desc/src and every
    badge's text field byte-identical -- only cls may change, and only for mapped badges."""
    atlas_data = _real_atlas_data()
    states = dict(_real_registry_states())

    # Force real diff work: flip one already-verified-correct mechanism's expected state so the
    # regenerator has something to change, without touching the real registry file.
    flipped_id = "combat_resolution"
    assert flipped_id in states
    original_state = states[flipped_id]
    states[flipped_id] = "gap" if original_state != "gap" else "partial"

    diffs = compute_diffs(atlas_data, states)
    assert diffs, "test fixture setup expected at least one diff to prove prose preservation against"
    mutated = apply_diffs(atlas_data, diffs)

    positions = all_mechanism_card_badge_positions()
    diffed_positions = {(d["section"], d["index"], d["badge_index"]) for d in diffs}

    for mech_id, entries in positions.items():
        for section, index, badge_index in entries:
            orig_card = atlas_data[section][index]
            new_card = mutated[section][index]
            # Every non-cls field on the card itself is untouched.
            for key in ("title", "fromNote", "desc", "src"):
                if key in orig_card:
                    assert new_card.get(key) == orig_card.get(key), (
                        f"{section}#{index} field {key!r} changed -- regenerator must never touch prose"
                    )
            orig_badge = orig_card["badges"][badge_index]
            new_badge = new_card["badges"][badge_index]
            assert new_badge.get("text") == orig_badge.get("text")
            if (section, index, badge_index) in diffed_positions:
                assert new_badge["cls"] != orig_badge["cls"]
            else:
                assert new_badge["cls"] == orig_badge["cls"]

    # Idea-level cards (design-ideas section, or any card absent from the mapping) are identical
    # objects in the untouched sections.
    mapped_keys = {(s, i) for s, i, _ in (pos for entries in positions.values() for pos in entries)}
    for section, cards in atlas_data.items():
        for idx, card in enumerate(cards):
            if (section, idx) not in mapped_keys:
                assert mutated[section][idx] == card, f"untouched card {section}#{idx} changed"
