"""
Integration tests for the CommittedIntention tier-5 materialization hook
(TCK-20260812-COMMITTED-INTENTION-SEQUENCE, plan.md Step 7/Step 8).

Covers AC3 (materializes as an ordinary tier-5 candidate through the unmodified
evaluate_project_switch() arbiter), AC4 (losing committed intentions are retried, not
discarded), and the two anti-drift guards from test_plan.md: routine/role-boost participation
(New Test 7) and duplicate-GoalKind coexistence with a live scorer (New Test 8).

Decision 6 (plan.md): unlike the three special branches (ADVENTURE_ROUTE/SOCIAL_CONTRACT/
REGION_STABILIZATION), a committed intention always materializes via the generic branch using
`best_candidate.utility` directly -- ProjectState.kind stays a GoalKind instance (100-ceiling
scale), not a ProjectKind instance (2.9-ceiling scale). `score == utility` is therefore
scale-consistent, expected behavior here, not a regression of
TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG's defect class.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole
from src.core.state import AuthoritativeState
from src.core.strategic import (
    CommittedIntention, GoalKind, ProjectKind, ProjectState, ProjectStatus,
)
from src.engine.patches import StrategicPatch
from src.systems.strategic import StrategicIntelligenceSystem
from src.systems.strategic_systems.intelligence import _COMMITTED_INTENTION_BASE_UTILITY


def _entity(eid=1, pos=(0.0, 0.0), committed_intentions=(), projects=None,
            current_project_id=None, hp=None, max_hp=None, role=None,
            interruption_resistance=None):
    builder = V2EntityBuilder(eid).kind("hero").location(*pos)
    builder = builder.strategic(
        committed_intentions=committed_intentions,
        projects=projects or {},
        current_project_id=current_project_id,
    )
    if hp is not None or max_hp is not None:
        builder = builder.combat(hp=hp, max_hp=max_hp)
    if role is not None:
        builder = builder.identity(role=role)
    if interruption_resistance is not None:
        builder = builder.cognition(interruption_resistance=interruption_resistance)
    return builder.build()


def _state(entities=None, tick=0):
    return AuthoritativeState(tick=tick, seed=42, entities=entities or {})


def _apply(entity, strategic_update):
    """Runs a StrategicUpdate through the sole authoritative merge path."""
    changes = {}
    StrategicPatch(entity_id=entity.id, strategic=strategic_update).apply(entity, changes)
    return replace(entity, strategic=changes.get("strategic", entity.strategic))


def test_committed_intention_head_materializes_as_ordinary_tier5_candidate():
    ci = CommittedIntention(
        intention_id="ci_1", goal_kind="harvesting", target_hint="node_5",
        sequence_index=0, status="pending",
    )
    entity = _entity(committed_intentions=(ci,))
    state = _state(entities={1: entity}, tick=0)

    result = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)

    assert result is not None
    assert result.current_project_id_set == "proj_harvesting_0"
    assert len(result.projects_add_or_update) == 1
    project = result.projects_add_or_update[0]
    assert project.id == "proj_harvesting_0"
    assert project.objectives[0].target == "node_5"

    # Win-transition bookkeeping (Design Decision 5): the winning committed intention flips to
    # "active" via the authoritative StrategicUpdate, not a bare dataclasses.replace() outside it.
    assert len(result.committed_intentions_add_or_update) == 1
    won = result.committed_intentions_add_or_update[0]
    assert won.intention_id == "ci_1"
    assert won.status == "active"
    assert won.sequence_index == 0


def test_committed_intention_materializes_via_generic_branch_with_scale_consistent_score():
    """Decision 6's corrected New Test 4: score == utility is CORRECT here (generic branch,
    GoalKind-typed ProjectState.kind), unlike the three special branches which must use
    metadata['raw_score']."""
    ci = CommittedIntention(
        intention_id="ci_1", goal_kind="harvesting", target_hint="node_5",
        sequence_index=0, status="pending",
    )
    entity = _entity(committed_intentions=(ci,))
    state = _state(entities={1: entity}, tick=0)

    result = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)
    project = result.projects_add_or_update[0]

    assert isinstance(project.kind, GoalKind)
    assert not isinstance(project.kind, ProjectKind)
    assert project.score == pytest.approx(_COMMITTED_INTENTION_BASE_UTILITY)


def test_losing_committed_intention_retries_next_eligible_tick():
    """AC4's explicitly required regression test: a committed intention that loses arbitration
    (blocked by evaluate_project_switch()'s own unmodified lock/margin logic) stays at
    sequence_index 0 with status unchanged, and is still eligible to compete the following tick.
    """
    current = ProjectState(
        id="current", kind=GoalKind.RECOVER, status=ProjectStatus.ACTIVE,
        score=90.0, lock_until_tick=1000,
    )
    ci = CommittedIntention(
        intention_id="ci_1", goal_kind="guild", target_hint="hall_1",
        sequence_index=0, status="pending",
    )
    entity = _entity(
        committed_intentions=(ci,),
        projects={"current": current},
        current_project_id="current",
        hp=50, max_hp=100,  # below _threat_resolved()'s 80% release threshold
    )
    state_tick0 = _state(entities={1: entity}, tick=0)

    result0 = StrategicIntelligenceSystem.evaluate_strategic_intent(state_tick0, entity, force=True)

    assert result0 is not None
    # No win-transition fired: the committed intention lost arbitration.
    assert result0.committed_intentions_add_or_update == []
    assert result0.committed_intentions_remove == []
    assert result0.current_project_id_set is None

    # Apply tick 0's (no-op-for-committed_intentions) update through the authoritative path and
    # confirm the entry survives untouched.
    entity_after_tick0 = _apply(entity, result0)
    assert entity_after_tick0.strategic.committed_intentions == (ci,)

    # Tick 1: unchanged world state, the same entry is still present and still eligible.
    state_tick1 = _state(entities={1: entity_after_tick0}, tick=1)
    result1 = StrategicIntelligenceSystem.evaluate_strategic_intent(
        state_tick1, entity_after_tick0, force=True
    )

    assert result1 is not None
    assert result1.committed_intentions_add_or_update == []
    assert result1.committed_intentions_remove == []

    entity_after_tick1 = _apply(entity_after_tick0, result1)
    assert entity_after_tick1.strategic.committed_intentions == (ci,)
    head = entity_after_tick1.strategic.committed_intentions[0]
    assert head.sequence_index == 0
    assert head.status == "pending"


def test_committed_intentions_participate_in_routine_role_boosting():
    """Confirms injection happens before intelligence.py's routine/role-boost comprehension, not
    after -- a WORKER entity's committed HARVESTING intention receives
    RoutineService.get_role_utility_boost's +15.0 WORKER/HARVESTING bonus."""
    ci = CommittedIntention(
        intention_id="ci_1", goal_kind="harvesting", target_hint="node_5",
        sequence_index=0, status="pending",
    )
    entity = _entity(committed_intentions=(ci,), role=EntityRole.WORKER)
    state = _state(entities={1: entity}, tick=0)

    result = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)
    project = result.projects_add_or_update[0]

    assert project.score == pytest.approx(_COMMITTED_INTENTION_BASE_UTILITY + 15.0)


