"""Tests for tools/mechanism_registry/registry.py and registries/mechanisms.yaml.

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

from tools.mechanism_registry import (
    MechanismRegistry,
    VALID_INSTRUMENTS,
    VALID_STATES,
    VALID_VERDICTS,
    build_verification_view,
    validate,
    verification_records_from_registry,
)
from tools.mechanism_registry import system_registry as _system_registry_module

REPO_ROOT = Path(__file__).resolve().parents[3]
_REGISTRY_PATH = REPO_ROOT / "registries" / "mechanisms.yaml"


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


def test_real_registry_passes_validation(registry_data, monkeypatch):
    # The real committed file must itself pass -- otherwise `make mechanism-registry-validate`
    # would fail on every clean checkout. Restores the real system registry (conftest.py's own
    # autouse fixture patches it to empty by default for every other test in this file, since
    # they use minimal synthetic fixtures that never declare `systems: []`) -- this is the one
    # test that validates the real, complete file and needs the real registered-systems set.
    import tools.mechanism_registry.registry as _registry_module
    monkeypatch.setattr(_registry_module, "_load_system_registry", _system_registry_module.load_registry)
    assert validate(registry_data) == []


# ── 3: reader class accessors ────────────────────────────────────────────────────────────────


def test_reader_get_state_known_id(registry):
    assert registry.get_state("combat_resolution") == "done"


def test_reader_get_state_unknown_id(registry):
    assert registry.get_state("nonexistent_mechanism_xyz") is None


def test_reader_all_mechanisms_returns_full_list(registry, registry_data):
    assert len(registry.all_mechanisms()) == len(registry_data["mechanisms"])


def test_reader_dependents_of_is_computed_not_stored(registry):
    # TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT (2026-09-18) removed 6 of the 8
    # "* -> action_pacing_readiness" edges declared here (tactical_decision, combat_engagement,
    # movement, readiness_speed_scaling, interaction_channeling, entity_trade, team_up): none of
    # those mechanisms' own real code ever reads readiness as a data input -- they only WRITE
    # readiness_delta as an output cost, and the actual gate lives entirely in the caller
    # (LegalityServiceV2/action_router.py), not in the dependent's own logic. `conversation` was
    # the sole surviving edge, recorded UNCLASSIFIABLE by that audit -- then REMOVED
    # (TCK-20260918-MECHANISM-UNCLASSIFIABLE-DEPENDS-ON-EDGES-RESOLUTION, 2026-09-19): confirmed no
    # "conversation" implementation exists anywhere (its own `state: gap` already said so), so a
    # depends_on edge declared from it cannot be verified.
    dependents = registry.dependents_of("action_pacing_readiness")
    assert dependents == []
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
    # Never mutate registries/mechanisms.yaml in place -- copy to a tmp_path first, per
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
        [sys.executable, "tools/mechanism_registry/registry.py", str(broken)],
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
    assert "tools/mechanism_registry/registry.py" in makefile_text


# ── TCK-20260915-MECHANISM-VERIFICATION-AXIS ─────────────────────────────────────────────────


def _valid_verified_block(instrument="code_trace", verdict="observed"):
    return {"instrument": instrument, "verdict": verdict, "date": "2026-09-16", "note": "x"}


def test_validator_rejects_unknown_instrument():
    fixture = {
        "layers": {"entity": {"cadence": "per_tick", "rank": 1}},
        "mechanisms": [
            {"id": "foo", "layer": "entity", "depends_on": [], "state": "done",
             "verified": _valid_verified_block(instrument="made_up_instrument")},
        ],
    }
    errors = validate(fixture)
    assert errors, "expected a validation failure for an unknown verified.instrument"
    assert any("foo" in e and "made_up_instrument" in e for e in errors), errors


def test_validator_rejects_unknown_verdict():
    fixture = {
        "layers": {"entity": {"cadence": "per_tick", "rank": 1}},
        "mechanisms": [
            {"id": "foo", "layer": "entity", "depends_on": [], "state": "done",
             "verified": _valid_verified_block(verdict="made_up_verdict")},
        ],
    }
    errors = validate(fixture)
    assert errors, "expected a validation failure for an unknown verified.verdict"
    assert any("foo" in e and "made_up_verdict" in e for e in errors), errors


def test_validator_rejects_incomplete_verified_block():
    fixture = {
        "layers": {"entity": {"cadence": "per_tick", "rank": 1}},
        "mechanisms": [
            {"id": "foo", "layer": "entity", "depends_on": [], "state": "done",
             "verified": {"instrument": "code_trace", "verdict": "observed"}},  # missing date/note
        ],
    }
    errors = validate(fixture)
    assert errors, "expected a validation failure for a verified block missing required fields"
    assert any("foo" in e and "date" in e for e in errors), errors


def test_validator_rejects_implemented_by_not_a_list():
    fixture = {
        "layers": {"entity": {"cadence": "per_tick", "rank": 1}},
        "mechanisms": [
            {"id": "foo", "layer": "entity", "depends_on": [], "state": "done",
             "implemented_by": "tools/mechanism_registry/registry.py"},
        ],
    }
    errors = validate(fixture)
    assert errors, "expected a validation failure for a non-list implemented_by"
    assert any("foo" in e and "implemented_by" in e for e in errors), errors


def test_validator_rejects_implemented_by_nonexistent_path():
    """[Load-bearing] TCK-20260916-MECHANISM-IMPLEMENTED-BY-BINDING's whole point: a deleted
    implementing module must fail validation immediately, not silently keep a stale citation."""
    fixture = {
        "layers": {"entity": {"cadence": "per_tick", "rank": 1}},
        "mechanisms": [
            {"id": "foo", "layer": "entity", "depends_on": [], "state": "done",
             "implemented_by": ["src/this/path/does/not/exist.py"]},
        ],
    }
    errors = validate(fixture)
    assert errors, "expected a validation failure for a nonexistent implemented_by path"
    assert any("foo" in e and "exist.py" in e for e in errors), errors


def test_validator_accepts_implemented_by_real_existing_path():
    fixture = {
        "layers": {"entity": {"cadence": "per_tick", "rank": 1}},
        "mechanisms": [
            {"id": "foo", "layer": "entity", "depends_on": [], "state": "done",
             "implemented_by": ["tools/mechanism_registry/registry.py"]},
        ],
    }
    assert validate(fixture) == []


def test_validator_accepts_absent_implemented_by():
    """implemented_by is optional -- a mechanism with none is still valid (the field grows
    organically, per peer review, not backfilled all at once)."""
    fixture = {
        "layers": {"entity": {"cadence": "per_tick", "rank": 1}},
        "mechanisms": [
            {"id": "foo", "layer": "entity", "depends_on": [], "state": "done"},
        ],
    }
    assert validate(fixture) == []


# ── implemented_by symbol-level and method-level binding (TCK-20260916-MECHANISM-IMPLEMENTED-BY-
# SYMBOL-LEVEL-BINDING, TCK-20260920-MECHANISM-ENTITY-LAYER-UNBOUND-CLAIMS-RESOLUTION) ──


def test_parse_implemented_by_entry_splits_path_only():
    from tools.mechanism_registry.registry import parse_implemented_by_entry

    assert parse_implemented_by_entry("src/engine/registry.py") == ("src/engine/registry.py", None)


def test_parse_implemented_by_entry_splits_symbol_level():
    from tools.mechanism_registry.registry import parse_implemented_by_entry

    assert parse_implemented_by_entry("src/x.py::MyClass") == ("src/x.py", "MyClass")


def test_parse_implemented_by_entry_keeps_method_level_symbol_whole():
    """A third `::` segment (method-level) is not split further here -- it is passed whole to
    symbol_defined_in_file, the one place that distinction is interpreted."""
    from tools.mechanism_registry.registry import parse_implemented_by_entry

    assert parse_implemented_by_entry("src/x.py::MyClass::my_method") == (
        "src/x.py",
        "MyClass::my_method",
    )


def test_validator_accepts_symbol_level_top_level_class():
    fixture = {
        "layers": {"entity": {"cadence": "per_tick", "rank": 1}},
        "mechanisms": [
            {"id": "foo", "layer": "entity", "depends_on": [], "state": "done",
             "implemented_by": ["tools/mechanism_registry/registry.py::MechanismRegistry"]},
        ],
    }
    assert validate(fixture) == []


def test_validator_rejects_symbol_level_nonexistent_class():
    fixture = {
        "layers": {"entity": {"cadence": "per_tick", "rank": 1}},
        "mechanisms": [
            {"id": "foo", "layer": "entity", "depends_on": [], "state": "done",
             "implemented_by": ["tools/mechanism_registry/registry.py::NoSuchClass"]},
        ],
    }
    errors = validate(fixture)
    assert errors, "expected a validation failure for a nonexistent symbol"
    assert any("NoSuchClass" in e for e in errors), errors


def test_validator_accepts_method_level_real_method_on_real_class():
    """[Load-bearing] The method-level binding this ticket adds: a real method that only exists
    inside a specific class's own body, not just anywhere in the file."""
    fixture = {
        "layers": {"entity": {"cadence": "per_tick", "rank": 1}},
        "mechanisms": [
            {"id": "foo", "layer": "entity", "depends_on": [], "state": "done",
             "implemented_by": [
                 "tools/mechanism_registry/registry.py::MechanismRegistry::get_state"
             ]},
        ],
    }
    assert validate(fixture) == []


