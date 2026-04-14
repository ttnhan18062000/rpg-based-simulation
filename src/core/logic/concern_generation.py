"""Concern Generation Service - Logic for injecting strategic interrupts. [PHASE 5]"""

from __future__ import annotations
import uuid
import logging
from typing import TYPE_CHECKING
from src.core.models.strategy import ConcernRecord, ConcernKind, StrategicStatus
from src.core.models.enums import InterpretedLifeEventKind, Domain

if TYPE_CHECKING:
    from src.core.models.world_state import WorldState
    from src.core.entities.entity import Entity
    from src.core.models.life_events import InterpretedLifeEvent
    from src.actions.base import StrategicUpdate
    from src.systems.rng import DeterministicRNG
    from src.ai.cognition_capacity import CognitionCapacityProfile

logger = logging.getLogger(__name__)

class ConcernGenerationService:
    """Rules for mapping interpreted events into strategic pressure."""

    @classmethod
    def generate(
        cls, 
        world: WorldState, 
        entity: Entity, 
        event: InterpretedLifeEvent, 
        updates: StrategicUpdate,
        rng: DeterministicRNG | None = None,
        profile: CognitionCapacityProfile | None = None
    ) -> None:
        """Analyze event and generate ConcernRecords if thresholds are met. [phase_2_intel_capacity]"""
        
        # Resolve profile if missing
        if profile is None:
            from src.ai.cognition_capacity import CognitionCapacityBuilder
            profile = CognitionCapacityBuilder.build(entity)

        # 1. Map Event Kind to Concern
        new_concern = None
        stability = profile.judgment_stability
        
        # Deterministic perturbation factor based on stability
        # A stable entity (1.0) has 1.0 multiplier. An unstable entity (0.5) has higher variance.
        perturb = 1.0
        if rng:
            # We use a deterministic seed to ensure replay stability
            seed_val = rng.next_float(Domain.SOCIAL, entity.id, world.tick, sub_id=50)
            # Factor: stable = 1.0, unstable = 0.8 to 1.5
            perturb = 1.0 + (seed_val - 0.5) * (2.0 * (1.0 - stability))

        if event.kind == InterpretedLifeEventKind.NEAR_DEATH:
            new_concern = ConcernRecord(
                concern_id=f"concern_survival_{rng.next_hex(Domain.SOCIAL, entity.id, world.tick, sub_id=20)}" if rng else f"concern_survival_{uuid.uuid4().hex[:6]}",
                kind=ConcernKind.THREAT,
                label="Recovery & Survival",
                priority=min(10.0, 4.5 * perturb),
                cause_type="event",
                source_event_id=event.event_id,
                urgency=min(1.0, 0.9 * perturb),
                irreversibility=0.8,
                visibility="private",
                created_tick=world.tick
            )
            
        elif event.kind == InterpretedLifeEventKind.ALLY_DIED_NEARBY:
            new_concern = ConcernRecord(
                concern_id=f"concern_grief_{rng.next_hex(Domain.SOCIAL, entity.id, world.tick, sub_id=21)}" if rng else f"concern_grief_{uuid.uuid4().hex[:6]}",
                kind=ConcernKind.THREAT,
                label="Avenge Fallen Ally",
                priority=max(1.0, min(10.0, 3.5 * perturb)),
                cause_type="event",
                source_event_id=event.event_id,
                urgency=min(1.0, 0.6 * perturb),
                attachment_relevance=0.8,
                visibility="shared",
                created_tick=world.tick
            )
            
        elif event.kind == InterpretedLifeEventKind.BETRAYAL:
            new_concern = ConcernRecord(
                concern_id=f"concern_betrayal_{rng.next_hex(Domain.SOCIAL, entity.id, world.tick, sub_id=22)}" if rng else f"concern_betrayal_{uuid.uuid4().hex[:6]}",
                kind=ConcernKind.THREAT,
                label="Justice/Avoidance of Betrayer",
                priority=max(1.0, min(10.0, 4.0 * perturb)),
                cause_type="event",
                source_event_id=event.event_id,
                urgency=min(1.0, 0.7 * perturb),
                social_cost=0.9,
                visibility="private",
                created_tick=world.tick
            )

        elif event.kind == InterpretedLifeEventKind.FLED_FROM_THREAT:
            new_concern = ConcernRecord(
                concern_id=f"concern_shame_{rng.next_hex(Domain.SOCIAL, entity.id, world.tick, sub_id=23)}" if rng else f"concern_shame_{uuid.uuid4().hex[:6]}",
                kind=ConcernKind.THREAT,
                label="Regain Composition/Safety",
                priority=max(1.0, 2.5 * perturb),
                cause_type="event",
                source_event_id=event.event_id,
                urgency=min(1.0, 0.5 * perturb),
                social_cost=0.4,
                visibility="private",
                created_tick=world.tick
            )

        elif event.kind == InterpretedLifeEventKind.HOME_DAMAGED:
            attachment = next((a for a in entity.mind.place_attachments if a.building_id == event.details.get("building_id") or (a.location_pos.x == event.location.x and a.location_pos.y == event.location.y)), None)
            
            base_priority = 4.0
            if attachment:
                base_priority += (attachment.importance * 2.0)
            else:
                base_priority = 1.0
            
            new_concern = ConcernRecord(
                concern_id=f"concern_home_{rng.next_hex(Domain.SOCIAL, entity.id, world.tick, sub_id=24)}" if rng else f"concern_home_{uuid.uuid4().hex[:6]}",
                kind=ConcernKind.THREAT,
                label="Home at Risk",
                priority=max(1.0, base_priority * perturb),
                cause_type="event",
                source_event_id=event.event_id,
                urgency=min(1.0, 0.8 * perturb),
                attachment_relevance=1.0 if attachment else 0.0,
                visibility="private",
                created_tick=world.tick
            )

        elif event.kind == InterpretedLifeEventKind.CONTRACT_BETRAYED_PUBLICLY:
            new_concern = ConcernRecord(
                concern_id=f"concern_betrayer_{rng.next_hex(Domain.SOCIAL, entity.id, world.tick, sub_id=25)}" if rng else f"concern_betrayer_{uuid.uuid4().hex[:6]}",
                kind=ConcernKind.THREAT,
                label="Betrayal Retribution",
                priority=max(1.0, min(10.0, 4.5 * perturb)),
                cause_type="event",
                source_event_id=event.event_id,
                urgency=min(1.0, 0.7 * perturb),
                social_cost=1.0,
                visibility="public",
                created_tick=world.tick
            )

        if new_concern:
            updates.concerns_add_or_update.append(new_concern)
            
            # [phase_2_intel_capacity] "Panic" logic: duplicate/noisy concerns if stability is low
            if stability < 0.7 and rng:
                panic_chance = (0.7 - stability) * 0.5
                if rng.next_float(Domain.SOCIAL, entity.id, world.tick, sub_id=51) < panic_chance:
                    noise_concern = new_concern.model_copy(update={
                        "concern_id": new_concern.concern_id + "_noise",
                        "label": "Fragmentary Panic: " + new_concern.label,
                        "priority": new_concern.priority * 0.8
                    })
                    updates.concerns_add_or_update.append(noise_concern)
                    logger.info("Entity %d generated panic noise concern", entity.id)

            logger.info("Entity %d generated concern: %s (perturb=%.2f)", entity.id, new_concern.label, perturb)
