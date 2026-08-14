# Compliance IDs: STRAT-067
"""
Event Interpretation Pipeline for Strategic Cognition.

Translates world/combat/social events into strategic mutations:
- Directives (enduring intentions)
- Concerns (environmental pressures)
- Project pivots (interrupting current work)
- Source trust recalibration

Covers:
- LEG-RPG-116: Strategic pivot on regional danger
- LEG-RPG-117: Scar detection and investigation
- Part 1 §Strategic: Event interpretation can mutate directives, projects, concerns, and source trust
"""
from __future__ import annotations
from dataclasses import replace
from typing import Optional, List

from src.core.state import EntityState, RegionState
from src.core.strategic import (
    DirectiveState, DirectivePriority, ConcernState,
    ProjectState, ProjectStatus, ObjectiveState, ObjectiveStatus,
    CognitionProfile
)
from src.core.updates import StrategicUpdate


class EventInterpreter:
    """
    Pure decision logic: reads entity + world state, returns StrategicUpdate.
    Does NOT mutate any state directly.
    """

    @staticmethod
    def compute_danger_urgency(region: RegionState) -> Optional[float]:
        """
        LEG-RPG-116: pure hazard-threshold/urgency math, byte-identical to the original inline
        computation this method replaces (events.py, historical lines 48-51). Extracted so
        interpret_regional_danger()'s own concern generation and RegionStabilizationGoalScorer
        (src/ai/goals/region_stabilization_scorer.py) share a single source of truth for the
        threshold/formula -- see plan.md TCK-20260811-REGION-STABILIZATION-GOAL-SCORER, New
        Finding #9, mirroring ContractService.get_project_mapping()'s own extraction precedent
        from TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER.

        Returns None if region.hazard_level <= 0.7 (no danger -- no concern, no candidate).
        Returns urgency in [0.0, 1.0] otherwise: 0.0 at hazard_level=0.7, 1.0 at hazard_level>=1.0.
        """
        if region.hazard_level <= 0.7:
            return None
        return min(1.0, (region.hazard_level - 0.7) / 0.3)

    @staticmethod
    def interpret_regional_danger(
        entity: EntityState,
        region: RegionState,
        current_tick: int
    ) -> Optional[StrategicUpdate]:
        """
        LEG-RPG-116: Strategic pivot on regional danger -- concern generation only.

        Project-pivot spawning is no longer performed here
        (TCK-20260811-REGION-STABILIZATION-GOAL-SCORER): RegionStabilizationGoalScorer
        (src/ai/goals/region_stabilization_scorer.py) now scores every entity's current region
        each tick as a tier-5 GoalRegistry candidate (via the shared
        EventInterpreter.compute_danger_urgency() helper), and the winning candidate is
        materialized into a real ProjectState/ObjectiveState by
        StrategicIntelligenceSystem.evaluate_strategic_intent()'s
        `elif best_candidate.kind == GoalKind.REGION_STABILIZATION:` branch, through
        evaluate_project_switch() -- not unconditionally. `entity` is retained as a parameter
        (unused by this simplified body) to preserve this method's existing call signature for
        its other 2 direct test call sites and for consistency with sibling
        EventInterpreter methods (interpret_scar_detection, interpret_near_death,
        interpret_directive_event all take `entity` as their first argument) -- see plan.md
        Scope Guards.
        """
        urgency = EventInterpreter.compute_danger_urgency(region)
        if urgency is None:
            return None

        concern = ConcernState(
            id=f"concern_danger_{region.id}",
            kind="danger",
            source=region.id,
            urgency=urgency,
            created_tick=current_tick
        )

        return StrategicUpdate(concerns_add_or_update=[concern])

    @staticmethod
    def interpret_scar_detection(
        entity: EntityState,
        region: RegionState,
        current_tick: int
    ) -> Optional[StrategicUpdate]:
        """
        LEG-RPG-117: Scar detection.

        If a nearby region has trauma_score > 0.5, the entity detects it
        and generates an INVESTIGATE objective.
        """
        if region.trauma_score <= 0.5:
            return None

        # Generate an investigation objective
        investigate_project = ProjectState(
            id=f"project_investigate_scar_{region.id}",
            kind="exploration",
            status=ProjectStatus.ACTIVE,
            score=region.trauma_score * 50,
            objectives=[
                ObjectiveState(
                    id=f"obj_investigate_scar_{region.id}",
                    kind="investigate",
                    target=region.id,
                    status=ObjectiveStatus.ACTIVE
                )
            ],
            active_objective_id=f"obj_investigate_scar_{region.id}",
            created_tick=current_tick
        )

        return StrategicUpdate(
            projects_add_or_update=[investigate_project],
            concerns_add_or_update=[
                ConcernState(
                    id=f"concern_scar_{region.id}",
                    kind="opportunity",
                    source=region.id,
                    urgency=region.trauma_score * 0.5,
                    created_tick=current_tick
                )
            ]
        )

    @staticmethod
    def interpret_near_death(
        entity: EntityState,
        current_tick: int
    ) -> StrategicUpdate:
        """
        Near-death event: generates a survival concern and may suspend current project.
        """
        concern = ConcernState(
            id=f"concern_near_death_{current_tick}",
            kind="danger",
            source="self",
            urgency=0.9,
            created_tick=current_tick
        )

        # Always interrupts — near death is urgent
        updates = StrategicUpdate(
            concerns_add_or_update=[concern],
            overload_source_set="trauma",
            overload_tick_set=current_tick
        )

        if entity.strategic.current_project_id:
            current = entity.strategic.projects.get(entity.strategic.current_project_id)
            if current and current.status == ProjectStatus.ACTIVE:
                updates = replace(
                    updates,
                    projects_add_or_update=[replace(current, status=ProjectStatus.SUSPENDED)],
                    current_project_id_set=None,
                    current_objective_id_set=None
                )

        return updates

    @staticmethod
    def interpret_directive_event(
        entity: EntityState,
        event_kind: str,
        target: Optional[str],
        salience: float,
        current_tick: int
    ) -> Optional[StrategicUpdate]:
        """
        Part 1 §Strategic: Event interpretation can mutate directives.

        Only high-salience events (> 0.5) create or strengthen directives.
        Repeated events of the same kind accumulate salience.
        """
        if salience <= 0.5:
            return None

        directive_id = f"directive_{event_kind}_{target or 'general'}"

        # Check if directive already exists
        existing = entity.strategic.directives.get(directive_id)
        if existing:
            # Strengthen existing directive
            new_salience = min(1.0, existing.salience + salience * 0.3)
            new_priority = existing.priority
            if new_salience > 0.8:
                new_priority = DirectivePriority.HIGH
            if new_salience > 0.95:
                new_priority = DirectivePriority.CRITICAL

            updated = replace(
                existing,
                salience=new_salience,
                priority=new_priority
            )
        else:
            # Create new directive
            priority = DirectivePriority.NORMAL
            if salience >= 0.8:
                priority = DirectivePriority.HIGH

            updated = DirectiveState(
                id=directive_id,
                kind=event_kind,
                target=target,
                priority=priority,
                salience=salience,
                created_tick=current_tick
            )

        return StrategicUpdate(directives_add_or_update=[updated])
