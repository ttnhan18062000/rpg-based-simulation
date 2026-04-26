"""RAID AI logic for faction aggression and building sabotage."""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from src_legacy.actions.base import ActionProposal
from src_legacy.core.models.enums import ActionType, AIState, EntityRole

if TYPE_CHECKING:
    from src_legacy.core.models.world_state import WorldState
    from src_legacy.core.entities.entity import Entity

logger = logging.getLogger(__name__)

class RaidAI:
    """Specialized AI for faction raids targeting the town."""

    @staticmethod
    def propose(entity: Entity, world: WorldState) -> ActionProposal | None:
        """Propose a raid-related action (attack building or hero)."""
        # 1. Target heroes first if very close
        targets = world.spatial_index.query_radius(entity.spatial.pos, radius=5)
        heroes = [world.entities[tid] for tid in targets 
                  if tid in world.entities and world.entities[tid].identity.role == EntityRole.HERO]
        
        if heroes:
            # Target closest hero
            heroes.sort(key=lambda h: h.spatial.pos.manhattan(entity.spatial.pos))
            target_h = heroes[0]
            if entity.spatial.pos.manhattan(target_h.spatial.pos) <= 1:
                return ActionProposal(entity.id, ActionType.ATTACK, target=target_h.id, reason="Raid: Attack hero")
            else:
                return ActionProposal(entity.id, ActionType.MOVE, target=target_h.spatial.pos, reason="Raid: Move to hero")

        # 2. If no heroes near, target buildings
        if world.buildings:
            functional = [b for b in world.buildings if b.is_functional]
            if functional:
                functional.sort(key=lambda b: b.spatial.pos.manhattan(entity.spatial.pos))
                target_b = functional[0]
                if entity.spatial.pos.manhattan(target_b.spatial.pos) <= 1:
                    from src_legacy.actions.base import BuildingTarget
                    return ActionProposal(entity.id, ActionType.ATTACK, target=BuildingTarget(building_id=target_b.building_id), reason="Raid: Sabotage building")
                else:
                    return ActionProposal(entity.id, ActionType.MOVE, target=target_b.spatial.pos, reason="Raid: Move to building")

        return None
