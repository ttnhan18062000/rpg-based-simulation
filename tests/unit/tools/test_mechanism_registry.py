"""Tests for tools/mechanism_registry.py and docs/brainstorm/mechanisms.yaml.

TCK-20260915-MECHANISM-REGISTRY-FOUNDATION (child of TCK-20260915-EPIC-MECHANISM-REGISTRY).

Per Acceptance Criteria #4: a validator only ever run against good data is indistinguishable from
one that does nothing. Every one of the four invariants below is proven failing on a deliberately
broken fixture, never just passing on a clean one -- and each fixture below is invalid for exactly
one invariant at a time, so a validator that only implements 1 of the 4 checks can't accidentally
pass all six invalid-fixture tests by coincidence.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from tools.mechanism_registry import MechanismRegistry, VALID_STATES, validate

REPO_ROOT = Path(__file__).resolve().parents[3]
_REGISTRY_PATH = REPO_ROOT / "docs" / "brainstorm" / "mechanisms.yaml"


@pytest.fixture(scope="module")
def registry_data():
    with open(_REGISTRY_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def registry():
    return MechanismRegistry()


# ── 1: existence / shape (AC #1, #2, #3) ────────────────────────────────────────────────────


def test_registry_yaml_exists():
    assert _REGISTRY_PATH.exists(), f"mechanisms.yaml missing at {_REGISTRY_PATH}"


def test_registry_has_layers_and_mechanisms_blocks(registry_data):
    assert "layers" in registry_data
    assert "mechanisms" in registry_data
    assert isinstance(registry_data["layers"], dict)
    assert isinstance(registry_data["mechanisms"], list)
    for layer_id, layer_def in registry_data["layers"].items():
        assert "cadence" in layer_def, f"layer '{layer_id}' missing cadence"
        assert "rank" in layer_def, f"layer '{layer_id}' missing rank"
    # AC #3: frequency lives only on layers, never on a mechanism.
    for m in registry_data["mechanisms"]:
        assert "cadence" not in m, f"mechanism '{m.get('id')}' must not carry its own cadence"
        assert "rank" not in m, f"mechanism '{m.get('id')}' must not carry its own rank"
    # AC #2: depends_on is the only hand-authored edge -- no stored dependent-count anywhere.
    for m in registry_data["mechanisms"]:
        assert "dependents" not in m, (
            f"mechanism '{m.get('id')}' must not store a dependent-count "
            "(computed by traversal via MechanismRegistry.dependents_of(), never hand-authored)"
        )


def test_registry_seed_meets_expected_scale(registry_data):
    # Sanity floor, not an exact-count match -- the real corpus-backed count is 75, not the
    # ticket's own 30-50 estimate (see investigation.md). Guards against an accidentally
    # near-empty seed, not against exceeding the original estimate.
    count = len(registry_data["mechanisms"])
    assert count >= 30, f"Registry has only {count} mechanisms (sanity floor: 30)"


def test_no_duplicate_mechanism_ids(registry_data):
    ids = [m["id"] for m in registry_data["mechanisms"]]
    assert len(ids) == len(set(ids)), "duplicate mechanism ids in mechanisms.yaml"


# ── 2: the four invariants, each on a deliberately broken fixture (AC #4) ──────────────────


def test_validator_rejects_unresolved_depends_on():
    fixture = {
        "layers": {"entity": {"cadence": "per_tick", "rank": 1}},
        "mechanisms": [
            {"id": "foo", "layer": "entity", "depends_on": ["nonexistent_id"], "state": "done"},
        ],
    }
    errors = validate(fixture)
    assert errors, "expected a validation failure for an unresolved depends_on id"
    assert any("foo" in e and "nonexistent_id" in e for e in errors), errors


def test_validator_rejects_dependency_cycle_direct():
    fixture = {
        "layers": {"entity": {"cadence": "per_tick", "rank": 1}},
        "mechanisms": [
            {"id": "a", "layer": "entity", "depends_on": ["b"], "state": "done"},
            {"id": "b", "layer": "entity", "depends_on": ["a"], "state": "done"},
        ],
    }
    errors = validate(fixture)
    assert errors, "expected a validation failure for a direct 2-node cycle"
    assert any("cycle" in e.lower() for e in errors), errors


def test_validator_rejects_dependency_cycle_longer():
    # A 3-node cycle, not just a direct pairwise a<->b symmetry -- catches a validator that only
    # checks immediate self-reference instead of running real cycle detection.
    fixture = {
        "layers": {"entity": {"cadence": "per_tick", "rank": 1}},
        "mechanisms": [
            {"id": "a", "layer": "entity", "depends_on": ["b"], "state": "done"},
            {"id": "b", "layer": "entity", "depends_on": ["c"], "state": "done"},
            {"id": "c", "layer": "entity", "depends_on": ["a"], "state": "done"},
        ],
    }
    errors = validate(fixture)
    assert errors, "expected a validation failure for a longer, 3-node cycle"
    assert any("cycle" in e.lower() for e in errors), errors


def test_validator_rejects_undeclared_layer():
    fixture = {
        "layers": {"entity": {"cadence": "per_tick", "rank": 1}},
        "mechanisms": [
            {"id": "foo", "layer": "nonexistent_layer", "depends_on": [], "state": "done"},
        ],
    }
    errors = validate(fixture)
    assert errors, "expected a validation failure for an undeclared layer"
    assert any("foo" in e and "nonexistent_layer" in e for e in errors), errors


def test_validator_rejects_invalid_state():
    fixture = {
        "layers": {"entity": {"cadence": "per_tick", "rank": 1}},
        "mechanisms": [
            {"id": "foo", "layer": "entity", "depends_on": [], "state": "broken"},
        ],
    }
    errors = validate(fixture)
    assert errors, "expected a validation failure for an invalid state"
    assert any("foo" in e and "broken" in e for e in errors), errors


@pytest.mark.parametrize("state", sorted(VALID_STATES))
def test_validator_accepts_every_valid_state(state):
    # Second half of AC #4's invariant-4 proof: confirm the enum boundary is exact, not
    # accidentally permissive on one side -- all six real values must individually pass.
    fixture = {
        "layers": {"entity": {"cadence": "per_tick", "rank": 1}},
        "mechanisms": [
            {"id": "foo", "layer": "entity", "depends_on": [], "state": state},
        ],
    }
    assert validate(fixture) == []


def test_validator_accepts_valid_fixture():
    # Required per AC #4's own warning: a validator only ever run against good data is
    # indistinguishable from one that does nothing. This proves the six invalid-fixture tests
    # above are testing a validator that CAN pass, not one that always fails. Uses real seeded
    # ids from the actual registry so this test doubles as a canary against a future rename.
    fixture = {
        "layers": {"entity": {"cadence": "per_tick", "rank": 1}},
        "mechanisms": [
            {
                "id": "combat_resolution",
                "layer": "entity",
                "depends_on": ["tactical_decision", "combat_engagement"],
                "state": "done",
            },
            {
                "id": "tactical_decision",
                "layer": "entity",
                "depends_on": ["action_pacing_readiness"],
                "state": "done",
            },
            {
                "id": "combat_engagement",
                "layer": "entity",
                "depends_on": ["action_pacing_readiness"],
                "state": "done",
            },
            {
                "id": "action_pacing_readiness",
                "layer": "entity",
                "depends_on": [],
                "state": "partial",
            },
        ],
    }
    assert validate(fixture) == []


def test_real_registry_passes_validation(registry_data):
    # The real committed file must itself pass -- otherwise `make mechanism-registry-validate`
    # would fail on every clean checkout.
    assert validate(registry_data) == []


# ── 3: reader class accessors ────────────────────────────────────────────────────────────────


def test_reader_get_state_known_id(registry):
    assert registry.get_state("combat_resolution") == "done"


def test_reader_get_state_unknown_id(registry):
    assert registry.get_state("nonexistent_mechanism_xyz") is None


def test_reader_all_mechanisms_returns_full_list(registry, registry_data):
    assert len(registry.all_mechanisms()) == len(registry_data["mechanisms"])


def test_reader_dependents_of_is_computed_not_stored(registry):
    # action_pacing_readiness is a real hub -- several mechanisms declare it as a dependency.
    dependents = registry.dependents_of("action_pacing_readiness")
    assert "tactical_decision" in dependents
    assert "combat_engagement" in dependents
    # A leaf with genuinely zero dependents returns an empty list, not an error.
    assert registry.dependents_of("nonexistent_mechanism_xyz") == []


# ── 4: make target (AC #5) ───────────────────────────────────────────────────────────────────


def test_make_target_validates_real_registry():
    result = subprocess.run(
        ["make", "mechanism-registry-validate"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"make mechanism-registry-validate failed:\nstdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )


def test_make_target_fails_on_injected_defect(tmp_path):
    # Never mutate docs/brainstorm/mechanisms.yaml in place -- copy to a tmp_path first, per
    # test_plan.md's own Anti-Drift Test Guard (a test that corrupts the real committed file,
    # even transiently, in a repo whose working directory can be shared across concurrent
    # sessions, is a real hazard).
    broken = tmp_path / "broken_mechanisms.yaml"
    broken.write_text(
        "layers:\n"
        "  entity: {cadence: per_tick, rank: 1}\n"
        "mechanisms:\n"
        "  - id: foo\n"
        "    layer: entity\n"
        "    depends_on: [nonexistent_id]\n"
        "    state: done\n"
    )
    result = subprocess.run(
        [sys.executable, "tools/mechanism_registry.py", str(broken)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert "nonexistent_id" in result.stdout


def test_makefile_wires_mechanism_registry_validate_target():
    makefile_text = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "mechanism-registry-validate:" in makefile_text
    assert "tools/mechanism_registry.py" in makefile_text
