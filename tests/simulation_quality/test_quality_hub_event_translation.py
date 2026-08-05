"""Tests for QualityHub event type translation table.

Verifies that engine event_type values are remapped to SimQ contract vocabulary
before scorer dispatch. Covers all mappings in _TRANSLATE_SIMPLE and _TRANSLATE_CONDITIONAL.
"""
from __future__ import annotations
import uuid
import pytest

from src.observability.events import ObservabilityEventEnvelope
from src.simulation_quality.quality_hub import QualityHub


def _env(event_type: str, payload: dict | None = None) -> ObservabilityEventEnvelope:
    return ObservabilityEventEnvelope(
        event_id=uuid.uuid4().hex,
        run_id="test",
        tick=1,
        entity_id=1,
        event_type=event_type,
        event_category="test",
        severity="INFO",
        source_system="test",
        message="",
        payload=payload or {},
    )


# ── Simple one-to-one translations ──────────────────────────────────────────

@pytest.mark.parametrize("engine_type,contract_type", [
    ("combat_kill",               "entity_killed"),
    ("gold_transaction",          "gold_transferred"),
    ("StrategicObjectiveChanged", "strategic_goal_changed"),
    ("StrategicConcernRaised",    "strategic_goal_changed"),
    ("StrategicDetourCreated",    "project_started"),
    ("StrategicLeadExhausted",    "knowledge_default_fallback"),
    ("leadership_changed",        "diplomatic_transition"),
    ("alliance_formed",           "alliance_accepted"),
])
def test_simple_translation(engine_type: str, contract_type: str) -> None:
    env = _env(engine_type)
    result = QualityHub._translate(env)
    assert result.event_type == contract_type
    assert result.payload.get("_original_event_type") == engine_type


# ── quest_event conditional translations ─────────────────────────────────────

def test_quest_event_started() -> None:
    result = QualityHub._translate(_env("quest_event", {"status": "started"}))
    assert result.event_type == "quest_started"

def test_quest_event_started_no_status() -> None:
    result = QualityHub._translate(_env("quest_event", {}))
    assert result.event_type == "quest_started"

def test_quest_event_completed() -> None:
    result = QualityHub._translate(_env("quest_event", {"status": "completed"}))
    assert result.event_type == "quest_completed"

def test_quest_event_failed() -> None:
    result = QualityHub._translate(_env("quest_event", {"status": "failed"}))
    assert result.event_type == "quest_failed"


# ── lifecycle conditional translations ───────────────────────────────────────

def test_lifecycle_level_up() -> None:
    result = QualityHub._translate(_env("lifecycle", {"action": "level_up"}))
    assert result.event_type == "level_up"

def test_lifecycle_despawn() -> None:
    result = QualityHub._translate(_env("lifecycle", {"action": "despawn"}))
    assert result.event_type == "entity_killed"

def test_lifecycle_death() -> None:
    result = QualityHub._translate(_env("lifecycle", {"action": "death"}))
    assert result.event_type == "entity_killed"

def test_lifecycle_spawn_no_translation() -> None:
    result = QualityHub._translate(_env("lifecycle", {"action": "spawn"}))
    assert result.event_type == "lifecycle"


# ── StrategicProjectChanged conditional translations ─────────────────────────

def test_strategic_project_completed() -> None:
    result = QualityHub._translate(_env("StrategicProjectChanged", {"reason": "completed"}))
    assert result.event_type == "project_completed"

def test_strategic_project_abandoned() -> None:
    result = QualityHub._translate(_env("StrategicProjectChanged", {"reason": "abandoned_by_user"}))
    assert result.event_type == "project_abandoned"

def test_strategic_project_started_default() -> None:
    result = QualityHub._translate(_env("StrategicProjectChanged", {"reason": "new_goal_selected"}))
    assert result.event_type == "project_started"


# ── InvariantViolation conditional translations ──────────────────────────────

def test_invariant_combat_law() -> None:
    result = QualityHub._translate(_env("InvariantViolation", {"law_id": "COMBAT-001"}))
    assert result.event_type == "combat_hard_law_violation"

def test_invariant_conservation_law() -> None:
    result = QualityHub._translate(_env("InvariantViolation", {"law_id": "CONSERVATION-007"}))
    assert result.event_type == "conservation_law_violated"