def test_validator_rejects_method_level_wrong_class():
    """[Load-bearing] A method that's real but lives on a DIFFERENT class must fail -- proves the
    check is bounded to the named class's own body, not "does this method exist anywhere in the
    file" (which symbol-level would already accept and method-level must not silently degrade to)."""
    fixture = {
        "layers": {"entity": {"cadence": "per_tick", "rank": 1}},
        "mechanisms": [
            # get_state is real, but defined on MechanismRegistry, not on `validate`'s own
            # (non-existent) class form -- MechanismRegistry itself has no `_dfs` method (that's
            # a nested function inside module-level `validate()`, not a class method at all).
            {"id": "foo", "layer": "entity", "depends_on": [], "state": "done",
             "implemented_by": [
                 "tools/mechanism_registry/registry.py::MechanismRegistry::_dfs"
             ]},
        ],
    }
    errors = validate(fixture)
    assert errors, "expected a validation failure for a method bound to the wrong class"
    assert any("_dfs" in e and "method" in e for e in errors), errors


def test_validator_rejects_method_level_nonexistent_method():
    fixture = {
        "layers": {"entity": {"cadence": "per_tick", "rank": 1}},
        "mechanisms": [
            {"id": "foo", "layer": "entity", "depends_on": [], "state": "done",
             "implemented_by": [
                 "tools/mechanism_registry/registry.py::MechanismRegistry::no_such_method"
             ]},
        ],
    }
    errors = validate(fixture)
    assert errors, "expected a validation failure for a nonexistent method"
    assert any("no_such_method" in e for e in errors), errors


