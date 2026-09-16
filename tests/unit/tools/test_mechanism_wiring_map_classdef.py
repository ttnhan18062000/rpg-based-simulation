"""Tests for tools/mechanism_registry/mechanism_wiring_map_classdef.py -- derives the wiring map's Entity Operating
Loop diagram's classDef state colouring from the real mechanism registry.

TCK-20260915-MECHANISM-PRIORITY-DERIVATION Scope item 3 (the real part, per peer review: only the
classDef state colouring derives from the registry, not the diagram's own topology).
"""
from __future__ import annotations

from pathlib import Path

from tools.mechanism_registry.mechanism_wiring_map_classdef import (
    OPERATING_LOOP_NODE_TO_MECHANISM_ID,
    STATE_TO_CLASSDEF,
    compute_expected_classdef,
    find_drift,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
_WIRING_MAP_PATH = REPO_ROOT / "docs" / "brainstorm" / "rpg_simulation_wiring_map.html"
_REGISTRY_PATH = REPO_ROOT / "docs" / "brainstorm" / "mechanisms.yaml"


def _fake_registry(states: dict) -> dict:
    return {"mechanisms": [{"id": mid, "state": state} for mid, state in states.items()]}


def test_compute_expected_classdef_maps_states_correctly():
    registry = _fake_registry({
        "combat_resolution": "done",
        "self_model": "gated",
        "conversation": "gap",
        "causal_spatial_memory": "orphan",
    })
    expected = compute_expected_classdef(registry)
    assert expected["CMB"] == "live"    # combat_resolution -> done -> live
    assert expected["SELF"] == "gated"  # self_model -> gated -> gated
    assert expected["CNV"] == "bug"     # conversation -> gap -> bug
    assert expected["MEM"] == "bug"     # causal_spatial_memory -> orphan -> bug


def test_find_drift_detects_a_real_mismatch():
    # Fixture wiring map text: SELF has no inline class and isn't in the "live" list either
    # (simulating a node the diagram simply never colored), while the registry says it's gated.
    registry = _fake_registry({"self_model": "gated"})
    text = 'SELF["Self-Model"]\nclass PER live\n'
    drift = find_drift(registry, text)
    assert "SELF" in drift
    assert drift["SELF"]["expected"] == "gated"


def test_find_drift_reports_nothing_when_diagram_agrees_with_registry():
    registry = _fake_registry({"self_model": "gated"})
    text = 'SELF["Self-Model"]:::gated\n'
    drift = find_drift(registry, text)
    assert "SELF" not in drift


def test_dec_has_no_registry_mapping():
    # Decide Route has no corresponding registry mechanism id -- deliberately excluded, not
    # silently guessed.
    assert "DEC" not in OPERATING_LOOP_NODE_TO_MECHANISM_ID


def test_all_state_classes_have_a_classdef_mapping():
    from tools.mechanism_registry import VALID_STATES
    for state in VALID_STATES:
        assert state in STATE_TO_CLASSDEF, f"no classDef mapping for state '{state}'"


def test_real_wiring_map_has_no_drift_against_the_real_registry():
    # The load-bearing regression test: the real committed file must stay in sync with the real
    # registry going forward, not just at the moment of the one-time fix. Re-derives on every run.
    import yaml
    with open(_REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = yaml.safe_load(f)
    text = _WIRING_MAP_PATH.read_text(encoding="utf-8")
    drift = find_drift(registry, text)
    assert drift == {}, (
        f"Entity Operating Loop diagram has drifted from the registry: {drift}. "
        f"Run `python3 tools/mechanism_registry/mechanism_wiring_map_classdef.py` for a readable report."
    )


def test_every_mapped_mechanism_id_exists_in_the_real_registry():
    import yaml
    with open(_REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = yaml.safe_load(f)
    real_ids = {m["id"] for m in registry["mechanisms"]}
    for node, mech_id in OPERATING_LOOP_NODE_TO_MECHANISM_ID.items():
        assert mech_id in real_ids, f"node '{node}' maps to unknown mechanism id '{mech_id}'"
