"""Project Mutation Service - Logic for history-sensitive project interruptions. [PHASE 5]"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Optional
from src.core.models.strategy import StrategicStatus, ProjectRecord

if TYPE_CHECKING:
    from src.core.models.world_state import WorldState
    from src.core.models.snapshot import Snapshot
    from src.core.entities.entity import Entity
    from src.core.models.life_events import InterpretedLifeEvent, TurningPointRecord
    from src.actions.base import StrategicUpdate
    from src.ai.cognition_capacity import CognitionCapacityProfile

logger = logging.getLogger(__name__)

class ProjectMutationService:
    """Rules for suspending, mutating, or abandoning projects based on events."""

    @classmethod
    def process_interruption(
        cls, 
        world: WorldState | Snapshot, 
        entity: Entity, 
        event: InterpretedLifeEvent, 
        tp: Optional[TurningPointRecord], 
        updates: StrategicUpdate,
        profile: CognitionCapacityProfile | None = None
    ) -> None:
        """Evaluate if the current project should be suspended or mutated. [phase_2_intel_capacity]"""
        current = entity.mind.strategic.current_project
        if not current:
            return
            
        # Resolve profile if missing
        if profile is None:
            from src.ai.cognition_capacity import CognitionCapacityBuilder
            profile = CognitionCapacityBuilder.build(entity)

        # 1. High-Impact Turning Points (Trauma/Betrayal)
        # Bounded by judgment stability and abandonment threshold
        salience_threshold = 6.0 * profile.judgment_stability
        if tp and tp.salience_score > salience_threshold:
            from src.core.models.enums import TurningPointKind
            if tp.kind in (TurningPointKind.BETRAYAL, TurningPointKind.ALLY_DIED, TurningPointKind.NEAR_DEATH):
                # Major life event — current project is likely obsolete or needs total pivot
                # Abandonment cost check
                if profile.abandonment_threshold_mod > 0.8:
                    cls._suspend_project(current, updates, f"Major Trauma: {tp.kind.name}", [event.event_id])
                else:
                    # Low abandonment threshold -> just abandon it
                    cls._abandon_project(current, updates, f"Traumatic Abandonment: {tp.kind.name}", [event.event_id])
                return

        # 2. Concerns-driven Interruption
        # Bounded by interruption resistance
        resistance_mod = (profile.interruption_resistance - 0.5) * 0.4 # range -0.2 to +0.2
        effective_threshold = current.interruption_threshold + resistance_mod

        for concern in updates.concerns_add_or_update:
            if concern.priority > current.priority + effective_threshold:
                # Decide: Suspend or Pivot?
                from src.core.models.enums import ConcernKind, ProjectKind
                
                # Pivot logic: If it's a threat and we were exploring, pivot to survival/defense
                if concern.kind == ConcernKind.THREAT and current.kind == ProjectKind.EXPLORATION:
                     cls._pivot_project(current, updates, ProjectKind.DEVELOPMENT, f"Threat response: {concern.label}", [event.event_id])
                else:
                     cls._suspend_project(current, updates, f"Strategic Interrupt: {concern.label}", [event.event_id])
                
                return

    @staticmethod
    def _pivot_project(
        project: ProjectRecord,
        updates: StrategicUpdate,
        new_kind: ProjectKind,
        reason: str,
        event_ids: list[str]
    ) -> None:
        """Mutate a project's kind while preserving progress if possible."""
        updated_p = project.model_copy(update={
            "kind": new_kind,
            "label": f"Pivoted: {project.label} ({reason})",
            "interrupted_by_event_ids": list(set(project.interrupted_by_event_ids) | set(event_ids)),
            "urgency": max(project.urgency, 0.7) # Increase urgency for pivots
        })
        
        # Merge into updates
        found = False
        for i, up in enumerate(updates.projects_add_or_update):
            if up.project_id == project.project_id:
                updates.projects_add_or_update[i] = updated_p
                found = True
                break
        if not found:
            updates.projects_add_or_update.append(updated_p)
            
        # Record interruption for AIBrain awareness
        updates.interrupted_project_id = project.project_id
            
        logger.info("Project %s pivoted to %s: %s", project.project_id, new_kind.name, reason)

    @staticmethod
    def _suspend_project(
        project: ProjectRecord, 
        updates: StrategicUpdate, 
        reason: str, 
        event_ids: list[str]
    ) -> None:
        """Prepare a project update that marks it as suspended with recovery metadata."""
        updated_p = project.model_copy(update={
            "status": StrategicStatus.SUSPENDED,
            "suspension_reason": reason,
            "interrupted_by_event_ids": list(set(project.interrupted_by_event_ids) | set(event_ids)),
            "recovery_behavior": "resume"
        })
        
        found = False
        for i, up in enumerate(updates.projects_add_or_update):
            if up.project_id == project.project_id:
                updates.projects_add_or_update[i] = updated_p
                found = True
                break
        if not found:
            updates.projects_add_or_update.append(updated_p)
        
        updates.interrupted_project_id = project.project_id
        logger.info("Project %s suspended: %s", project.project_id, reason)

    @staticmethod
    def _abandon_project(
        project: ProjectRecord,
        updates: StrategicUpdate,
        reason: str,
        event_ids: list[str]
    ) -> None:
        """Prepare a project update that marks it as abandoned. [phase_2_intel_capacity]"""
        updated_p = project.model_copy(update={
            "status": StrategicStatus.ABANDONED,
            "abandonment_reason": reason,
            "interrupted_by_event_ids": list(set(project.interrupted_by_event_ids) | set(event_ids))
        })
        
        found = False
        for i, up in enumerate(updates.projects_add_or_update):
            if up.project_id == project.project_id:
                updates.projects_add_or_update[i] = updated_p
                found = True
                break
        if not found:
            updates.projects_add_or_update.append(updated_p)
        
        updates.interrupted_project_id = project.project_id
        logger.info("Project %s abandoned: %s", project.project_id, reason)