def test_validator_rejects_method_level_nonexistent_class():
    fixture = {
        "layers": {"entity": {"cadence": "per_tick", "rank": 1}},
        "mechanisms": [
            {"id": "foo", "layer": "entity", "depends_on": [], "state": "done",
             "implemented_by": [
                 "tools/mechanism_registry/registry.py::NoSuchClass::some_method"
             ]},
        ],
    }
    errors = validate(fixture)
    assert errors, "expected a validation failure when the class itself doesn't exist"
    assert any("NoSuchClass" in e for e in errors), errors


def test_symbol_defined_in_file_bounds_method_lookup_to_its_own_class():
    """Direct unit test of the boundary logic: two classes in one file, same method name on
    neither/one/the other -- confirms the class-body slice stops at the next top-level class/def,
    not at end of file."""
    from tools.mechanism_registry.registry import symbol_defined_in_file

    tmp_text = (
        "class First:\n"
        "    def shared_name(self):\n"
        "        pass\n"
        "\n"
        "class Second:\n"
        "    def other(self):\n"
        "        pass\n"
    )
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(tmp_text)
        tmp_path = Path(f.name)
    try:
        assert symbol_defined_in_file(tmp_path, "First::shared_name") is True
        assert symbol_defined_in_file(tmp_path, "Second::shared_name") is False
        assert symbol_defined_in_file(tmp_path, "Second::other") is True
        assert symbol_defined_in_file(tmp_path, "First::other") is False
    finally:
        tmp_path.unlink()


# ── invariant 8: unaudited_depends_on_edges (TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT) ──


