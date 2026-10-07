"""TCK-20261007-STRATEGIC-CAPACITY-GATE-COUNTS-TERMINAL-PROJECTS-SO-NO-NEW-PROJECT-KIND-CAN-START.

`CognitionProfile.max_active_projects` bounds the projects an entity is working on. The capacity gate (intelligence.py), the
bandwidth trim (detour.py), the capacity-enforcement phase and two spare-capacity readers all counted every STORED project,
COMPLETED and ABANDONED ones included, and nothing removes those. An entity that had ever held `max_active_projects`
projects could therefore never start a new KIND of project (only reactivate a kind it already had a record of): in the
corpus a fatigue goal won its evaluation and was dropped, so nobody slept. One predicate now says which projects count.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, BuildingState
from src.core.strategic import (
    ObjectiveKind, ObjectiveState, ObjectiveStatus, ProjectKind, ProjectState, ProjectStatus,
    has_project_capacity, is_live_project, live_projects,
)
from src.core.updates import EntityUpdate, StateUpdate, StrategicUpdate
from src.engine.pipeline_phases.capacity_enforcement import CapacityEnforcementPhase
from src.systems.strategic_systems.detour import DetourSuggestionSystem
from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem

TERMINAL = (ProjectStatus.COMPLETED, ProjectStatus.ABANDONED)
LIVE = (ProjectStatus.ACTIVE, ProjectStatus.SUSPENDED)


def _project(pid, status=ProjectStatus.ACTIVE, kind=ProjectKind.TRAVEL, score=10.0):
    objective = ObjectiveState(id=f"o_{pid}", kind=ObjectiveKind.REACH_LOCATION, status=ObjectiveStatus.RESOLVED)
    return ProjectState(id=pid, kind=kind, status=status, objectives=[objective], active_objective_id=objective.id, score=score)


def _entity(projects, max_projects=3, sleep_debt=0.0):
    entity = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).cognition(max_active_projects=max_projects).build()
    entity = replace(entity, biological=replace(entity.biological, sleep_debt=sleep_debt))
    return replace(entity, strategic=replace(entity.strategic, projects={p.id: p for p in projects}))


def _state_with_inn(entity):
    inn = BuildingState(id=7, kind="inn", position=(5.0, 5.0), functional=True)
    return AuthoritativeState(tick=500, seed=1, entities={entity.id: entity}, buildings={7: inn})


# --- the predicate ----------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("status", LIVE)
def test_active_and_suspended_projects_are_live(status):
    assert is_live_project(_project("p", status))


@pytest.mark.parametrize("status", TERMINAL)
def test_completed_and_abandoned_projects_are_not_live(status):
    assert not is_live_project(_project("p", status))


def test_live_projects_keeps_only_the_live_ones():
    projects = {p.id: p for p in (_project("a", ProjectStatus.ACTIVE), _project("b", ProjectStatus.COMPLETED),
                                  _project("c", ProjectStatus.SUSPENDED), _project("d", ProjectStatus.ABANDONED))}
    assert sorted(live_projects(projects)) == ["a", "c"]


def test_capacity_ignores_terminal_projects_and_counts_live_ones():
    terminal = {p.id: p for p in (_project(f"t{i}", ProjectStatus.ABANDONED) for i in range(5))}
    assert has_project_capacity(terminal, 3)
    live = {p.id: p for p in (_project(f"l{i}", ProjectStatus.SUSPENDED) for i in range(3))}
    assert not has_project_capacity(live, 3)
    assert has_project_capacity({**live, "x": _project("x", ProjectStatus.COMPLETED)}, 4)


def test_a_limit_of_zero_has_no_capacity_whatever_the_projects():
    assert not has_project_capacity({}, 0)


# --- the gate: a new kind of project can start --------------------------------------------------------------------------

def _fatigue_projects(entity):
    state = _state_with_inn(entity)
    update = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)
    return [(getattr(p.kind, "value", p.kind), p.status) for p in (update.projects_add_or_update or [])]


def test_an_entity_holding_only_finished_projects_can_start_a_fatigue_project():
    finished = [_project("h", ProjectStatus.COMPLETED, ProjectKind.HARVESTING),
                _project("t1", ProjectStatus.ABANDONED), _project("t2", ProjectStatus.ABANDONED)]
    assert _fatigue_projects(_entity(finished, sleep_debt=90.0)) == [("fatigue", ProjectStatus.ACTIVE)]


def test_an_entity_holding_max_live_projects_still_cannot_start_a_new_kind():
    live = [_project("a", ProjectStatus.SUSPENDED, ProjectKind.HARVESTING), _project("b", ProjectStatus.SUSPENDED),
            _project("c", ProjectStatus.SUSPENDED, ProjectKind.QUEST)]
    assert _fatigue_projects(_entity(live, sleep_debt=90.0)) == []


def test_an_entity_with_no_projects_starts_one():
    assert _fatigue_projects(_entity([], sleep_debt=90.0)) == [("fatigue", ProjectStatus.ACTIVE)]


# --- the trim: the same predicate, so it never evicts a live project for a finished record -------------------------------

def test_the_trim_does_not_evict_live_projects_to_make_room_for_finished_ones():
    # the two finished records have the HIGHER ids, which the old trim kept in preference to the live projects
    entity = _entity([_project("a_live"), _project("b_live", ProjectStatus.SUSPENDED),
                      _project("z1", ProjectStatus.COMPLETED), _project("z2", ProjectStatus.ABANDONED)], max_projects=2)
    assert DetourSuggestionSystem.enforce_bandwidth(entity, current_tick=1).projects_remove == []


def test_the_trim_still_removes_a_live_project_over_the_limit_and_never_a_finished_one():
    entity = _entity([_project("live_1"), _project("live_2"), _project("live_3", ProjectStatus.SUSPENDED),
                      _project("done", ProjectStatus.COMPLETED)], max_projects=2)
    removed = DetourSuggestionSystem.enforce_bandwidth(entity, current_tick=1).projects_remove
    assert len(removed) == 1
    assert removed[0].startswith("live_")


# --- the enforcement phase ----------------------------------------------------------------------------------------------

def test_the_enforcement_phase_does_not_drop_a_new_project_because_of_finished_records():
    finished = [_project(f"t{i}", ProjectStatus.ABANDONED, score=99.0) for i in range(3)]  # scores above the new project's
    entity = _entity(finished)
    new = _project("proj_fatigue_500", ProjectStatus.ACTIVE, ProjectKind.QUEST, score=50.0)
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, strategic=StrategicUpdate(projects_add_or_update=[new]))})

    result = CapacityEnforcementPhase.enforce(AuthoritativeState(tick=500, seed=1, entities={1: entity}), update)

    assert result.entity_updates[1].strategic.projects_remove == []


def test_the_enforcement_phase_still_trims_live_projects_over_the_limit():
    live = [_project(f"l{i}", ProjectStatus.SUSPENDED, score=float(i)) for i in range(3)]
    entity = _entity(live)
    new = _project("proj_new", ProjectStatus.ACTIVE, ProjectKind.QUEST, score=50.0)
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, strategic=StrategicUpdate(projects_add_or_update=[new]))})

    result = CapacityEnforcementPhase.enforce(AuthoritativeState(tick=500, seed=1, entities={1: entity}), update)

    assert result.entity_updates[1].strategic.projects_remove == ["l0"]


# --- the spare-capacity reader in the goal scorers ------------------------------------------------------------------------

def _guild_state(entity):
    from src.core.state import BuildingState as _Building

    town_hall = _Building(id=20000, kind="town_hall", position=(50.0, 50.0), hp=500, max_hp=500, functional=True)
    return AuthoritativeState(tick=1, seed=42, entities={1: entity}, buildings={20000: town_hall},
                              feature_flags={"ENABLE_GUILD_QUEST_GENERATION": "ON"})


def test_the_guild_scorer_sees_spare_capacity_when_only_finished_projects_are_stored():
    from src.ai.goals.scorers import GuildNeedScorer

    entity = _entity([_project(f"t{i}", ProjectStatus.COMPLETED) for i in range(5)])
    assert GuildNeedScorer().score(entity, _guild_state(entity)).utility > 0.0


def test_the_guild_scorer_has_no_spare_capacity_when_live_projects_fill_the_limit():
    from src.ai.goals.scorers import GuildNeedScorer

    entity = _entity([_project(f"l{i}", ProjectStatus.SUSPENDED) for i in range(3)])
    assert GuildNeedScorer().score(entity, _guild_state(entity)).utility == 0.0
