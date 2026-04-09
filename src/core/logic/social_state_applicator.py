"""Social State Applicator — orchestrates the application of interpreted social events. [PHASE 2]

This service is the hub for Stage 4 implementation. It takes InterpretedLifeEvents
and routes them to TurningPointService, RelationshipService, and ReputationService.
It ensures that semantic interpretations actually change the simulation state.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List

from src.core.logic.turning_points import TurningPointService
from src.core.logic.relationship_service import RelationshipService
from src.core.logic.reputation_service import ReputationService
from src.core.models.life_events import TurningPointRecord
from src.core.models.enums import TurningPointKind

if TYPE_CHECKING:
    from src.core.entities.entity import Entity
    from src.core.models.world_state import WorldState
    from src.core.models.life_events import InterpretedLifeEvent
    from src.actions.base import SocialUpdate, ReputationUpdate

logger = logging.getLogger(__name__)

class SocialStateApplicator:
    """Orchestrates social state updates from interpreted events."""

    @classmethod
    def apply_interpreted_event(
        cls, 
        event: InterpretedLifeEvent, 
        world: WorldState
    ) -> None:
        """Apply an interpreted event to the world and involved entities."""
        tick = world.tick
        actor = world.get_entity(event.actor_id)
        if not actor:
            return

        # 1. Handle Turning Point Candidates
        if event.turning_point_candidate:
            tp = TurningPointRecord(
                event_id=event.event_id,
                kind=cls._map_event_to_tp_kind(event.kind),
                tick=tick,
                location=event.location,
                involved_entity_ids=event.subject_ids,
                emotional_impact=event.severity,
                relationship_effects=event.relationship_deltas,
                reputation_effects=event.reputation_deltas,
                tags_add=event.tags_add,
                tags_remove=event.tags_remove,
                salience_score=0.0 # Will be calc'd in insert
            )
            TurningPointService.insert(actor, tp, tick)

        # 2. Apply Reputation Deltas (Authoritative)
        if event.reputation_deltas:
            from src.actions.base import ReputationUpdate
            # Ensure keys match ReputationUpdate fields (e.g. 'heroism_score' -> 'heroism_delta')
            rep_data = {}
            for k, v in event.reputation_deltas.items():
                field_name = k.replace('_score', '') + '_delta'
                if field_name == 'notoriety_delta': field_name = 'threat_notoriety_delta'
                rep_data[field_name] = v
            
            update = ReputationUpdate(
                tags_add=event.tags_add,
                tags_remove=event.tags_remove,
                **rep_data
            )
            ReputationService.apply_update(actor, update)

        # 3. Apply Relationship Deltas
        for subject_id, deltas in event.relationship_deltas.items():
            from src.actions.base import SocialUpdate
            # Mapping short names to delta fields (e.g. 'trust' -> 'trust_delta')
            social_data = {f"{k}_delta": v for k, v in deltas.items()}
            
            # Authoritative choice: Subject's view of Actor changes based on Actor's action
            update = SocialUpdate(
                source_id=subject_id, # The perceiver
                target_id=event.actor_id, # The perceived
                **social_data
            )
            RelationshipService.apply_update(world.social_registry, update, tick)

    @staticmethod
    def _map_event_to_tp_kind(event_kind: int) -> TurningPointKind:
        """Internal mapping from interpretation kind to durable turning point kind."""
        # Simple mapping for Phase 2 Stage 4
        from src.core.models.enums import InterpretedLifeEventKind
        
        mapping = {
            InterpretedLifeEventKind.NEAR_DEATH: TurningPointKind.NEAR_DEATH,
            InterpretedLifeEventKind.ALLY_DIED_NEARBY: TurningPointKind.ALLY_DIED,
            InterpretedLifeEventKind.AVENGED_ALLY: TurningPointKind.AVENGED_ALLY,
            InterpretedLifeEventKind.FIRST_BOSS_ENCOUNTER: TurningPointKind.BOSS_ENCOUNTER,
            InterpretedLifeEventKind.BETRAYAL: TurningPointKind.BETRAYAL,
            InterpretedLifeEventKind.FIRST_KILL: TurningPointKind.FIRST_KILL,
        }
        return mapping.get(event_kind, TurningPointKind.NEAR_DEATH) # Default to near death if unknown
