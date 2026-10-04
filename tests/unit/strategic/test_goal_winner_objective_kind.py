"""
Generic goal-winner consumption carries the scorer-decided objective kind
(TCK-20261002-GOAL-WINNER-CONSUMPTION-DISCARDS-DECIDED-OBJECTIVE-KIND, test_plan.md T1/T2/T6).

The defect is in the wiring between a scorer and the project it materialises, so these tests drive the real
``StrategicIntelligenceSystem.evaluate_strategic_intent`` generic branch. A unit test on
``ObjectiveIntentResolver`` cannot prove this fix: the resolver is never consulted on this path.
"""
from __future__ import annotations

import pytest

from src.ai.goals.base import GoalRegistry, GoalScore
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.core.strategic import GoalKind, ObjectiveKind, ProjectKind
from src.systems.strategic import StrategicIntelligenceSystem

# investigation.md section 6: fall-through kinds whose scorer publishes no obj_kind, for which a
# hardcoded REACH_LOCATION is correct (node/building ids resolve on arrival; "town_center" is a fixed place).
_REACH_LOCATION_KINDS = [
    GoalKind.HARVESTING, GoalKind.FATIGUE, GoalKind.HUNGER, GoalKind.SOCIAL, GoalKind.TOWN_RETURN,
    GoalKind.COMBAT_RETREAT, GoalKind.RECOVER, GoalKind.RESOLVE_BLOCKER, GoalKind.GUILD,
]


def _materialise(monkeypatch, score: GoalScore):
    entity = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).build()
    state = AuthoritativeState(tick=0, seed=42, entities={1: entity})
    monkeypatch.setattr(GoalRegistry, "get_all_scores", classmethod(lambda cls, e, s: [score]))
    result = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)
    assert result is not None and result.projects_add_or_update, "the candidate must win and materialise"
    return result.projects_add_or_update[0]


@pytest.mark.parametrize("kind", _REACH_LOCATION_KINDS)
def test_kinds_that_publish_no_objective_kind_still_materialise_reach_location(monkeypatch, kind):
    project = _materialise(monkeypatch, GoalScore(kind=kind, utility=80.0, target_id="node_1", target_pos=(3.0, 4.0)))
    assert project.objectives[0].kind == ObjectiveKind.REACH_LOCATION


@pytest.mark.parametrize("metadata", [{}, {"obj_kind": None}])
def test_missing_or_none_obj_kind_falls_back_to_reach_location(monkeypatch, metadata):
    project = _materialise(monkeypatch, GoalScore(
        kind=GoalKind.HARVESTING, utility=80.0, target_id="node_1", target_pos=(3.0, 4.0), metadata=metadata))
    assert project.objectives[0].kind == ObjectiveKind.REACH_LOCATION


def test_published_obj_kind_is_carried_through_winner_consumption(monkeypatch):
    project = _materialise(monkeypatch, GoalScore(
        kind=GoalKind.COMBAT_ENGAGE, utility=80.0, target_id="2", target_pos=(3.0, 4.0),
        metadata={"obj_kind": ObjectiveKind.DEFEAT_ENEMY}))
    assert project.objectives[0].kind == ObjectiveKind.DEFEAT_ENEMY
    assert project.objectives[0].target == "2"


def test_generic_branch_keeps_goal_kind_and_utility_scale(monkeypatch):
    """Scope guard: ProjectState.kind stays a GoalKind and score stays the 100-scale utility. Making kind a
    ProjectKind would silently move the retention ceiling from 100.0 to 2.9 (_score_scale_max)."""
    project = _materialise(monkeypatch, GoalScore(
        kind=GoalKind.COMBAT_ENGAGE, utility=80.0, target_id="2", target_pos=(3.0, 4.0),
        metadata={"obj_kind": ObjectiveKind.DEFEAT_ENEMY}))
    assert project.kind == GoalKind.COMBAT_ENGAGE
    assert not isinstance(project.kind, ProjectKind)
    assert project.score == pytest.approx(80.0)
