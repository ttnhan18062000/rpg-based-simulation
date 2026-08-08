"""Unit tests for GuildNeedScorer (TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING)."""
from __future__ import annotations

from src.ai.goals.scorers import GuildNeedScorer
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, BuildingState


def _state_with_town_hall(entities: dict, flags: dict | None = None) -> AuthoritativeState:
    building = BuildingState(id=20000, kind="town_hall", position=(50.0, 50.0), hp=500, max_hp=500, functional=True)
    return AuthoritativeState(
        tick=1, seed=42, entities=entities, buildings={20000: building},
        feature_flags=flags or {},
    )


def _entity(eid: int = 1, pos: tuple = (0.0, 0.0), project_count: int = 0):
    projects = {}
    if project_count > 0:
        from src.core.strategic import ProjectState, ProjectStatus
        for i in range(project_count):
            projects[f"p{i}"] = ProjectState(id=f"p{i}", kind="harvesting", status=ProjectStatus.ACTIVE)
    return (
        V2EntityBuilder(eid)
        .kind("hero")
        .location(*pos)
        .strategic(projects=projects)
        .build()
    )


class TestFlagGating:
    def test_returns_zero_utility_when_flag_off(self):
        entity = _entity()
        state = _state_with_town_hall({1: entity}, flags={"ENABLE_GUILD_QUEST_GENERATION": "OFF"})
        score = GuildNeedScorer().score(entity, state)
        assert score.utility == 0.0

    def test_returns_zero_utility_when_flag_absent(self):
        entity = _entity()
        state = _state_with_town_hall({1: entity}, flags={})
        score = GuildNeedScorer().score(entity, state)
        assert score.utility == 0.0


class TestCapacityGating:
    def test_returns_zero_utility_when_at_project_capacity(self):
        entity = _entity(project_count=10)  # default profile max_active_projects is small
        state = _state_with_town_hall({1: entity}, flags={"ENABLE_GUILD_QUEST_GENERATION": "ON"})
        score = GuildNeedScorer().score(entity, state)
        assert score.utility == 0.0

    def test_returns_real_score_when_flag_on_and_spare_capacity(self):
        entity = _entity(project_count=0)
        state = _state_with_town_hall({1: entity}, flags={"ENABLE_GUILD_QUEST_GENERATION": "ON"})
        score = GuildNeedScorer().score(entity, state)
        assert score.utility > 0.0
        assert score.target_id == "20000"
        assert score.target_pos == (50.0, 50.0)


class TestNoBuilding:
    def test_returns_zero_utility_when_no_town_hall_exists(self):
        entity = _entity()
        state = AuthoritativeState(
            tick=1, seed=42, entities={1: entity}, buildings={},
            feature_flags={"ENABLE_GUILD_QUEST_GENERATION": "ON"},
        )
        score = GuildNeedScorer().score(entity, state)
        assert score.utility == 0.0
