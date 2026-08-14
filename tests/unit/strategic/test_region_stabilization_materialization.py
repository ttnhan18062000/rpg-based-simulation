"""
Integration tests for the tier-5 REGION_STABILIZATION materialization branch
(TCK-20260811-REGION-STABILIZATION-GOAL-SCORER, plan.md Step 6/Step 8).

Covers AC3 (arbitration clears with no current project), AC5/AC6 (materialization uses
metadata["raw_score"], never best_candidate.utility, and a real ProjectKind member),
Design Decision #4 (the resume/dedup lookup stays inert for REGION_STABILIZATION winners),
New Finding #7 (shared 2.9-ceiling score scale), and New Finding #8 (target_pos is tactically
resolvable via the region centroid, not a stall).
"""
from __future__ import annotations

import ast

import pytest

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, RegionState
from src.core.strategic import (
    GoalKind, ProjectKind, ObjectiveKind, ProjectState, ProjectStatus,
)
from src.engine.tactical import TacticalDecisionSystem
from src.systems.strategic import StrategicIntelligenceSystem
from src.systems.strategic_systems.intelligence import _score_scale_max, _ADVENTURE_ROUTE_SCORE_MAX


def _entity(eid=1, pos=(5.0, 5.0), projects=None, current_project_id=None,
            hp=None, max_hp=None, interruption_resistance=None):
    builder = V2EntityBuilder(eid).kind("hero").location(*pos)
    if projects is not None or current_project_id is not None:
        builder = builder.strategic(
            projects=projects or {},
            current_project_id=current_project_id,
        )
    if hp is not None or max_hp is not None:
        builder = builder.combat(hp=hp, max_hp=max_hp)
    if interruption_resistance is not None:
        builder = builder.cognition(interruption_resistance=interruption_resistance)
    return builder.build()


def _state(entities=None, regions=None, tick=0):
    return AuthoritativeState(
        tick=tick, seed=42, entities=entities or {}, regions=regions or {}
    )


# High-hazard region used across several tests below: hazard_level=0.95 -> urgency =
# min(1.0,(0.95-0.7)/0.3) = 0.8333333333333333 -> raw_score = urgency*2.9 = 2.4166666666666665.
_SWAMP_HIGH_HAZARD = RegionState(
    id="swamp", name="Swamp", bounds=(0, 0, 10, 10), hazard_level=0.95
)


def test_active_region_stabilization_wins_arbitration_with_no_current_project():
    entity = _entity()
    state = _state(entities={1: entity}, regions={"swamp": _SWAMP_HIGH_HAZARD}, tick=0)

    result = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)

    assert result is not None
    assert result.current_project_id_set == "project_stabilize_swamp_t0"
    assert len(result.projects_add_or_update) == 1
    assert result.projects_add_or_update[0].id == "project_stabilize_swamp_t0"


def test_region_stabilization_winner_materializes_with_raw_score_not_utility():
    """AC5/AC6: ProjectState.score must equal the RAW score (2.4166666666666665), never the
    normalized utility ((2.4166666666666665/2.9)*100 ~= 83.33) -- a regression here silently
    reproduces TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG's defect class."""
    entity = _entity()
    state = _state(entities={1: entity}, regions={"swamp": _SWAMP_HIGH_HAZARD}, tick=0)

    result = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)

    assert result is not None
    project = result.projects_add_or_update[0]
    expected_utility = (2.4166666666666665 / 2.9) * 100.0

    assert project.score == pytest.approx(2.4166666666666665)
    assert project.score != pytest.approx(expected_utility)


def test_region_stabilization_materialized_kind_is_real_project_kind_enum_member():
    entity = _entity()
    state = _state(entities={1: entity}, regions={"swamp": _SWAMP_HIGH_HAZARD}, tick=0)

    result = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)

    project = result.projects_add_or_update[0]
    assert project.kind == ProjectKind.STABILIZE
    assert project.kind != GoalKind.REGION_STABILIZATION
    assert project.objectives[0].kind == ObjectiveKind.INVESTIGATE


def test_high_lock_current_project_retains_against_low_urgency_regional_danger():
    """hp is deliberately below the 80% _threat_resolved() early-release threshold (50/100 ->
    0.5) so the locked-branch's normalized comparison actually runs instead of being
    unconditionally bypassed by evaluate_project_switch()'s threat-resolved short-circuit.

    current: kind=GoalKind.HARVESTING, score=90.0, lock_until_tick=150 (> tick=100), default
    profile (interruption_resistance=0.3, resistance_multiplier=30.0) -> retention_margin=9.0.
    current_max=_score_scale_max(GoalKind.HARVESTING)=100.0 -> current_pct=0.9;
    normalized_effective_current_pct = 0.9 + 9.0/100 = 0.99.

    Low-urgency region (hazard_level=0.72): urgency=min(1.0,(0.72-0.7)/0.3)=0.06666...;
    raw_score=urgency*2.9=0.19333... candidate_pct=raw_score/2.9=urgency=0.06667, clears
    neither normalized_effective_current_pct (0.99) nor the 0.8 urgency floor -> blocked.
    """
    low_urgency_region = RegionState(
        id="hills", name="Hills", bounds=(0, 0, 10, 10), hazard_level=0.72
    )
    current = ProjectState(
        id="current", kind=GoalKind.HARVESTING, status=ProjectStatus.ACTIVE,
        score=90.0, lock_until_tick=150,
    )
    entity = _entity(
        projects={"current": current},
        current_project_id="current",
        hp=50, max_hp=100,
    )
    state = _state(entities={1: entity}, regions={"hills": low_urgency_region}, tick=100)

    result = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)

    # evaluate_project_switch() returns None (blocked at the lock-bypass gate), so
    # evaluate_strategic_intent() falls through to its boredom-only return -- current_project_id
    # is never touched and no project is added/suspended.
    assert result is not None
    assert result.current_project_id_set is None
    assert result.projects_add_or_update == []


