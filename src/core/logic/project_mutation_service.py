"""Project Mutation Service - Logic for history-sensitive project interruptions. [PHASE 5]"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Optional
from src.core.models.strategy import StrategicStatus, ProjectRecord

if TYPE_CHECKING:
    from src.core.models.world_state import WorldState
    from src.core.entities.entity import Entity
    from src.core.models.life_events import InterpretedLifeEvent, TurningPointRecord
    from src.actions.base import StrategicUpdate

logger = logging.getLogger(__name__)

class ProjectMutationService:
    """Rules for suspending, mutating, or abandoning projects based on events."""

    @classmethod
    def process_interruption(
        cls, 
        world: WorldState, 
        entity: Entity, 
        event: InterpretedLifeEvent, 
        tp: Optional[TurningPointRecord], 
        updates: StrategicUpdate
    ) -> None:
        """Evaluate if the current project should be suspended or mutated."""
        current = entity.mind.strategic.current_project
        if not current:
            return

        # 1. High-Impact Turning Points (Trauma/Betrayal)
        if tp and tp.salience_score > 6.0:
            from src.core.models.enums import TurningPointKind
            if tp.kind in (TurningPointKind.BETRAYAL, TurningPointKind.ALLY_DIED, TurningPointKind.NEAR_DEATH):
                # Major life event — current project is likely obsolete or needs total pivot
                cls._suspend_project(current, updates, f"Major Trauma: {tp.kind.name}", [event.event_id])
                return

        # 2. Concerns-driven Interruption
        # If the StrategicConsequenceService just added a high-priority concern, 
        # we should probably suspend the current project if it's not urgent enough.
        # However, StrategicInterruptionService (Tactical) usually handles the *decision*.
        # This service handles the *mutation* and *recovery semantics*.
        
        # We look at the concerns we just added to the updates
        for concern in updates.concerns_add_or_update:
            if concern.priority > current.priority + current.interruption_threshold:
                # We should record that this project IS being interrupted by this concern
                cls._suspend_project(current, updates, f"Strategic Interrupt: {concern.label}", [event.event_id])
                # Note: AIBrain will actually switch the current_project_id later.
                # Here we just prepare the record for suspension.

    @staticmethod
    def _suspend_project(
        project: ProjectRecord, 
        updates: StrategicUpdate, 
        reason: str, 
        event_ids: list[str]
    ) -> None:
        """Prepare a project update that marks it as suspended with recovery metadata."""
        # Use existing record but modify fields
        updated_p = project.model_copy(update={
            "status": StrategicStatus.SUSPENDED,
            "suspension_reason": reason,
            "interrupted_by_event_ids": list(set(project.interrupted_by_event_ids + event_ids)),
            "recovery_behavior": "resume" # Default to resume for now
        })
        
        # Check if already in updates to avoid duplicates
        found = False
        for i, up in enumerate(updates.projects_add_or_update):
            if up.project_id == project.project_id:
                updates.projects_add_or_update[i] = updated_p
                found = True
                break
        if not found:
            updates.projects_add_or_update.append(updated_p)
        
        # Also ensure current_project_id is cleared if we are suspending
        updates.interrupted_project_id = project.project_id
        # We don't clear current_project_id here yet, because AIBrain needs to know it's switching.
        # Actually, ActionSystem application of StrategicUpdate will set current_project_id if provided.
        # But here we are just providing the mutated project record.
        
        logger.info("Project %s suspended: %s", project.project_id, reason)