def test_invariant_unknown_no_translation() -> None:
    result = QualityHub._translate(_env("InvariantViolation", {"law_id": "UNKNOWN-LAW"}))
    assert result.event_type == "InvariantViolation"

def test_invariant_spawn_occupancy_law() -> None:
    result = QualityHub._translate(_env("InvariantViolation", {"law_id": "LAW-SPAWN-OCCUPANCY"}))
    assert result.event_type == "spawn_occupancy_violation"

def test_invariant_unknown_law_id_no_translation() -> None:
    """A law_id that matches none of the known real laws or dormant prefix branches passes
    through untranslated. (Previously this test used LAW-HP-NONNEGATIVE as its "unknown" example
    — that was the exact gap TCK-20260805-SIMQ-HARDLAW-BRIDGE-COVERAGE-GAP closed; see
    test_invariant_hp_nonnegative_routes_to_combat_hard_law below for the corrected behavior.)"""
    result = QualityHub._translate(_env("InvariantViolation", {"law_id": "LAW-DOES-NOT-EXIST"}))
    assert result.event_type == "InvariantViolation"


def test_invariant_hp_nonnegative_routes_to_combat_hard_law() -> None:
    """TCK-20260805-SIMQ-HARDLAW-BRIDGE-COVERAGE-GAP: real HardLawMonitor laws (LAW-* prefixed)
    previously fell through untranslated except LAW-SPAWN-OCCUPANCY. HP/READINESS are
    combat-domain invariants routed to the existing generic combat_hard_law_violation signal."""
    result = QualityHub._translate(_env("InvariantViolation", {"law_id": "LAW-HP-NONNEGATIVE"}))
    assert result.event_type == "combat_hard_law_violation"


def test_invariant_readiness_nonnegative_routes_to_combat_hard_law() -> None:
    result = QualityHub._translate(_env("InvariantViolation", {"law_id": "LAW-READINESS-NONNEGATIVE"}))
    assert result.event_type == "combat_hard_law_violation"


def test_invariant_gold_nonnegative_routes_to_conservation_violated() -> None:
    result = QualityHub._translate(_env("InvariantViolation", {"law_id": "LAW-GOLD-NONNEGATIVE"}))
    assert result.event_type == "conservation_law_violated"


def test_invariant_stamina_position_occupancy_route_to_world_hard_law() -> None:
    for law_id in ("LAW-STAMINA-NONNEGATIVE", "LAW-POSITION-FINITE", "LAW-OCCUPANCY-COLLISION"):
        result = QualityHub._translate(_env("InvariantViolation", {"law_id": law_id}))
        assert result.event_type == "world_hard_law_violation", law_id


# ── Pass-through for unknown types ───────────────────────────────────────────

# ── betrayal_desertion conditional translations ──────────────────────────────

def test_betrayal_desertion_with_faction_routes_to_tension_delta() -> None:
    result = QualityHub._translate(_env("betrayal_desertion", {"faction_id": "faction_a"}))
    assert result.event_type == "faction_tension_delta"
    assert result.payload.get("_original_event_type") == "betrayal_desertion"

def test_betrayal_desertion_without_faction_routes_to_contract_lapsed() -> None:
    result = QualityHub._translate(_env("betrayal_desertion", {}))
    assert result.event_type == "contract_lapsed"
    assert result.payload.get("_original_event_type") == "betrayal_desertion"


# ── Pass-through for unknown types ───────────────────────────────────────────

def test_unknown_event_type_passthrough() -> None:
    env = _env("some_future_event_type")
    result = QualityHub._translate(env)
    assert result is env  # same object — no copy made

def test_action_executed_passthrough() -> None:
    env = _env("action_executed")
    result = QualityHub._translate(env)
    assert result is env


# ── Payload preservation ──────────────────────────────────────────────────────

def test_original_payload_preserved() -> None:
    env = _env("combat_kill", {"attacker_id": 42, "damage": 100})
    result = QualityHub._translate(env)
    assert result.payload["attacker_id"] == 42
    assert result.payload["damage"] == 100
    assert result.payload["_original_event_type"] == "combat_kill"

def test_original_envelope_not_mutated() -> None:
    env = _env("combat_kill", {"x": 1})
    _ = QualityHub._translate(env)
    assert "_original_event_type" not in env.payload
    assert env.event_type == "combat_kill"