def test_validator_accepts_absent_unaudited_depends_on_edges():
    fixture = {
        "layers": {"entity": {"cadence": "per_tick", "rank": 1}},
        "mechanisms": [
            {"id": "foo", "layer": "entity", "depends_on": ["bar"], "state": "done"},
            {"id": "bar", "layer": "entity", "depends_on": [], "state": "done"},
        ],
    }
    assert validate(fixture) == []


def test_validator_accepts_unaudited_edge_matching_a_real_depends_on_pair():
    fixture = {
        "layers": {"entity": {"cadence": "per_tick", "rank": 1}},
        "mechanisms": [
            {"id": "foo", "layer": "entity", "depends_on": ["bar"], "state": "done"},
            {"id": "bar", "layer": "entity", "depends_on": [], "state": "done"},
        ],
        "unaudited_depends_on_edges": [["foo", "bar"]],
    }
    assert validate(fixture) == []


def test_validator_rejects_unaudited_edge_that_is_not_a_declared_depends_on():
    fixture = {
        "layers": {"entity": {"cadence": "per_tick", "rank": 1}},
        "mechanisms": [
            {"id": "foo", "layer": "entity", "depends_on": [], "state": "done"},
            {"id": "bar", "layer": "entity", "depends_on": [], "state": "done"},
        ],
        # foo does not depend_on bar in this fixture -- stale marker.
        "unaudited_depends_on_edges": [["foo", "bar"]],
    }
    errors = validate(fixture)
    assert errors, "expected a validation failure for an unaudited edge with no matching depends_on"
    assert any("foo" in e and "bar" in e and "stale" in e.lower() for e in errors), errors


def test_validator_rejects_unaudited_edge_naming_unknown_mechanism():
    fixture = {
        "layers": {"entity": {"cadence": "per_tick", "rank": 1}},
        "mechanisms": [
            {"id": "foo", "layer": "entity", "depends_on": [], "state": "done"},
        ],
        "unaudited_depends_on_edges": [["nonexistent_mechanism", "foo"]],
    }
    errors = validate(fixture)
    assert errors, "expected a validation failure for an unaudited edge naming an unknown mechanism"
    assert any("nonexistent_mechanism" in e for e in errors), errors


def test_real_registry_unaudited_edges_all_resolve(registry_data, monkeypatch):
    """The real committed registry's own unaudited_depends_on_edges list validates clean -- every
    entry names a currently-declared depends_on edge, none stale."""
    import tools.mechanism_registry.registry as _registry_module
    monkeypatch.setattr(_registry_module, "_load_system_registry", _system_registry_module.load_registry)
    assert validate(registry_data) == []


# ── invariants 9/10: mechanism `systems: []` membership (TCK-20260918-MECHANISM-SYSTEM-
# MEMBERSHIP-FOUNDATION) — conftest.py's own autouse fixture patches the registered-systems
# lookup to empty for every test that doesn't explicitly override it, so these tests set up their
# own small registry via monkeypatch, deliberately invalid one invariant at a time, per AC #3
# ("not proven by a clean pass on valid data").


def _fixture_registry(monkeypatch, systems: dict):
    """Patches the system-registry lookup registry.py::validate() reads, to the given
    {system_name: entry_dict} mapping, for the duration of one test."""
    import tools.mechanism_registry.registry as _registry_module
    monkeypatch.setattr(_registry_module, "_load_system_registry", lambda *a, **kw: dict(systems))


def test_validator_accepts_mechanism_declaring_a_registered_system(monkeypatch):
    _fixture_registry(monkeypatch, {"combat": {"system": "combat", "added_date": "2026-09-19"}})
    fixture = {
        "layers": {"entity": {"cadence": "per_tick", "rank": 1}},
        "mechanisms": [
            {"id": "foo", "layer": "entity", "depends_on": [], "state": "done", "systems": ["combat"]},
        ],
    }
    assert validate(fixture) == []


def test_validator_rejects_mechanism_declaring_unregistered_system(monkeypatch):
    _fixture_registry(monkeypatch, {"combat": {"system": "combat", "added_date": "2026-09-19"}})
    fixture = {
        "layers": {"entity": {"cadence": "per_tick", "rank": 1}},
        "mechanisms": [
            {"id": "foo", "layer": "entity", "depends_on": [], "state": "done", "systems": ["not_a_real_system"]},
        ],
    }
    errors = validate(fixture)
    assert errors, "expected a validation failure for an unregistered system reference"
    assert any("foo" in e and "not_a_real_system" in e for e in errors), errors


