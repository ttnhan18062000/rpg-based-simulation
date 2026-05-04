"""
Contract tests for Strategic Cognition Event Interpretation.

Covers:
- LEG-RPG-116: Strategic pivot on regional danger
- LEG-RPG-117: Scar detection
- Part 1 §Strategic: Event interpretation can mutate directives
- RPG-0049: strategic_outcome_processing
"""
import pytest
from src.core.state import EntityState, RegionState
from src.core.strategic import (
    StrategicComponent, CognitionProfile, ProjectState, ProjectStatus,
    ObjectiveState, ObjectiveStatus, DirectiveState, DirectivePriority
)
from src.systems.event_interpreter import EventInterpreter


def _make_entity(entity_id=1, profile=None, current_project=None):
    """Helper to build a minimal entity for testing."""
    from src.core.builder import V2EntityBuilder
    projects = {current_project.id: current_project} if current_project else {}
    current_id = current_project.id if current_project else None
    
    builder = (V2EntityBuilder(entity_id)
        .kind("hero")
        .at((5.0, 5.0))
        .with_strategic(projects=projects))
    
    if current_id:
        builder.current_project(current_id)
        
    if profile:
        builder.with_strategic_profile(
            resistance=profile.interruption_resistance
        )
        
    return builder.build()


class TestStrategicPivotOnDanger:
    """LEG-RPG-116: Strategic pivot on regional danger."""

    def test_no_pivot_when_hazard_low(self):
        entity = _make_entity()
        region = RegionState(id="forest", name="Forest", bounds=(0, 0, 10, 10), hazard_level=0.5)
        result = EventInterpreter.interpret_regional_danger(entity, region, current_tick=10)
        assert result is None

    def test_concern_generated_on_high_hazard(self):
        entity = _make_entity()
        region = RegionState(id="forest", name="Forest", bounds=(0, 0, 10, 10), hazard_level=0.85)
        result = EventInterpreter.interpret_regional_danger(entity, region, current_tick=10)
        assert result is not None
        assert len(result.concerns_add_or_update) == 1
        concern = result.concerns_add_or_update[0]
        assert concern.kind == "danger"
        assert concern.source == "forest"

    def test_project_pivot_when_urgency_exceeds_resistance(self):
        """Entity with low resistance pivots project on danger."""
        current = ProjectState(id="proj_craft", kind="crafting", status=ProjectStatus.ACTIVE, score=50)
        entity = _make_entity(
            profile=CognitionProfile(interruption_resistance=0.3),
            current_project=current
        )
        region = RegionState(id="swamp", name="Swamp", bounds=(0, 0, 10, 10), hazard_level=0.95)
        result = EventInterpreter.interpret_regional_danger(entity, region, current_tick=20)
        assert result is not None
        # Current project should be suspended
        suspended = [p for p in result.projects_add_or_update if p.id == "proj_craft"]
        assert len(suspended) == 1
        assert suspended[0].status == ProjectStatus.SUSPENDED
        # New stabilize project should be active
        assert result.current_project_id_set is not None
        assert "stabilize" in result.current_project_id_set

    def test_no_pivot_when_resistance_high(self):
        """Entity with high resistance keeps current project."""
        current = ProjectState(id="proj_craft", kind="crafting", status=ProjectStatus.ACTIVE, score=50)
        entity = _make_entity(
            profile=CognitionProfile(interruption_resistance=0.9),
            current_project=current
        )
        # hazard 0.75 → urgency = (0.75-0.7)/0.3 ≈ 0.167, which is < 0.9 resistance
        region = RegionState(id="hills", name="Hills", bounds=(0, 0, 10, 10), hazard_level=0.75)
        result = EventInterpreter.interpret_regional_danger(entity, region, current_tick=30)
        assert result is not None
        # Concern generated but no project pivot
        assert len(result.concerns_add_or_update) == 1
        assert result.current_project_id_set is None


class TestScarDetection:
    """LEG-RPG-117: Scar detection."""

    def test_no_detection_when_trauma_low(self):
        entity = _make_entity()
        region = RegionState(id="plains", name="Plains", bounds=(0, 0, 10, 10), trauma_score=0.3)
        result = EventInterpreter.interpret_scar_detection(entity, region, current_tick=10)
        assert result is None

    def test_investigation_generated_on_high_trauma(self):
        entity = _make_entity()
        region = RegionState(id="ruins", name="Ruins", bounds=(0, 0, 10, 10), trauma_score=0.7)
        result = EventInterpreter.interpret_scar_detection(entity, region, current_tick=15)
        assert result is not None
        # Should generate an investigation project
        assert len(result.projects_add_or_update) == 1
        project = result.projects_add_or_update[0]
        assert project.kind == "exploration"
        assert len(project.objectives) == 1
        assert project.objectives[0].kind == "investigate"
        assert project.objectives[0].target == "ruins"
        # Should generate a concern
        assert len(result.concerns_add_or_update) == 1
        assert result.concerns_add_or_update[0].kind == "opportunity"


class TestDirectiveEvent:
    """Part 1 §Strategic: Event interpretation can mutate directives."""

    def test_low_salience_ignored(self):
        entity = _make_entity()
        result = EventInterpreter.interpret_directive_event(
            entity, event_kind="explore", target="cave", salience=0.3, current_tick=5
        )
        assert result is None

    def test_high_salience_creates_directive(self):
        entity = _make_entity()
        result = EventInterpreter.interpret_directive_event(
            entity, event_kind="avenge", target="bandit_001", salience=0.8, current_tick=5
        )
        assert result is not None
        assert len(result.directives_add_or_update) == 1
        d = result.directives_add_or_update[0]
        assert d.kind == "avenge"
        assert d.target == "bandit_001"
        assert d.priority == DirectivePriority.HIGH

    def test_repeated_events_strengthen_directive(self):
        """Salience accumulates on repeated events."""
        from src.core.builder import V2EntityBuilder
        existing = DirectiveState(
            id="directive_avenge_bandit_001", kind="avenge",
            target="bandit_001", priority=DirectivePriority.NORMAL, salience=0.6
        )
        entity = (V2EntityBuilder(1)
            .kind("hero")
            .at((5.0, 5.0))
            .with_strategic(directives={"directive_avenge_bandit_001": existing})
            .build())

        result = EventInterpreter.interpret_directive_event(
            entity, event_kind="avenge", target="bandit_001", salience=0.7, current_tick=10
        )
        assert result is not None
        d = result.directives_add_or_update[0]
        assert d.salience > existing.salience
        assert d.priority in (DirectivePriority.HIGH, DirectivePriority.CRITICAL)


class TestNearDeath:
    """Near-death event handling."""

    def test_near_death_generates_concern(self):
        entity = _make_entity()
        result = EventInterpreter.interpret_near_death(entity, current_tick=50)
        assert len(result.concerns_add_or_update) == 1
        assert result.concerns_add_or_update[0].urgency == 0.9
        assert result.overload_source_set == "trauma"

    def test_near_death_suspends_current_project(self):
        current = ProjectState(id="proj_quest", kind="quest", status=ProjectStatus.ACTIVE, score=30)
        entity = _make_entity(current_project=current)
        result = EventInterpreter.interpret_near_death(entity, current_tick=60)
        suspended = [p for p in result.projects_add_or_update if p.id == "proj_quest"]
        assert len(suspended) == 1
        assert suspended[0].status == ProjectStatus.SUSPENDED
        assert result.current_project_id_set is None
