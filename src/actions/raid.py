"""RAID AI logic for faction aggression and building sabotage."""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from src.actions.base import ActionProposal
from src.core.enums import ActionType, AIState, EntityRole

if TYPE_CHECKING:
    from src.core.world_state import WorldState
    from src.core.models import Entity

logger = logging.getLogger(__name__)

class RaidAI:
    """Specialized AI for faction raids targeting the town."""

    @staticmethod
    def propose(entity: Entity, world: WorldState) -> ActionProposal | None:
        """Propose a raid-related action (attack building or hero)."""
        # 1. Target heroes first if very close
        targets = world.spatial_index.query_radius(entity.pos, radius=5)
        heroes = [world.entities[tid] for tid in targets 
                  if tid in world.entities and world.entities[tid].role == EntityRole.HERO]
        
        if heroes:
            # Target closest hero
            heroes.sort(key=lambda h: h.pos.manhattan(entity.pos))
            target_h = heroes[0]
            if entity.pos.manhattan(target_h.pos) <= 1:
                return ActionProposal(entity.id, ActionType.ATTACK, target=target_h.id, reason="Raid: Attack hero")
            else:
                return ActionProposal(entity.id, ActionType.MOVE, target=target_h.pos, reason="Raid: Move to hero")

        # 2. If no heroes near, target buildings
        if world.buildings:
            functional = [b for b in world.buildings if b.is_functional]
            if functional:
                functional.sort(key=lambda b: b.pos.manhattan(entity.pos))
                target_b = functional[0]
                
                if entity.pos.manhattan(target_b.pos) <= 1:
                    return ActionProposal(entity.id, ActionType.ATTACK, target=f"BUILDING:{target_b.building_id}", reason="Raid: Sabotage building")
                else:
                    return ActionProposal(entity.id, ActionType.MOVE, target=target_b.pos, reason="Raid: Move to building")

        return None