def test_validator_rejects_registered_system_with_zero_members(monkeypatch):
    _fixture_registry(monkeypatch, {
        "combat": {"system": "combat", "added_date": "2026-09-19"},
        "economy": {"system": "economy", "added_date": "2026-09-19"},
    })
    fixture = {
        "layers": {"entity": {"cadence": "per_tick", "rank": 1}},
        "mechanisms": [
            # Only "combat" is ever declared -- "economy" is registered but orphan.
            {"id": "foo", "layer": "entity", "depends_on": [], "state": "done", "systems": ["combat"]},
        ],
    }
    errors = validate(fixture)
    assert errors, "expected a validation failure for a registered system with zero members"
    assert any("economy" in e and "orphan" in e.lower() for e in errors), errors
    # combat has a real member -- must NOT be reported as orphan alongside economy.
    assert not any("'combat' is registered" in e for e in errors), errors


def test_validator_accepts_multi_system_mechanism(monkeypatch):
    """AC #2: systems: [] accepts multiple values -- a mechanism with 2 real, registered systems
    must not trip either invariant."""
    _fixture_registry(monkeypatch, {
        "combat": {"system": "combat", "added_date": "2026-09-19"},
        "world": {"system": "world", "added_date": "2026-09-19"},
    })
    fixture = {
        "layers": {"entity": {"cadence": "per_tick", "rank": 1}},
        "mechanisms": [
            {"id": "movement", "layer": "entity", "depends_on": [], "state": "done", "systems": ["combat", "world"]},
        ],
    }
    assert validate(fixture) == []


def test_validator_accepts_mechanism_with_no_systems_field_at_all(monkeypatch):
    """A mechanism that omits `systems:` entirely (not yet assigned) must not itself trip the
    missing-system invariant -- absence is handled by mechanisms_by_system()'s own "unassigned"
    bucket (AC #4/#5), not by validate() rejecting the omission."""
    _fixture_registry(monkeypatch, {"combat": {"system": "combat", "added_date": "2026-09-19"}})
    fixture = {
        "layers": {"entity": {"cadence": "per_tick", "rank": 1}},
        "mechanisms": [
            {"id": "foo", "layer": "entity", "depends_on": [], "state": "done", "systems": ["combat"]},
            {"id": "bar", "layer": "entity", "depends_on": [], "state": "done"},  # no systems key
        ],
    }
    assert validate(fixture) == []


def test_real_registry_systems_all_resolve(registry_data, monkeypatch):
    """The real committed registry's own systems: [] declarations validate clean against the
    real registries/system_registry.jsonl -- no missing, no orphan."""
    import tools.mechanism_registry.registry as _registry_module
    monkeypatch.setattr(_registry_module, "_load_system_registry", _system_registry_module.load_registry)
    assert validate(registry_data) == []


# ── mechanisms_by_system() — AC #4/#5: a mechanism with no system must be proven to RENDER, not
# just checked for absence of a validation error.


def test_mechanisms_by_system_groups_declared_membership(monkeypatch):
    from tools.mechanism_registry import mechanisms_by_system
    _fixture_registry(monkeypatch, {
        "combat": {"system": "combat", "added_date": "2026-09-19"},
        "economy": {"system": "economy", "added_date": "2026-09-19"},
    })
    fixture = {
        "layers": {"entity": {"cadence": "per_tick", "rank": 1}},
        "mechanisms": [
            {"id": "foo", "layer": "entity", "depends_on": [], "state": "done", "systems": ["combat"]},
            {"id": "bar", "layer": "entity", "depends_on": [], "state": "done", "systems": ["combat", "economy"]},
        ],
    }
    result = mechanisms_by_system(fixture)
    assert result["combat"] == ["bar", "foo"]
    assert result["economy"] == ["bar"]


