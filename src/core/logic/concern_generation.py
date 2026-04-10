"""Concern Generation Service - Logic for injecting strategic interrupts. [PHASE 5]"""

from __future__ import annotations
import uuid
import logging
from typing import TYPE_CHECKING
from src.core.models.strategy import ConcernRecord, ConcernKind, StrategicStatus

if TYPE_CHECKING:
    from src.core.models.world_state import WorldState
    from src.core.entities.entity import Entity
    from src.core.models.life_events import InterpretedLifeEvent
    from src.actions.base import StrategicUpdate

logger = logging.getLogger(__name__)

class ConcernGenerationService:
    """Rules for mapping interpreted events into strategic pressure."""

    @classmethod
    def generate(
        cls, 
        world: WorldState, 
        entity: Entity, 
        event: InterpretedLifeEvent, 
        updates: StrategicUpdate
    ) -> None:
        """Analyze event and generate ConcernRecords if thresholds are met."""
        from src.core.models.enums import InterpretedLifeEventKind
        
        # 1. Map Event Kind to Concern
        new_concern = None
        
        if event.kind == InterpretedLifeEventKind.NEAR_DEATH:
            new_concern = ConcernRecord(
                concern_id=f"concern_survival_{uuid.uuid4().hex[:6]}",
                kind=ConcernKind.THREAT,
                label="Recovery & Survival",
                priority=4.5, # Very high
                cause_type="event",
                source_event_id=event.event_id,
                urgency=0.9,
                irreversibility=0.8,
                visibility="private",
                created_tick=world.tick
            )
            
        elif event.kind == InterpretedLifeEventKind.ALLY_DIED_NEARBY:
            # Check attachment / relationship to deceased (not fully implemented in EventInterpreter yet, but assume it matters)
            new_concern = ConcernRecord(
                concern_id=f"concern_grief_{uuid.uuid4().hex[:6]}",
                kind=ConcernKind.THREAT,
                label="Avenge Fallen Ally",
                priority=3.5,
                cause_type="event",
                source_event_id=event.event_id,
                urgency=0.6,
                attachment_relevance=0.8,
                visibility="shared",
                created_tick=world.tick
            )
            
        elif event.kind == InterpretedLifeEventKind.BETRAYAL:
            new_concern = ConcernRecord(
                concern_id=f"concern_betrayal_{uuid.uuid4().hex[:6]}",
                kind=ConcernKind.THREAT,
                label="Justice/Avoidance of Betrayer",
                priority=4.0,
                cause_type="event",
                source_event_id=event.event_id,
                urgency=0.7,
                social_cost=0.9,
                visibility="private",
                created_tick=world.tick
            )

        elif event.kind == InterpretedLifeEventKind.FLED_FROM_THREAT:
            new_concern = ConcernRecord(
                concern_id=f"concern_shame_{uuid.uuid4().hex[:6]}",
                kind=ConcernKind.THREAT,
                label="Regain Composition/Safety",
                priority=2.5,
                cause_type="event",
                source_event_id=event.event_id,
                urgency=0.5,
                social_cost=0.4,
                visibility="private",
                created_tick=world.tick
            )

        if new_concern:
            updates.concerns_add_or_update.append(new_concern)
            logger.info("Entity %d generated concern: %s", entity.id, new_concern.label)
