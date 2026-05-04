"""
Contract tests for Dynamic Quest Generation.

Covers:
- LEG-RPG-141: Dynamic Quests
"""
import pytest
from src.core.state import EntityState, RegionState
from src.core.strategic import StrategicComponent, BlockerState, ProjectStatus
from src.systems.quests import QuestGenerationSystem
from src.core.builder import V2EntityBuilder


class TestQuestFromScar:
    """LEG-RPG-141: Quest generation from scar state."""

    def test_no_quest_when_trauma_low(self):
        region = RegionState(id="plains", name="Plains", bounds=(0, 0, 10, 10), trauma_score=0.2)
        result = QuestGenerationSystem.generate_from_scar(region, current_tick=100)
        assert result is None

    def test_quest_generated_on_high_trauma(self):
        region = RegionState(id="ruins", name="Ruins", bounds=(0, 0, 10, 10), trauma_score=0.7)
        result = QuestGenerationSystem.generate_from_scar(region, current_tick=100)
        assert result is not None
        assert result.kind == "scar_investigation"
        assert result.region_id == "ruins"
        assert len(result.objectives) >= 1
        assert result.objectives[0].kind == "investigate"

    def test_hazardous_scar_generates_clear_objective(self):
        region = RegionState(
            id="swamp", name="Swamp", bounds=(0, 0, 10, 10),
            trauma_score=0.8, hazard_level=0.7
        )
        result = QuestGenerationSystem.generate_from_scar(region, current_tick=100)
        assert len(result.objectives) == 2
        kinds = {obj.kind for obj in result.objectives}
        assert "investigate" in kinds
        assert "clear_threat" in kinds

    def test_quest_rewards_scale_with_trauma(self):
        low = RegionState(id="a", name="A", bounds=(0,0,10,10), trauma_score=0.4)
        high = RegionState(id="b", name="B", bounds=(0,0,10,10), trauma_score=0.9)
        q_low = QuestGenerationSystem.generate_from_scar(low, current_tick=1)
        q_high = QuestGenerationSystem.generate_from_scar(high, current_tick=1)
        assert q_high.objectives[0].reward_gold > q_low.objectives[0].reward_gold


class TestQuestFromBlockers:
    """LEG-RPG-141: Quest generation from blocker state."""

    def test_no_quests_when_no_blockers(self):
        entity = V2EntityBuilder(1).at((5.0, 5.0)).build()
        result = QuestGenerationSystem.generate_from_blockers(entity, current_tick=100)
        assert len(result) == 0

    def test_material_blocker_generates_expedition(self):
        blockers = {"b1": BlockerState(id="b1", kind="material", subject="iron", severity=0.7)}
        entity = (V2EntityBuilder(1)
                  .at((5.0, 5.0))
                  .with_strategic(blockers=blockers)
                  .build())
        result = QuestGenerationSystem.generate_from_blockers(entity, current_tick=100)
        assert len(result) == 1
        assert result[0].kind == "resource_expedition"
        assert result[0].objectives[0].kind == "gather"
        assert result[0].objectives[0].target == "iron"

    def test_resolved_blockers_ignored(self):
        blockers = {"b1": BlockerState(id="b1", kind="material", subject="iron", severity=0.7, resolved=True)}
        entity = (V2EntityBuilder(1)
                  .at((5.0, 5.0))
                  .with_strategic(blockers=blockers)
                  .build())
        result = QuestGenerationSystem.generate_from_blockers(entity, current_tick=100)
        assert len(result) == 0


class TestQuestToProject:
    """Quest templates can be converted to strategic projects."""

    def test_conversion_produces_active_project(self):
        region = RegionState(id="cave", name="Cave", bounds=(0,0,10,10), trauma_score=0.6)
        quest = QuestGenerationSystem.generate_from_scar(region, current_tick=50)
        project = QuestGenerationSystem.quest_to_project(quest, current_tick=50)
        assert project.status == ProjectStatus.ACTIVE
        assert len(project.objectives) >= 1
        assert project.kind == "quest"