def test_mechanisms_by_system_renders_unassigned_mechanism_by_presence(monkeypatch):
    """AC #5: proven by asserting the unassigned mechanism's own id is PRESENT in the output --
    not by checking the assigned rows look right, which an omission bug would not catch."""
    from tools.mechanism_registry import mechanisms_by_system
    _fixture_registry(monkeypatch, {"combat": {"system": "combat", "added_date": "2026-09-19"}})
    fixture = {
        "layers": {"entity": {"cadence": "per_tick", "rank": 1}},
        "mechanisms": [
            {"id": "foo", "layer": "entity", "depends_on": [], "state": "done", "systems": ["combat"]},
            {"id": "orphan_mech", "layer": "entity", "depends_on": [], "state": "done"},  # no systems
        ],
    }
    result = mechanisms_by_system(fixture)
    assert "unassigned" in result, "the unassigned key must always be present, even with zero members"
    assert "orphan_mech" in result["unassigned"], (
        "a mechanism with no systems: [] must render under 'unassigned', not be silently dropped"
    )
    assert "orphan_mech" not in result["combat"]


def test_mechanisms_by_system_unassigned_present_but_empty_when_all_mechanisms_assigned(monkeypatch):
    from tools.mechanism_registry import mechanisms_by_system
    _fixture_registry(monkeypatch, {"combat": {"system": "combat", "added_date": "2026-09-19"}})
    fixture = {
        "layers": {"entity": {"cadence": "per_tick", "rank": 1}},
        "mechanisms": [
            {"id": "foo", "layer": "entity", "depends_on": [], "state": "done", "systems": ["combat"]},
        ],
    }
    result = mechanisms_by_system(fixture)
    assert result["unassigned"] == []


def test_real_registry_zero_unassigned_mechanisms(registry_data, monkeypatch):
    """The real committed registry has all 93 mechanisms assigned (per the value investigation's
    own broad pass) -- pinned so a future mechanism landing with no systems: [] is caught here,
    not silently rendered as 'unassigned' with nobody noticing."""
    from tools.mechanism_registry import mechanisms_by_system
    import tools.mechanism_registry.registry as _registry_module
    monkeypatch.setattr(_registry_module, "_load_system_registry", _system_registry_module.load_registry)
    result = mechanisms_by_system(registry_data)
    assert result["unassigned"] == [], (
        f"expected zero unassigned mechanisms in the real registry, found: {result['unassigned']}"
    )
    unaudited = registry_data.get("unaudited_depends_on_edges") or []
    assert len(unaudited) == 0, (
        f"expected 0 unaudited edges (TCK-20260920-MECHANISM-ENTITY-LAYER-UNBOUND-CLAIMS-"
        f"RESOLUTION resolved the last 2, the motivation_doctrine pair, on 2026-09-20 -- both "
        f"removed from motivation_doctrine's own depends_on as unauditable against deleted code "
        f"with no evidence of ever being a genuine functional dependency; all 17 original edges "
        f"from TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT are now resolved), "
        f"found {len(unaudited)} -- if this genuinely changed, update this pinned count with a "
        f"citation, don't just adjust the number"
    )


@pytest.mark.parametrize("instrument", sorted(VALID_INSTRUMENTS))
def test_validator_accepts_all_four_instruments(instrument):
    fixture = {
        "layers": {"entity": {"cadence": "per_tick", "rank": 1}},
        "mechanisms": [
            {"id": "foo", "layer": "entity", "depends_on": [], "state": "done",
             "verified": _valid_verified_block(instrument=instrument)},
        ],
    }
    assert validate(fixture) == []


@pytest.mark.parametrize("verdict", sorted(VALID_VERDICTS))
def test_validator_accepts_all_three_verdicts(verdict):
    fixture = {
        "layers": {"entity": {"cadence": "per_tick", "rank": 1}},
        "mechanisms": [
            {"id": "foo", "layer": "entity", "depends_on": [], "state": "done",
             "verified": _valid_verified_block(verdict=verdict)},
        ],
    }
    assert validate(fixture) == []


def test_verification_view_includes_every_mechanism_even_unverified():
    # The load-bearing test per AC #2's own instruction: assert presence, not absence. A test
    # that only checks the verified row looks right is blind to an omission bug -- this arc's own
    # recurring failure shape.
    mechanisms = [
        {"id": "verified_one", "layer": "entity", "state": "done"},
        {"id": "unverified_one", "layer": "entity", "state": "gap"},
    ]
    records = {"verified_one": [_valid_verified_block()]}
    view = build_verification_view(records, mechanisms)
    ids_in_view = {row["id"] for row in view}
    assert "unverified_one" in ids_in_view, "unverified mechanism was omitted, not rendered"
    assert "verified_one" in ids_in_view
    assert len(view) == 2


