"""Knowledge Propagation Service — handles the systemic spread of social information. [PHASE 2]

This service manages how entities share beliefs, rumors, and reputations with 
one another, enabling emergent social phenomena like gossip and collective memory.
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING, List, Dict

from src.ai.beliefs import BeliefService

if TYPE_CHECKING:
    from src.core.entities.entity import Entity
    from src.core.models.world_state import WorldState
    from src.actions.base import PerceptionUpdate

logger = logging.getLogger(__name__)

class KnowledgePropagationService:
    """Service for orchestrating the flow of information between entities."""

    @staticmethod
    def propagate_gossip(
        sharer: Entity, 
        recipient: Entity, 
        world: WorldState
    ) -> PerceptionUpdate | None:
        """Shares high-salience beliefs from sharer to recipient.
        
        AOA: Returns a PerceptionUpdate for the recipient. 
        Higher trust between sharer/recipient increases the confidence of shared info.
        """
        from src.actions.base import PerceptionUpdate
        
        # 1. Identify high-salience targets in sharer's memory
        # Salience based on fame, threat, or personal bond importance
        sharer_memory = sharer.mind.perception.entity_memory
        if not sharer_memory:
            return None
            
        # Select top 3 most salient/recent beliefs to share
        targets_to_share = sorted(
            sharer_memory.keys(),
            key=lambda eid: sharer_memory[eid].confidence * sharer_memory[eid].directness,
            reverse=True
        )[:3]
        
        updates = {}
        for target_id in targets_to_share:
            # Don't share info about the recipient with the recipient
            if target_id == recipient.id:
                continue
                
            indirect_belief = BeliefService.share_knowledge(sharer, recipient, target_id, world.tick)
            if indirect_belief:
                updates[target_id] = indirect_belief
                
        if not updates:
            return None
            
        return PerceptionUpdate(target_id=recipient.id, entity_memory=updates)

    @staticmethod
    def sync_faction_standing(
        entity: Entity, 
        faction_rep: Dict[str, float],
        world: WorldState
    ) -> None:
        """Broadcasts faction-level changes to a set of entities (e.g. at a Guild Hall)."""
        # Placeholder for Stage 4 expansion
        pass
