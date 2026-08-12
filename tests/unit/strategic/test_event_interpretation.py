"""
Contract tests for Strategic Cognition Event Interpretation.

Covers:
- LEG-RPG-116: Strategic pivot on regional danger
- LEG-RPG-117: Scar detection
- Part 1 §Strategic: Event interpretation can mutate directives
- RPG-0049: strategic_outcome_processing
"""
import pytest
from src.core.state import EntityState, RegionState, AuthoritativeState
from src.core.strategic import (
    StrategicComponent, CognitionProfile, ProjectState, ProjectStatus,
    ObjectiveState, ObjectiveStatus, DirectiveState, DirectivePriority, ProjectKind
)
from src.systems.event_interpreter import EventInterpreter
from src.ai.goals.region_stabilization_scorer import RegionStabilizationGoalScorer
from src.systems.strategic import StrategicIntelligenceSystem


def _make_entity(entity_id=1, profile=None, current_project=None):
    """Helper to build a minimal entity for testing."""
    from src.core.builder import V2EntityBuilder
    projects = {current_project.id: current_project} if current_project else {}
    current_id = current_project.id if current_project else None
    
    builder = (V2EntityBuilder(entity_id)
        .kind("hero")
        .location(5.0, 5.0)
        .strategic(projects=projects))
    
    if current_id:
        builder.strategic(current_project_id=current_id)
        
    if profile:
        builder.cognition(
            interruption_resistance=profile.interruption_resistance
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
        """
        TCK-20260811-REGION-STABILIZATION-GOAL-SCORER, AC2/AC4: rewritten to exercise the new
        scorer path (interpret_regional_danger() itself no longer spawns/pivots any project --
        see AC2). Equivalent assertions:
        (1) interpret_regional_danger() still returns a concern and no longer sets
            current_project_id_set or projects_add_or_update at all;
        (2) RegionStabilizationGoalScorer().score(entity, state) on an entity positioned inside
            the same high-hazard region returns a non-zero-utility GoalScore whose
            metadata["raw_score"] is populated and calibrated to the 2.9 ceiling;
        (3) StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)
            end-to-end produces a suspended proj_craft (same outcome as before the migration)
            and a new active project whose id contains "stabilize" and whose
            kind == ProjectKind.STABILIZE (the enum member, not the bare string).

        interruption_resistance=0.01 (not the original 0.3) is deliberate, not an oversight:
        Design Decision #5 drops the old direct `urgency > interruption_resistance` pre-filter
        entirely in favor of evaluate_project_switch()'s own retention_margin gate, whose raw,
        unnormalized comparison (`candidate.score > current.score + retention_margin`) requires
        a much lower resistance value to clear against a raw stabilize score capped at 2.9 --
        this is the disclosed behavior change Design Decision #5 documents.

        current: kind="crafting" (bare string, 100-ceiling scale, unaffected by this ticket),
        score=1.0, lock_until_tick=0 (default, unlocked) -> unlocked-path final check only:
        retention_margin = 0.01*30.0 = 0.3; effective_current_score = 1.0+0.3 = 1.3.
        region "swamp": hazard_level=0.95 -> urgency=min(1.0,(0.95-0.7)/0.3)=0.8333333333333333;
        raw_score = urgency*2.9 = 2.4166666666666665 > 1.3 -> switch succeeds.
        """
        current = ProjectState(id="proj_craft", kind="crafting", status=ProjectStatus.ACTIVE, score=1.0)
        entity = _make_entity(
            profile=CognitionProfile(interruption_resistance=0.01),
            current_project=current
        )
        region = RegionState(id="swamp", name="Swamp", bounds=(0, 0, 10, 10), hazard_level=0.95)

        # (1) interpret_regional_danger() is concern-generation only (AC2).
        interp_result = EventInterpreter.interpret_regional_danger(entity, region, current_tick=20)
        assert interp_result is not None
        assert interp_result.current_project_id_set is None
        assert interp_result.projects_add_or_update == []
        assert len(interp_result.concerns_add_or_update) == 1

        # (2) The scorer independently reproduces the danger decision against real state.
        state = AuthoritativeState(
            tick=20, seed=42, entities={entity.id: entity}, regions={"swamp": region}
        )
        score = RegionStabilizationGoalScorer().score(entity, state)
        assert score.utility > 0.0
        assert score.metadata["raw_score"] == pytest.approx(2.4166666666666665)
        assert score.metadata["raw_score"] <= 2.9

        # (3) End-to-end materialization through the arbiter.
        result = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)
        assert result is not None
        suspended = [p for p in result.projects_add_or_update if p.id == "proj_craft"]
        assert len(suspended) == 1
        assert suspended[0].status == ProjectStatus.SUSPENDED
        assert result.current_project_id_set is not None
        assert "stabilize" in result.current_project_id_set
        new_project = next(
            p for p in result.projects_add_or_update if p.id == result.current_project_id_set
        )
        assert new_project.kind == ProjectKind.STABILIZE

    def test_no_pivot_when_resistance_high(self):
        """
        TCK-20260811-REGION-STABILIZATION-GOAL-SCORER, AC2/AC4: rewritten to exercise the new
        scorer path. Equivalent assertions:
        (1) interpret_regional_danger() still generates a concern and current_project_id_set is
            None -- now true simply because the method never sets it at all (AC2), not because
            urgency (0.167) is less than the entity's own resistance (0.9) the way the old
            `should_pivot` pre-filter judged it. This is itself a disclosed semantic shift
            (Design Decision #5): the old direct urgency-vs-resistance comparison no longer
            exists anywhere in this codebase.
        (2) The scorer/arbiter path, exercised end-to-end via evaluate_strategic_intent(), does
            NOT switch current_project_id away from proj_craft -- because a raw stabilize score
            capped at 2.9 can never clear even a modest crafting project's raw
            effective_current_score under the unlocked-path final check, regardless of
            resistance. hazard 0.75 -> urgency=(0.75-0.7)/0.3~=0.1667 -> raw_score~=0.4833;
            current: score=50, lock_until_tick=0 (unlocked) -> retention_margin=0.9*30=27 ->
            effective_current_score=77; 0.4833 > 77 is False -> no switch.
        """
        current = ProjectState(id="proj_craft", kind="crafting", status=ProjectStatus.ACTIVE, score=50)
        entity = _make_entity(
            profile=CognitionProfile(interruption_resistance=0.9),
            current_project=current
        )
        # hazard 0.75 → urgency = (0.75-0.7)/0.3 ≈ 0.167
        region = RegionState(id="hills", name="Hills", bounds=(0, 0, 10, 10), hazard_level=0.75)

        interp_result = EventInterpreter.interpret_regional_danger(entity, region, current_tick=30)
        assert interp_result is not None
        # Concern generated; current_project_id_set is None -- now unconditionally true (AC2),
        # not conditional on resistance the way it was before this migration.
        assert len(interp_result.concerns_add_or_update) == 1
        assert interp_result.current_project_id_set is None

        state = AuthoritativeState(
            tick=30, seed=42, entities={entity.id: entity}, regions={"hills": region}
        )
        result = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)
        assert result is not None
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
            .location(5.0, 5.0)
            .strategic(directives={"directive_avenge_bandit_001": existing})
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