def test_verification_view_unverified_row_shape():
    mechanisms = [{"id": "unverified_one", "layer": "entity", "state": "gap"}]
    view = build_verification_view({}, mechanisms)
    row = view[0]
    assert row["verified"] is False
    assert row["verdict"] == "unverified"
    assert row["instrument"] is None


def test_verification_view_collapses_multiple_records_to_latest():
    mechanisms = [{"id": "foo", "layer": "entity", "state": "done"}]
    records = {
        "foo": [
            {"instrument": "code_trace", "verdict": "observed", "date": "2026-08-01",
             "note": "older"},
            {"instrument": "scenario", "verdict": "contradicted", "date": "2026-09-16",
             "note": "newer"},
        ]
    }
    view = build_verification_view(records, mechanisms)
    assert len(view) == 1, "multiple records for one mechanism must collapse to a single row"
    row = view[0]
    assert row["date"] == "2026-09-16"
    assert row["verdict"] == "contradicted"
    assert row["note"] == "newer"


def test_verification_view_groups_static_evidence_separately_from_runtime():
    mechanisms = [
        {"id": "runtime_one", "layer": "entity", "state": "done"},
        {"id": "static_one", "layer": "entity", "state": "done"},
        {"id": "unverified_one", "layer": "entity", "state": "gap"},
    ]
    records = {
        "runtime_one": [_valid_verified_block(instrument="scenario")],
        "static_one": [_valid_verified_block(instrument="code_trace")],
    }
    view = build_verification_view(records, mechanisms)
    order = [row["id"] for row in view]
    assert order.index("runtime_one") < order.index("static_one") < order.index("unverified_one")


def test_real_registry_verification_view_seeds_non_empty(registry_data):
    records = verification_records_from_registry(registry_data)
    view = build_verification_view(records, registry_data["mechanisms"])
    assert len(view) == len(registry_data["mechanisms"])

    by_id = {row["id"]: row for row in view}
    expected = {
        "combat_engagement": "scenario",
        "succession": "code_trace",
        "self_model": "code_trace",
        "information_trust_deception": "code_trace",
        "opportunity_rumor_seeds": "code_trace",
        "cross_episode_grief_nemesis": "code_trace",
    }
    for mech_id, instrument in expected.items():
        assert by_id[mech_id]["verified"] is True
        assert by_id[mech_id]["instrument"] == instrument
        assert by_id[mech_id]["verdict"] == "observed"


def test_reader_get_verification_known_and_unknown(registry):
    verified = registry.get_verification("combat_engagement")
    assert verified is not None
    assert verified["instrument"] == "scenario"
    assert registry.get_verification("succession")["instrument"] == "code_trace"
    assert registry.get_verification("clan") is None  # real, unverified id -- `movement` itself
    # was this example until TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN gave it a
    # real verified block (batch 3 of the unbound-claims program); swapped to `clan`, still
    # genuinely unverified as of this edit.
    assert registry.get_verification("nonexistent_mechanism_xyz") is None  # unknown id


def test_make_target_generates_verification_view():
    result = subprocess.run(
        ["make", "mechanism-verification-view"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"make mechanism-verification-view failed:\nstdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )
    # The real committed output must already be in sync with the real registry -- run the
    # script's own --check mode against the real files, never hand-diff.
    check = subprocess.run(
        [sys.executable, "tools/mechanism_registry/generate_mechanism_verification_view.py", "--check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert check.returncode == 0, check.stdout + check.stderr


def test_generator_check_mode_detects_staleness(tmp_path):
    # Never mutate the real committed output -- write to a tmp_path output instead, matching
    # this file's own established discipline for real-file-adjacent subprocess tests.
    stale_output = tmp_path / "stale_view.md"
    stale_output.write_text("this is not the real generated content\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "tools/mechanism_registry/generate_mechanism_verification_view.py",
         "--output", str(stale_output), "--check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert "STALE" in result.stdout


def test_makefile_wires_mechanism_verification_view_target():
    makefile_text = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "mechanism-verification-view:" in makefile_text
    assert "tools/mechanism_registry/generate_mechanism_verification_view.py" in makefile_text
