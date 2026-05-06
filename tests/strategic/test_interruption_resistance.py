"""
Contract tests for Strategic Cognition: Interruption Resistance & Project Switching.

Covers:
- Part 1 §Strategic: Project switching uses interruption resistance / margin logic
- Part 1 §Strategic: Current project gets reservation/retention priority
- RPG-0040: project_objective_continuity
- RPG-0041: project_interruption_resistance
- RPG-0042: current_project_retention
"""
import pytest
from src.core.state import EntityState
from src.core.strategic import (
    StrategicComponent, CognitionProfile, ProjectState, ProjectStatus,
    ObjectiveState, ObjectiveStatus
)
from src.systems.strategic import StrategicIntelligenceSystem


def _make_entity(profile=None, current_project=None):
    """Helper to build a minimal entity for testing."""
    from src.core.builder import V2EntityBuilder
    projects = {current_project.id: current_project} if current_project else {}
    current_id = current_project.id if current_project else None
    
    builder = (V2EntityBuilder(1)
        .kind("hero")
        .location(5.0, 5.0)
        .strategic(projects=projects))
    
    if current_id:
        builder.current_project(current_id)
        
    if profile:
        builder.cognition(
            resistance=profile.interruption_resistance
        )
        
    return builder.build()


class TestInterruptionResistance:
    """Part 1 §Strategic: Project switching uses margin logic."""

    def test_switch_when_no_current_project(self):
        """Always switch if there's no current project."""
        entity = _make_entity()
        candidate = ProjectState(id="new_proj", kind="crafting", status=ProjectStatus.ACTIVE, score=30)
        result = StrategicIntelligenceSystem.evaluate_project_switch(entity, candidate, current_tick=10)
        assert result is not None
        assert result.current_project_id_set == "new_proj"

    def test_retention_when_candidate_below_margin(self):
        """Current project retained when candidate doesn't exceed margin."""
        current = ProjectState(id="current", kind="crafting", status=ProjectStatus.ACTIVE, score=50)
        entity = _make_entity(
            profile=CognitionProfile(interruption_resistance=0.5),
            current_project=current
        )
        # Candidate score 55 vs current 50 + (0.5 * 30) = 65 → candidate loses
        candidate = ProjectState(id="rival", kind="quest", status=ProjectStatus.ACTIVE, score=55)
        result = StrategicIntelligenceSystem.evaluate_project_switch(entity, candidate, current_tick=10)
        assert result is None  # No switch

    def test_switch_when_candidate_exceeds_margin(self):
        """Switch when candidate clearly outscores current + retention bonus."""
        current = ProjectState(id="current", kind="crafting", status=ProjectStatus.ACTIVE, score=50)
        entity = _make_entity(
            profile=CognitionProfile(interruption_resistance=0.3),
            current_project=current
        )
        # Candidate score 80 vs current 50 + (0.3 * 30) = 59 → candidate wins
        candidate = ProjectState(id="urgent", kind="combat", status=ProjectStatus.ACTIVE, score=80)
        result = StrategicIntelligenceSystem.evaluate_project_switch(entity, candidate, current_tick=10)
        assert result is not None
        assert result.current_project_id_set == "urgent"
        # Verify current was suspended
        suspended = [p for p in result.projects_add_or_update if p.id == "current"]
        assert len(suspended) == 1
        assert suspended[0].status == ProjectStatus.SUSPENDED

    def test_higher_resistance_prevents_more_switches(self):
        """Higher resistance → harder to switch."""
        current = ProjectState(id="current", kind="crafting", status=ProjectStatus.ACTIVE, score=50)
        candidate = ProjectState(id="rival", kind="quest", status=ProjectStatus.ACTIVE, score=65)

        # Low resistance: switch happens
        entity_low = _make_entity(
            profile=CognitionProfile(interruption_resistance=0.2),
            current_project=current
        )
        result_low = StrategicIntelligenceSystem.evaluate_project_switch(entity_low, candidate, current_tick=10)
        assert result_low is not None

        # High resistance: switch blocked
        entity_high = _make_entity(
            profile=CognitionProfile(interruption_resistance=0.8),
            current_project=current
        )
        result_high = StrategicIntelligenceSystem.evaluate_project_switch(entity_high, candidate, current_tick=10)
        assert result_high is None

    def test_lock_prevents_switch(self):
        """Project lock prevents any switch regardless of score."""
        current = ProjectState(
            id="locked", kind="crafting", status=ProjectStatus.ACTIVE,
            score=10, lock_until_tick=100
        )
        entity = _make_entity(
            profile=CognitionProfile(interruption_resistance=0.0),
            current_project=current
        )
        candidate = ProjectState(id="rival", kind="quest", status=ProjectStatus.ACTIVE, score=999)
        result = StrategicIntelligenceSystem.evaluate_project_switch(entity, candidate, current_tick=50)
        assert result is None  # Locked until tick 100

    def test_resume_suspended_project(self):
        """Verify a suspended project can be resumed."""
        from src.core.builder import V2EntityBuilder
        suspended = ProjectState(
            id="old_quest", kind="quest", status=ProjectStatus.SUSPENDED,
            score=40, active_objective_id="obj_1"
        )
        entity = (V2EntityBuilder(1)
            .kind("hero")
            .location(5.0, 5.0)
            .strategic(projects={"old_quest": suspended})
            .build())

        result = StrategicIntelligenceSystem.resume_project(entity, "old_quest")
        assert result is not None
        resumed = result.projects_add_or_update[0]
        assert resumed.status == ProjectStatus.ACTIVE
        assert result.current_project_id_set == "old_quest"
        assert result.current_objective_id_set == "obj_1"


class TestCognitionProfile:
    """Part 1 §Strategic: Profile derivation is deterministic."""

    def test_profile_derivation_deterministic(self):
        """Same entity state always produces same profile."""
        from src.core.builder import V2EntityBuilder
        entity = (V2EntityBuilder(1)
            .kind("hero")
            .location(5.0, 5.0)
            .attributes(wisdom=15, intelligence=12)
            .build())
        p1 = StrategicIntelligenceSystem.derive_cognition_profile(entity)
        p2 = StrategicIntelligenceSystem.derive_cognition_profile(entity)
        assert p1 == p2

    def test_higher_stats_produce_larger_capacities(self):
        """Higher WIS/INT → bigger strategic bandwidth."""
        from src.core.builder import V2EntityBuilder
        entity_low = (V2EntityBuilder(1)
            .kind("hero")
            .location(5.0, 5.0)
            .attributes(wisdom=5, intelligence=5, perception=5)
            .build())
        entity_high = (V2EntityBuilder(2)
            .kind("hero")
            .location(5.0, 5.0)
            .attributes(wisdom=25, intelligence=25, perception=25)
            .build())
        p_low = StrategicIntelligenceSystem.derive_cognition_profile(entity_low)
        p_high = StrategicIntelligenceSystem.derive_cognition_profile(entity_high)

        assert p_high.max_leads > p_low.max_leads
        assert p_high.max_concerns > p_low.max_concerns
        assert p_high.interruption_resistance > p_low.interruption_resistance
