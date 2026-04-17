"""Authoritative spatial and timing rulebook for the simulation.

[Milestone 1] Freeze the laws of space and time.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from src.core.models.vectors import Vector2

if TYPE_CHECKING:
    from src.core.models.world_state import WorldState

logger = logging.getLogger(__name__)

class LegalityService:
    """The central authority for verifying simulation laws."""

    @staticmethod
    def get_distance(a: Vector2, b: Vector2) -> int:
        """Universal distance metric (Manhattan)."""
        return a.manhattan(b)

    @staticmethod
    def is_adjacent(a: Vector2, b: Vector2) -> bool:
        """Orthogonal adjacency check (dist == 1)."""
        return a.manhattan(b) == 1

    @staticmethod
    def check_range(origin: Vector2, target: Vector2, weapon_range: int) -> bool:
        """Verify if target is within reach using Manhattan metric."""
        return origin.manhattan(target) <= weapon_range

    @staticmethod
    def check_occupancy(pos: Vector2, world: WorldState, ignore_entity_id: int | None = None) -> bool:
        """Verify if a tile is legally enterable."""
        # [Milestone 1] Rule: 1 entity per tile. No pass-through.
        entity_id = world.get_entity_at(pos)
        if entity_id is not None:
             if ignore_entity_id is not None and entity_id == ignore_entity_id:
                  return True
             return False
        return True

    @staticmethod
    def check_aoe_legality(origin: Vector2, impact: Vector2, range: int, world: WorldState) -> bool:
        """Verify if an AoE impact point is legal (range + LOS)."""
        # 1. Range check to impact center
        if origin.manhattan(impact) > range:
            return False
        
        # 2. LOS check to impact center
        if not world.grid.has_line_of_sight(origin.x, origin.y, impact.x, impact.y):
            return False
            
        return True

    @staticmethod
    def get_affected_by_aoe(impact: Vector2, radius: int, world: WorldState) -> list[int]:
        """Return list of entity IDs within Manhattan radius of impact."""
        # Use spatial index to find nearby candidates
        candidates = world.entities_at_radius(impact, radius)
        affected: list[int] = []
        for entity in candidates:
            if entity.spatial.pos.manhattan(impact) <= radius:
                affected.append(entity.id)
        return affected
    @staticmethod
    def is_engaged(entity_id: int, world: WorldState) -> bool:
        """Centralized check if an entity is adjacent to a hostile."""
        from src.core.logic.combat_interaction_service import CombatInteractionService
        entity = world.entities.get(entity_id)
        if not entity or not entity.combat.alive:
            return False
        return CombatInteractionService.is_engaged(entity, world)
