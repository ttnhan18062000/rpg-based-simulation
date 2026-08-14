"""Unit tests for GuildVisitPhase (TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING)."""
from __future__ import annotations

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, BuildingState
from src.core.strategic import (
    GoalKind, ObjectiveKind, ObjectiveState, ObjectiveStatus, ProjectState, ProjectStatus,
)
from src.core.updates import StateUpdate
from src.engine.pipeline_phases.guild_visit import GuildVisitPhase

_BUILDING = BuildingState(id=20000, kind="town_hall", position=(50.0, 50.0), hp=500, max_hp=500, functional=True)


def _guild_project(target: str = "20000", status: ProjectStatus = ProjectStatus.ACTIVE,
                    obj_status: ObjectiveStatus = ObjectiveStatus.ACTIVE) -> ProjectState:
    obj = ObjectiveState(
        id="guild_obj", kind=ObjectiveKind.REACH_LOCATION, target=target,
        target_position=(50.0, 50.0), status=obj_status,
    )
    return ProjectState(
        id="proj_guild", kind=GoalKind.GUILD, status=status,
        objectives=[obj], active_objective_id="guild_obj", score=25.0,
    )


def _entity_with_guild_project(eid: int, pos: tuple, project: ProjectState):
    return (
        V2EntityBuilder(eid)
        .kind("hero")
        .location(*pos)
        .strategic(projects={"proj_guild": project}, current_project_id="proj_guild",
                   current_objective_id="guild_obj")
        .build()
    )


class TestFlagGating:
    def test_no_op_when_flag_off(self):
        entity = _entity_with_guild_project(1, (50.0, 50.0), _guild_project())
        state = AuthoritativeState(
            tick=1, seed=42, entities={1: entity}, buildings={20000: _BUILDING},
            feature_flags={"ENABLE_GUILD_QUEST_GENERATION": "OFF"},
        )
        result = GuildVisitPhase.resolve(state, StateUpdate())
        assert result.entity_updates == {}

    def test_no_op_when_flag_absent(self):
        entity = _entity_with_guild_project(1, (50.0, 50.0), _guild_project())
        state = AuthoritativeState(
            tick=1, seed=42, entities={1: entity}, buildings={20000: _BUILDING},
            feature_flags={},
        )
        result = GuildVisitPhase.resolve(state, StateUpdate())
        assert result.entity_updates == {}


class TestArrival:
    def test_completes_visit_when_arrived(self):
        entity = _entity_with_guild_project(1, (50.0, 50.0), _guild_project())
        state = AuthoritativeState(
            tick=1, seed=42, entities={1: entity}, buildings={20000: _BUILDING},
            feature_flags={"ENABLE_GUILD_QUEST_GENERATION": "ON"},
        )
        result = GuildVisitPhase.resolve(state, StateUpdate())
        assert 1 in result.entity_updates
        eu = result.entity_updates[1]
        assert eu.strategic.current_project_id_set == ""
        assert eu.strategic.current_objective_id_set == ""
        completed = [p for p in eu.strategic.projects_add_or_update if p.id == "proj_guild"]
        assert len(completed) == 1
        assert completed[0].status == ProjectStatus.COMPLETED

    def test_not_arrived_is_no_op(self):
        entity = _entity_with_guild_project(1, (0.0, 0.0), _guild_project())
        state = AuthoritativeState(
            tick=1, seed=42, entities={1: entity}, buildings={20000: _BUILDING},
            feature_flags={"ENABLE_GUILD_QUEST_GENERATION": "ON"},
        )
        result = GuildVisitPhase.resolve(state, StateUpdate())
        assert result.entity_updates == {}

    def test_non_guild_project_kind_is_ignored(self):
        obj = ObjectiveState(id="o1", kind=ObjectiveKind.REACH_LOCATION, target="20000",
                              status=ObjectiveStatus.ACTIVE)
        proj = ProjectState(id="p1", kind="harvesting", status=ProjectStatus.ACTIVE,
                             objectives=[obj], active_objective_id="o1")
        entity = _entity_with_guild_project(1, (50.0, 50.0), proj)
        state = AuthoritativeState(
            tick=1, seed=42, entities={1: entity}, buildings={20000: _BUILDING},
            feature_flags={"ENABLE_GUILD_QUEST_GENERATION": "ON"},
        )
        result = GuildVisitPhase.resolve(state, StateUpdate())
        assert result.entity_updates == {}

    def test_suspended_project_is_ignored(self):
        entity = _entity_with_guild_project(1, (50.0, 50.0), _guild_project(status=ProjectStatus.SUSPENDED))
        state = AuthoritativeState(
            tick=1, seed=42, entities={1: entity}, buildings={20000: _BUILDING},
            feature_flags={"ENABLE_GUILD_QUEST_GENERATION": "ON"},
        )
        result = GuildVisitPhase.resolve(state, StateUpdate())
        assert result.entity_updates == {}

    def test_missing_building_is_no_op(self):
        entity = _entity_with_guild_project(1, (50.0, 50.0), _guild_project(target="99999"))
        state = AuthoritativeState(
            tick=1, seed=42, entities={1: entity}, buildings={20000: _BUILDING},
            feature_flags={"ENABLE_GUILD_QUEST_GENERATION": "ON"},
        )
        result = GuildVisitPhase.resolve(state, StateUpdate())
        assert result.entity_updates == {}

    def test_unparseable_target_is_no_op(self):
        entity = _entity_with_guild_project(1, (50.0, 50.0), _guild_project(target="not_an_id"))
        state = AuthoritativeState(
            tick=1, seed=42, entities={1: entity}, buildings={20000: _BUILDING},
            feature_flags={"ENABLE_GUILD_QUEST_GENERATION": "ON"},
        )
        result = GuildVisitPhase.resolve(state, StateUpdate())
        assert result.entity_updates == {}
