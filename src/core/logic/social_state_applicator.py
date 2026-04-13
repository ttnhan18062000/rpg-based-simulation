"""Social State Applicator — orchestrates the application of interpreted social events. [PHASE 2]

This service is the hub for Stage 4 implementation. It takes InterpretedLifeEvents
and routes them to TurningPointService, RelationshipService, and ReputationService.
It ensures that semantic interpretations actually change the simulation state.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List, Optional

from src.core.logic.turning_points import TurningPointService
from src.core.logic.relationship_service import RelationshipService
from src.core.logic.reputation_service import ReputationService
from src.core.models.life_events import TurningPointRecord
from src.core.models.enums import TurningPointKind
from src.core.logic.strategic_consequence_service import StrategicConsequenceService

if TYPE_CHECKING:
    from src.core.entities.entity import Entity
    from src.core.models.world_state import WorldState
    from src.core.models.life_events import InterpretedLifeEvent
    from src.actions.base import SocialUpdate, ReputationUpdate, IntentUpdate
    from src.systems.rng import DeterministicRNG

logger = logging.getLogger(__name__)

class SocialStateApplicator:
    """Orchestrates social state updates from interpreted events. [PHASE 1 REFACTOR]
    
    AOA Pillar 2: Pure interpretation and intent emission.
    """

    @classmethod
    def apply_interpreted_event(
        cls, 
        event: InterpretedLifeEvent, 
        world: WorldState,
        rng: DeterministicRNG | None = None
    ) -> list[IntentUpdate]:
        """Apply an interpreted event by generating intent updates.
        
        AOA Pillar 2: Services return intent. No direct mutations allowed here.
        """
        updates: list[IntentUpdate] = []
        tick = world.tick
        actor = world.get_entity(event.actor_id)
        if not actor:
            return []

        # 1. Handle Turning Point Candidates (Functional prepare)
        if event.turning_point_candidate:
            tp_record = TurningPointRecord(
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
                salience_score=0.0 
            )
            tp_up = TurningPointService.prepare_insertion(actor, tp_record, tick, rng)
            if tp_up:
                updates.append(tp_up)

        # 2. Apply Reputation Deltas (Refactor to emit ReputationUpdate)
        if event.reputation_deltas:
            from src.actions.base import ReputationUpdate
            # Mapping keys to ReputationUpdate fields
            rep_data = {}
            for k, v in event.reputation_deltas.items():
                field_name = k.replace('_score', '') + '_delta'
                if field_name == 'notoriety_delta': field_name = 'threat_notoriety_delta'
                rep_data[field_name] = v
            
            updates.append(ReputationUpdate(
                target_id=event.actor_id, # The one whose reputation is changing
                tags_add=event.tags_add,
                tags_remove=event.tags_remove,
                **rep_data
            ))

        # 3. Apply Relationship Deltas (Refactor to emit SocialUpdate)
        for subject_id, deltas in event.relationship_deltas.items():
            from src.actions.base import SocialUpdate
            social_data = {f"{k}_delta": v for k, v in deltas.items()}
            
            updates.append(SocialUpdate(
                source_id=event.actor_id, # The perceiver (The one who experiences the event)
                target_id=subject_id,    # The perceived (The one the sentiment is about)
                **social_data
            ))

        # 4. Chain to StrategicConsequenceService [PHASE 5]
        # We find the TurningPointRecord if it was created
        tp_up = next((u for u in updates if hasattr(u, 'turning_points_add') and u.turning_points_add), None)
        tp_record = tp_up.turning_points_add[0] if tp_up else None
        
        strat_up = StrategicConsequenceService.process_consequences(world, actor, event, tp_record, rng)
        if strat_up:
            updates.append(strat_up)

        return updates

    @staticmethod
    def _map_event_to_tp_kind(event_kind: int) -> TurningPointKind:
        """Internal mapping from interpretation kind to durable turning point kind."""
        from src.core.models.enums import InterpretedLifeEventKind
        
        mapping = {
            InterpretedLifeEventKind.NEAR_DEATH: TurningPointKind.NEAR_DEATH,
            InterpretedLifeEventKind.ALLY_DIED_NEARBY: TurningPointKind.ALLY_DIED,
            InterpretedLifeEventKind.AVENGED_ALLY: TurningPointKind.AVENGED_ALLY,
            InterpretedLifeEventKind.FIRST_BOSS_ENCOUNTER: TurningPointKind.BOSS_ENCOUNTER,
            InterpretedLifeEventKind.BETRAYAL: TurningPointKind.BETRAYAL,
            InterpretedLifeEventKind.FIRST_KILL: TurningPointKind.FIRST_KILL,
        }
        return mapping.get(event_kind, TurningPointKind.NEAR_DEATH)