def test_duplicate_goal_kind_committed_intention_and_live_scorer_coexist():
    """A committed intention reusing a GoalKind with a live registered scorer (TOWN_RETURN via
    TownScorer, which always emits an unconditional candidate) must not crash the sort/selection
    path, and the higher-utility entry (the committed intention, base utility 50.0, vs. the
    default entity's live TownScorer candidate, utility 0.0) wins deterministically."""
    ci = CommittedIntention(
        intention_id="ci_1", goal_kind="town_return", target_hint="town_center",
        sequence_index=0, status="pending",
    )
    entity = _entity(committed_intentions=(ci,))
    state = _state(entities={1: entity}, tick=0)

    result = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)

    assert result is not None
    assert result.current_project_id_set == "proj_town_return_0"
    assert len(result.committed_intentions_add_or_update) == 1
    assert result.committed_intentions_add_or_update[0].intention_id == "ci_1"
    assert result.committed_intentions_add_or_update[0].status == "active"


def test_committed_intention_epic_goal_kind_is_not_materialized():
    """Design Decision 2: an epic GoalKind (ADVENTURE_ROUTE/SOCIAL_CONTRACT/
    REGION_STABILIZATION) on a committed intention's head is silently treated as not-due
    (no-op this tick), never crashes -- restricted to the 10 generic kinds, MVP scope."""
    ci = CommittedIntention(
        intention_id="ci_1", goal_kind=GoalKind.ADVENTURE_ROUTE.value, target_hint="somewhere",
        sequence_index=0, status="pending",
    )
    entity = _entity(committed_intentions=(ci,))
    state = _state(entities={1: entity}, tick=0)

    result = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)

    assert result is not None
    assert result.current_project_id_set is None
    assert result.committed_intentions_add_or_update == []


def test_committed_intention_with_no_target_hint_never_materializes():
    """Design Decision 9: a None target_hint is never resolvable, so the synthesized candidate
    never clears the arbiter's own existing floor check (target_id is None and target_pos is
    None) -- zero new code, re-synthesized and re-skipped every eligible tick."""
    ci = CommittedIntention(
        intention_id="ci_1", goal_kind="guild", target_hint=None,
        sequence_index=0, status="pending",
    )
    entity = _entity(committed_intentions=(ci,))
    state = _state(entities={1: entity}, tick=0)

    result = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)

    assert result is not None
    assert result.current_project_id_set is None
    assert result.committed_intentions_add_or_update == []


def test_committed_intention_non_pending_head_is_not_materialized():
    """Design Decision 8: the materialization hook only ever reads committed_intentions[0]; a
    head whose status is anything other than 'pending' is treated as not-due -- no auto-advance
    to index 1 in this ticket's scope."""
    active_head = CommittedIntention(
        intention_id="ci_1", goal_kind="harvesting", target_hint="node_5",
        sequence_index=0, status="active",
    )
    entity = _entity(committed_intentions=(active_head,))
    state = _state(entities={1: entity}, tick=0)

    result = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)

    assert result is not None
    assert result.current_project_id_set is None