def test_high_urgency_regional_danger_interrupts_locked_current_project():
    """A genuinely high-urgency region clears BOTH of evaluate_project_switch()'s gates (the
    normalized lock-bypass gate AND the raw, unnormalized effective_current_score check)
    against a low-score locked current -- interruption_resistance is deliberately set low
    (0.01) here so the final raw check is actually reachable, mirroring the equivalent
    social-contract/adventure tests' own low-interruption-resistance pattern.

    current: kind=GoalKind.HARVESTING, score=1.0, lock_until_tick=150 (> tick=100).
    interruption_resistance=0.01, resistance_multiplier=30.0 (default) -> retention_margin=0.3.
    current_max=_score_scale_max(GoalKind.HARVESTING)=100.0 -> current_pct=0.01;
    normalized_effective_current_pct = 0.01 + 0.3/100 = 0.013.

    High-hazard region (hazard_level=1.0): urgency=1.0; raw_score=urgency*2.9=2.9 (the
    formula's own ceiling). candidate_pct = 2.9/2.9 = 1.0, clears both 0.013 and the 0.8
    floor -> lock bypassed. Final raw check: effective_current_score = 1.0+0.3 = 1.3;
    candidate.score(2.9) > 1.3 -> switch succeeds.
    """
    max_hazard_region = RegionState(
        id="swamp", name="Swamp", bounds=(0, 0, 10, 10), hazard_level=1.0
    )
    current = ProjectState(
        id="current", kind=GoalKind.HARVESTING, status=ProjectStatus.ACTIVE,
        score=1.0, lock_until_tick=150,
    )
    entity = _entity(
        projects={"current": current},
        current_project_id="current",
        hp=50, max_hp=100,
        interruption_resistance=0.01,
    )
    state = _state(entities={1: entity}, regions={"swamp": max_hazard_region}, tick=100)

    result = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)

    assert result is not None
    assert result.current_project_id_set == "project_stabilize_swamp_t100"
    suspended = [p for p in result.projects_add_or_update if p.id == "current"]
    assert len(suspended) == 1
    assert suspended[0].status == ProjectStatus.SUSPENDED


def test_region_stabilization_target_position_is_tactically_resolvable_not_a_stall():
    entity = _entity()
    state = _state(entities={1: entity}, regions={"swamp": _SWAMP_HIGH_HAZARD}, tick=0)

    result = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)
    project = result.projects_add_or_update[0]
    materialized_obj = project.objectives[0]

    expected_centroid = (5.0, 5.0)
    assert materialized_obj.target_position == expected_centroid

    # ast.literal_eval("swamp") must NOT succeed -- proves the target_position fallback (not
    # an accidental coordinate-string collision) is what resolves it.
    with pytest.raises((ValueError, SyntaxError)):
        ast.literal_eval(materialized_obj.target)

    resolved_pos, node_id, building_id = TacticalDecisionSystem._resolve_target_position(
        state, materialized_obj
    )
    assert resolved_pos == expected_centroid
    assert node_id is None
    assert building_id is None


def test_region_stabilization_and_adventure_route_share_score_scale_as_designed():
    """Explicit, in-code assertion that a region-stabilization-originated ProjectKind lands on
    the SAME 2.9-ceiling constant as adventure's own ProjectKind-typed candidates -- a
    deliberate, disclosed design choice (_score_scale_max() dispatches by Python enum class
    identity, not provenance)."""
    assert _score_scale_max(ProjectKind.STABILIZE) == _ADVENTURE_ROUTE_SCORE_MAX


def test_region_stabilization_winner_preserves_dedup_lookup_inert_behavior():
    """Design Decision #4: a suspended region-stabilize project is never resumed by the
    pre-existing `existing = next(...)` lookup (intelligence.py:1429) for a
    REGION_STABILIZATION winner -- it is re-materialized fresh under a new tick-suffixed id.
    Documents the accepted, shared, unfixed gap rather than leaving it silently unasserted."""
    suspended = ProjectState(
        id="project_stabilize_swamp_t0", kind=ProjectKind.STABILIZE,
        status=ProjectStatus.SUSPENDED, score=1.0,
    )
    entity = _entity(projects={"project_stabilize_swamp_t0": suspended})
    state = _state(entities={1: entity}, regions={"swamp": _SWAMP_HIGH_HAZARD}, tick=5)

    result = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)

    assert result is not None
    assert result.current_project_id_set == "project_stabilize_swamp_t5"
    assert result.current_project_id_set != "project_stabilize_swamp_t0"
