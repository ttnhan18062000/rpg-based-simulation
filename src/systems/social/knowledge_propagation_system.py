"""KnowledgePropagationSystem orchestrates the sharing of information between entities. [PHASE 2]

This system manages how rumors and knowledge spread through the world, ensuring
that social consequences ripple through the population.
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING, List

from src.systems.infrastructure.base import System, SystemContext
from src.core.models.enums import Domain
from src.core.logic.knowledge_propagation import KnowledgePropagationService

if TYPE_CHECKING:
    from src.core.entities.entity import Entity

logger = logging.getLogger(__name__)

class KnowledgePropagationSystem(System):
    """System for orchestrated belief sharing in the tick loop."""

    def on_tick(self, ctx: SystemContext, tick: int) -> None:
        """Process periodic gossip/knowledge sharing between nearby entities."""
        # 1. Throttling: Knowledge propagation is expensive and doesn't need to happen every tick.
        # Propagation happens every 5 ticks.
        if tick % 5 != 0:
            return
            
        world = ctx.world
        entities = [e for e in world.entities.values() if e.combat.alive and e.kind != "generator"]
        
        # 2. Identify potential sharing pairs (nearby allies)
        for sharer in entities:
            # Random chance to share if not busy
            if ctx.rng.next_bool(Domain.SOCIAL, sharer.id, tick, 0.3): # ~30% chance to attempt sharing
                continue
                
            # Get nearby entities in vision range
            neighbors = world.entities_at_radius(sharer.spatial.pos, sharer.spatial.vision_range)
            for recipient in neighbors:
                if recipient.id == sharer.id or not recipient.combat.alive:
                    continue
                    
                # Only share with allies/neutrals (to start with)
                if not ctx.faction_reg.is_hostile(sharer.identity.faction, recipient.identity.faction):
                    # Attempt propagation
                    update = KnowledgePropagationService.propagate_gossip(sharer, recipient, world)
                    if update:
                        # Authoritative application via ActionSystem shim or direct update
                        # Since this is a system running in the tick loop, we apply directly to the recipient's mind update queue or similar.
                        # In this architecture, systems usually push updates to the context.
                        # ctx.emit("social", f"{sharer.display_name} shared rumors with {recipient.display_name}", (sharer.id, recipient.id))
                        
                        # Apply to memory (Authoritative transition)
                        for eid, belief in update.entity_memory.items():
                            from src.ai.beliefs import BeliefService
                            BeliefService.merge_indirect_belief(recipient, belief)
                            
                        # Log for visualization
                        if ctx.emit:
                             ctx.emit("social", f"{sharer.identity.display_name} shared knowledge with {recipient.identity.display_name}", (sharer.id, recipient.id))

