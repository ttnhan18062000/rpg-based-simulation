"""TCK-20261007-PROJECT-SWITCH-COMPARES-A-LIVE-CANDIDATE-SCORE-TO-THE-CURRENT-PROJECTS-CREATION-TIME-SCORE.

`evaluate_project_switch` compared a LIVE candidate utility against the current project's `score`, which is the utility its
goal had when the project was created and is never refreshed. A need that grew after the project started therefore looked
weaker than it was; the same goal's own live score could exceed its stale stored score by the retention margin and replace the
project with a duplicate (the old one suspended). The comparison now sees the current project's live utility.
"""
from __future__ import annotations

from dataclasses import replace

from src.ai.goals.base import GoalScore
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, BuildingState
from src.core.strategic import (
    GoalKind, ObjectiveKind, ObjectiveState, ObjectiveStatus, ProjectKind, ProjectState, ProjectStatus,
    with_live_current_score,
)
from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem


def _project(pid, kind, status=ProjectStatus.ACTIVE, score=10.0, lock_until=0):
    objective = ObjectiveState(id=f"o_{pid}", kind=ObjectiveKind.REACH_LOCATION, target="7", status=ObjectiveStatus.ACTIVE)
    return ProjectState(id=pid, kind=kind, status=status, score=score, objectives=[objective],
                        active_objective_id=objective.id, lock_until_tick=lock_until)


def _entity(projects, current_id, sleep_debt=0.0):
    entity = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).cognition(max_active_projects=3).build()
    entity = replace(entity, biological=replace(entity.biological, sleep_debt=sleep_debt))
    strategic = replace(entity.strategic, projects={p.id: p for p in projects}, current_project_id=current_id,
                        current_objective_id=f"o_{current_id}" if current_id else None)
    return replace(entity, strategic=strategic)


def _score(kind, utility):
    return GoalScore(kind=kind, utility=utility, target_id="7", target_pos=(5.0, 5.0))


# --- the helper ----------------------------------------------------------------------------------------------------------

def test_a_goal_kind_project_is_compared_at_its_live_utility():
    entity = _entity([_project("p", GoalKind.FATIGUE, score=10.0)], "p")
    refreshed = with_live_current_score(entity, [_score(GoalKind.FATIGUE, 77.0), _score(GoalKind.HUNGER, 5.0)])
    assert refreshed.strategic.projects["p"].score == 77.0
    assert entity.strategic.projects["p"].score == 10.0  # the stored state is not mutated


def test_other_projects_and_other_fields_are_untouched():
    other = _project("q", GoalKind.HARVESTING, ProjectStatus.SUSPENDED, score=33.0)
    entity = _entity([_project("p", GoalKind.FATIGUE, score=10.0), other], "p")
    refreshed = with_live_current_score(entity, [_score(GoalKind.FATIGUE, 77.0)])
    assert refreshed.strategic.projects["q"] is other
    assert refreshed.strategic.current_project_id == "p"


def test_a_project_kind_project_keeps_its_raw_score_on_the_other_scale():
    entity = _entity([_project("p", ProjectKind.TRAVEL, score=1.7)], "p")
    assert with_live_current_score(entity, [_score(GoalKind.FATIGUE, 77.0)]) is entity


def test_no_live_score_for_the_goal_leaves_the_entity_alone():
    entity = _entity([_project("p", GoalKind.FATIGUE, score=10.0)], "p")
    assert with_live_current_score(entity, [_score(GoalKind.HUNGER, 40.0)]) is entity


def test_no_current_project_leaves_the_entity_alone():
    entity = _entity([_project("p", GoalKind.FATIGUE)], None)
    assert with_live_current_score(entity, [_score(GoalKind.FATIGUE, 77.0)]) is entity


# --- through the real arbiter ---------------------------------------------------------------------------------------------

def _evaluate(entity):
    inn = BuildingState(id=7, kind="inn", position=(5.0, 5.0), functional=True)
    state = AuthoritativeState(tick=500, seed=1, entities={1: entity}, buildings={7: inn})
    return StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)


def test_a_grown_need_no_longer_replaces_its_own_project_with_a_duplicate():
    """The fatigue project was created when sleep debt was low (stored score 10); sleep debt is now 90 and the live fatigue
    utility is far above that. Old behaviour: the live candidate beat 10 + margin, so a duplicate fatigue project was created
    and the original suspended. Now the live score is the current project's own score, so nothing changes."""
    entity = _entity([_project("proj_fatigue_1", GoalKind.FATIGUE, score=10.0, lock_until=100)], "proj_fatigue_1", sleep_debt=90.0)
    update = _evaluate(entity)
    assert not (update.projects_add_or_update or [])
    assert not update.current_project_id_set
