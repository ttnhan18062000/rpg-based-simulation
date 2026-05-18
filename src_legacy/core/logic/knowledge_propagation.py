"""Knowledge Propagation Service — handles the systemic spread of social information. [PHASE 2]

This service manages how entities share beliefs, rumors, and reputations with 
one another, enabling emergent social phenomena like gossip and collective memory.
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING, List, Dict

from src_legacy.ai.beliefs import BeliefService

if TYPE_CHECKING:
    from src_legacy.core.entities.entity import Entity
    from src_legacy.core.models.world_state import WorldState
    from src_legacy.actions.base import PerceptionUpdate

logger = logging.getLogger(__name__)

class KnowledgePropagationService:
    """Service for orchestrating the flow of information between entities."""

    @staticmethod
    def propagate_gossip(
        sharer: Entity, 
        recipient: Entity, 
        world: WorldState
    ) -> tuple[PerceptionUpdate | None, StrategicUpdate | None]:
        """Shares high-salience beliefs and strategic leads from sharer to recipient.
        
        AOA: Returns updates for the recipient. 
        """
        from src_legacy.actions.base import PerceptionUpdate, StrategicUpdate
        
        perception_up = None
        strategic_up = None

        # 1. Share entity beliefs (Existing)
        sharer_memory = sharer.mind.perception.entity_memory
        if sharer_memory:
            potential_targets = sorted(
                sharer_memory.keys(),
                key=lambda eid: sharer_memory[eid].confidence * sharer_memory[eid].directness,
                reverse=True
            )[:5]
            
            p_updates = {}
            for target_id in potential_targets:
                if target_id == recipient.id:
                    continue
                
                belief = sharer_memory[target_id]
                dist = sharer.spatial.pos.manhattan(belief.pos)
                if dist > 50:
                    is_hero = belief.apparent_role == "hero"
                    is_boss = belief.apparent_role == "world_boss"
                    if not (is_hero or is_boss):
                        continue

                indirect_belief = BeliefService.share_knowledge(sharer, recipient, target_id, world.tick)
                if indirect_belief:
                    p_updates[target_id] = indirect_belief
                    if len(p_updates) >= 3:
                         break
            
            if p_updates:
                perception_up = PerceptionUpdate(target_id=recipient.id, entity_memory=p_updates)

        # 2. Share Strategic Leads (Phase 3)
        sharer_leads = sharer.mind.strategic.leads
        if sharer_leads:
            # Pick a lead to share if it matches the recipient's need or is generally interesting
            # (Heuristic: Share the highest confidence lead that isn't exhausted)
            potential_leads = sorted(
                [l for l in sharer_leads if not l.is_exhausted],
                key=lambda l: l.certainty,
                reverse=True
            )
            
            if potential_leads:
                lead_to_share = potential_leads[0]
                # Filter leads already known by recipient
                existing = next((l for l in recipient.mind.strategic.leads if l.label == lead_to_share.label), None)
                if not existing or (lead_to_share.certainty > existing.certainty):
                    # [phase_3_task_6] Rumor Degradation
                    # Create an indirect copy with reduced confidence and directness
                    new_lead = lead_to_share.model_copy(update={
                        "source_type": "gossip",
                        "source_entity_id": sharer.id,
                        "directness": lead_to_share.directness * 0.8,
                        "certainty": lead_to_share.certainty * 0.9,
                        "freshness_tick": world.tick
                    })
                    
                    # Recipient's trust in sharer affects initial source_confidence
                    sharer_belief = recipient.mind.perception.entity_memory.get(sharer.id)
                    if sharer_belief:
                        # If known, use recipient's subjective trust in sharer
                        new_lead.source_confidence = sharer_belief.apparent_trustworthiness
                    
                    strategic_up = StrategicUpdate(
                        target_id=recipient.id,
                        leads_add_or_update=[new_lead]
                    )

        return perception_up, strategic_up

    @staticmethod
    def sync_faction_standing(
        entity: Entity, 
        faction_rep: Dict[str, float],
        world: WorldState
    ) -> None:
        """Broadcasts faction-level changes to a set of entities (e.g. at a Guild Hall)."""
        # Placeholder for Stage 4 expansion
        pass
