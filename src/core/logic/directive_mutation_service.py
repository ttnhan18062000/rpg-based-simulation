"""Directive Mutation Service - Logic for identity shifts from turning points. [PHASE 5]"""

from __future__ import annotations
import uuid
import logging
from typing import TYPE_CHECKING
from src.core.models.strategy import DirectiveRecord, DirectiveKind

if TYPE_CHECKING:
    from src.core.models.world_state import WorldState
    from src.core.entities.entity import Entity
    from src.core.models.life_events import TurningPointRecord
    from src.actions.base import StrategicUpdate

logger = logging.getLogger(__name__)

class DirectiveMutationService:
    """Rules for shifting long-term orientations based on salient memories."""

    @classmethod
    def evaluate_mutation(
        cls, 
        world: WorldState, 
        entity: Entity, 
        tp: TurningPointRecord, 
        updates: StrategicUpdate
    ) -> None:
        """Analyze turning point and mutate directives if salience thresholds are met."""
        from src.core.models.enums import TurningPointKind
        
        # High salience requirement for identity shift
        # (Assuming salience_score is calculated in TurningPointService.insert)
        if tp.salience_score < 0.8: 
            return

        # 1. Map Turning Point Kind to Directive Shift
        if tp.kind == TurningPointKind.NEAR_DEATH:
            cls._ensure_directive(entity, updates, "Safety & Self-Preservation", DirectiveKind.PERSONAL, 3.5, "trauma")
            
        elif tp.kind == TurningPointKind.BETRAYAL or tp.kind == TurningPointKind.ALLY_DIED:
            cls._ensure_directive(entity, updates, "Avenge Betrayal/Loss", DirectiveKind.PERSONAL, 3.0, "trauma")
            
        elif tp.kind == TurningPointKind.BOSS_ENCOUNTER:
            if tp.emotional_impact < 0:
                # Failed boss encounter
                cls._ensure_directive(entity, updates, "Ascend/Become Stronger", DirectiveKind.PROFESSIONAL, 3.0, "defeat")
            else:
                # Successful boss encounter
                cls._ensure_directive(entity, updates, "Legendary Ambition", DirectiveKind.PROFESSIONAL, 4.0, "glory")

        elif tp.kind == TurningPointKind.AVENGED_ALLY:
            cls._ensure_directive(entity, updates, "Guardian of the Guild", DirectiveKind.FACTIONAL, 3.5, "loyalty")

        elif tp.kind == TurningPointKind.RESCUE:
            cls._ensure_directive(entity, updates, "Heroic Altruism", DirectiveKind.IDEOLOGICAL, 3.2, "social")

        elif tp.kind == TurningPointKind.FIRST_KILL:
            cls._ensure_directive(entity, updates, "Lethal Resolve", DirectiveKind.PERSONAL, 2.5, "bloodshed")

    @staticmethod
    def _ensure_directive(
        entity: Entity, 
        updates: StrategicUpdate, 
        label: str, 
        kind: DirectiveKind, 
        priority: float,
        source: str
    ) -> None:
        """Check for existing directive by label or add a new one."""
        existing = next((d for d in entity.mind.strategic.directives if d.label == label), None)
        
        if existing:
            # Strengthen priority if already exists
            new_priority = min(5.0, existing.priority + 0.5)
            if new_priority > existing.priority:
                # We update by adding it again to the update list (ActionSystem handles replacement by ID)
                updated_d = existing.model_copy(update={"priority": new_priority})
                updates.directives_add.append(updated_d)
        else:
            # Add new directive
            new_d = DirectiveRecord(
                directive_id=f"dir_{label.lower().replace(' ', '_')}_{uuid.uuid4().hex[:4]}",
                kind=kind,
                label=label,
                priority=priority,
                source=source,
                created_tick=0 # Will be populated by system if needed, or stick to 0 for default
            )
            updates.directives_add.append(new_d)
            logger.info("Entity %d acquired new directive: %s", entity.id, label)
