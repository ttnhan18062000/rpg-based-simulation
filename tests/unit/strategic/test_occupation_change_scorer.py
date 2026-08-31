"""
Unit tests for OccupationChangeGoalScorer (TCK-20260824-OCCUPATION-CHANGE-TRIGGER).

Covers AC1 (registration + reachability), the role-gate/open-slot/skill-check algorithm, and the
tier-5 materialization branch in StrategicIntelligenceSystem.evaluate_strategic_intent(), which
must use metadata["raw_score"], never best_candidate.utility (the same
TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG class RegionStabilizationGoalScorer's
own tests re-check). Also covers the CAREER_CHANGE per-tick completion check.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.ai.goals import GoalRegistry
from src.ai.goals.base import GoalScore
from src.ai.goals.occupation_change_scorer import OccupationChangeGoalScorer
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole
from src.core.state import AuthoritativeState, RegionState
from src.core.strategic import (
    GoalKind, ProjectKind, ObjectiveKind, ProjectState, ProjectStatus,
    ObjectiveState, ObjectiveStatus,
)
from src.systems.strategic import StrategicIntelligenceSystem
from src.systems.strategic_systems.intelligence import (
    _score_scale_max, _ADVENTURE_ROUTE_SCORE_MAX, _COMMITTED_INTENTION_ELIGIBLE_KINDS,
)

_REGION = RegionState(id="town", name="Town", bounds=(0, 0, 10, 10))


def _citizen(eid: int = 1, pos: tuple = (5.0, 5.0), **identity_kwargs):
    builder = V2EntityBuilder(eid).kind("citizen").location(*pos)
    builder = builder.identity(role=EntityRole.CITIZEN, **identity_kwargs)
    return builder.build()


def _worker_entity(eid: int, role: int, pos: tuple = (2.0, 2.0)):
    return V2EntityBuilder(eid).kind("npc").location(*pos).identity(role=role).build()


def _state(entities=None, regions=None, tick=0):
    return AuthoritativeState(tick=tick, seed=42, entities=entities or {}, regions=regions or {})


# --- Role gate --------------------------------------------------------------------------------


def test_occupation_change_scorer_returns_zero_utility_for_non_eligible_role():
    entity = V2EntityBuilder(1).kind("hero").location(5.0, 5.0).identity(role=EntityRole.HERO).build()
    state = _state(entities={1: entity}, regions={"town": _REGION})

    score = OccupationChangeGoalScorer().score(entity, state)

    assert isinstance(score, GoalScore)
    assert score.kind == GoalKind.OCCUPATION_CHANGE
    assert score.utility == 0.0
    assert score.target_id is None


# --- Open slot + skill match --------------------------------------------------------------------


def test_occupation_change_scorer_fires_when_open_slot_and_skill_match():
    entity = _citizen()
    state = _state(entities={1: entity}, regions={"town": _REGION})

    score = OccupationChangeGoalScorer().score(entity, state)

    assert score.kind == GoalKind.OCCUPATION_CHANGE
    assert score.utility > 0.0
    assert score.target_id == "town"
    assert score.metadata["dest_role"] == int(EntityRole.SHOPKEEPER)
    assert score.metadata["proj_kind"] == ProjectKind.CAREER_CHANGE
    assert score.metadata["obj_kind"] == ObjectiveKind.CHANGE_OCCUPATION
    assert score.metadata["raw_score"] == pytest.approx(_ADVENTURE_ROUTE_SCORE_MAX * 0.9)
    assert score.metadata["raw_score"] != score.utility


def test_occupation_change_scorer_does_not_fire_without_open_slot():
    citizen = _citizen(eid=1)
    shopkeeper = _worker_entity(2, EntityRole.SHOPKEEPER, pos=(1.0, 1.0))
    worker = _worker_entity(3, EntityRole.WORKER, pos=(2.0, 2.0))
    guard = _worker_entity(4, EntityRole.GUARD, pos=(3.0, 3.0))
    state = _state(
        entities={1: citizen, 2: shopkeeper, 3: worker, 4: guard},
        regions={"town": _REGION},
    )

    score = OccupationChangeGoalScorer().score(citizen, state)

    assert score.kind == GoalKind.OCCUPATION_CHANGE
    assert score.utility == 0.0
    assert score.target_id is None


# --- Registration -------------------------------------------------------------------------------


def test_occupation_change_goal_registered_in_goal_registry():
    assert GoalKind("occupation_change") == GoalKind.OCCUPATION_CHANGE
    assert isinstance(
        GoalRegistry._scorers[GoalKind.OCCUPATION_CHANGE], OccupationChangeGoalScorer
    )
    assert GoalKind.OCCUPATION_CHANGE not in _COMMITTED_INTENTION_ELIGIBLE_KINDS


# --- Materialization ------------------------------------------------------------------------


def test_occupation_change_materializes_into_project_with_correct_kind():
    entity = _citizen()
    state = _state(entities={1: entity}, regions={"town": _REGION})

    result = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)

    assert result is not None
    assert len(result.projects_add_or_update) == 1
    project = result.projects_add_or_update[0]
    assert project.kind == ProjectKind.CAREER_CHANGE
    assert project.objectives[0].kind == ObjectiveKind.CHANGE_OCCUPATION

    raw_score = _ADVENTURE_ROUTE_SCORE_MAX * 0.9
    utility = (raw_score / _ADVENTURE_ROUTE_SCORE_MAX) * 100.0
    assert project.score == pytest.approx(raw_score)
    assert project.score != pytest.approx(utility)

    assert _score_scale_max(ProjectKind.CAREER_CHANGE) == _ADVENTURE_ROUTE_SCORE_MAX


# --- Completion check (Step 5) ------------------------------------------------------------------


def test_career_change_project_completes_once_role_is_no_longer_citizen():
    obj = ObjectiveState(
        id="obj_career_town_t0",
        kind=ObjectiveKind.CHANGE_OCCUPATION,
        target="role_1",
        target_position=(5.0, 5.0),
        status=ObjectiveStatus.ACTIVE,
    )
    project = ProjectState(
        id="project_career_town_t0",
        kind=ProjectKind.CAREER_CHANGE,
        status=ProjectStatus.ACTIVE,
        objectives=[obj],
        active_objective_id=obj.id,
        lock_until_tick=10,
        created_tick=0,
        score=2.61,
    )
    entity = (
        V2EntityBuilder(1)
        .kind("npc")
        .location(5.0, 5.0)
        .identity(role=EntityRole.SHOPKEEPER)
        .strategic(projects={project.id: project}, current_project_id=project.id)
        .build()
    )
    state = _state(entities={1: entity}, regions={"town": _REGION}, tick=5)

    result = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)

    assert result is not None
    completed = [p for p in result.projects_add_or_update if p.id == project.id]
    assert len(completed) == 1
    assert completed[0].status == ProjectStatus.COMPLETED
    assert result.current_project_id_set == ""
