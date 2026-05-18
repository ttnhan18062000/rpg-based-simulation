"""KnowledgePropagationSystem orchestrates the sharing of information between entities. [PHASE 2]

This system manages how rumors and knowledge spread through the world, ensuring
that social consequences ripple through the population.
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING, List

from src_legacy.systems.infrastructure.base import System, SystemContext
from src_legacy.core.models.enums import Domain
from src_legacy.core.logic.knowledge_propagation import KnowledgePropagationService

if TYPE_CHECKING:
    from src_legacy.core.entities.entity import Entity

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
            if not ctx.rng.next_bool(Domain.SOCIAL, sharer.id, tick, 0.4): # ~40% chance to attempt sharing
                continue
                
            # Get nearby entities in vision range
            neighbors = world.entities_at_radius(sharer.spatial.pos, sharer.spatial.vision_range)
            for recipient in neighbors:
                if recipient.id == sharer.id or not recipient.combat.alive:
                    continue
                    
                # Only share with allies/neutrals (to start with)
                if not ctx.faction_reg.is_hostile(sharer.identity.faction, recipient.identity.faction):
                    # Attempt propagation
                    p_update, s_update = KnowledgePropagationService.propagate_gossip(sharer, recipient, world)
                    
                    if p_update:
                        # Apply entity memory (Authoritative transition)
                        for eid, belief in p_update.entity_memory.items():
                            from src_legacy.ai.beliefs import BeliefService
                            up = BeliefService.merge_indirect_belief(recipient, belief)
                            if up and up.entity_memory:
                                recipient.mind.perception.entity_memory.update(up.entity_memory)
                            
                    if s_update:
                        # Apply strategic leads (Authoritative transition)
                        strat = recipient.mind.strategic
                        if s_update.leads_add_or_update:
                            for new_lead in s_update.leads_add_or_update:
                                # Merge lead
                                existing = next((l for l in strat.leads if l.label == new_lead.label), None)
                                if existing:
                                    # Update certainty if higher
                                    existing.certainty = max(existing.certainty, new_lead.certainty)
                                else:
                                    strat.leads.append(new_lead)
                        
                    if p_update or s_update:
                        # Log for visualization
                        if ctx.emit:
                             ctx.emit("social", f"{sharer.identity.display_name} shared knowledge with {recipient.identity.display_name}", (sharer.id, recipient.id))

