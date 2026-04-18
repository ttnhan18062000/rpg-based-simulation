"""Authoritative spatial and timing rulebook for the simulation.

[Milestone 1] Freeze the laws of space and time.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from src.core.models.vectors import Vector2

if TYPE_CHECKING:
    from src.core.models.world_state import WorldState
    from src.core.models.snapshot import Snapshot

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
    def check_targeting_legality(origin: Vector2, target: Vector2, weapon_range: int, world: WorldState | Snapshot, requires_los: bool = True) -> bool:
        """Centralized targeting check (Range + Optional LOS). [Milestone 1]"""
        success, _ = LegalityService.verify_targeting_legality(origin, target, weapon_range, world, requires_los)
        return success

    @staticmethod
    def verify_targeting_legality(origin: Vector2, target: Vector2, weapon_range: int, world: WorldState | Snapshot, requires_los: bool = True) -> tuple[bool, ActionReason | None]:
        """Authoritative targeting verification with structured reason. [Milestone 7]"""
        from src.core.models.reason_codes import ActionReason, ReasonCode
        
        # 1. Range check
        dist = origin.manhattan(target)
        if dist > weapon_range:
            return False, ActionReason(code=ReasonCode.OUT_OF_RANGE, metadata={"max_range": weapon_range, "actual_dist": dist}, is_rejection=True)
        
        # 2. LOS check (skip if adjacent or not required)
        if requires_los and weapon_range > 1 and not LegalityService.is_adjacent(origin, target):
            if not world.grid.has_line_of_sight(origin.x, origin.y, target.x, target.y):
                return False, ActionReason(code=ReasonCode.PATH_NOT_FOUND, metadata={"detail": "No Line of Sight"}, is_rejection=True)
                
        return True, None

    @staticmethod
    def check_occupancy(pos: Vector2, world: WorldState | Snapshot, ignore_entity_id: int | None = None) -> bool:
        """Verify if a tile is legally enterable."""
        success, _ = LegalityService.verify_occupancy(pos, world, ignore_entity_id)
        return success

    @staticmethod
    def verify_occupancy(pos: Vector2, world: WorldState | Snapshot, ignore_entity_id: int | None = None) -> tuple[bool, ActionReason | None]:
        """Authoritative occupancy verification with structured reason. [Milestone 7]"""
        from src.core.models.reason_codes import ActionReason, ReasonCode
        
        # [Milestone 1] Rule: 1 entity per tile. No pass-through.
        entity_id = world.get_entity_at(pos)
        if entity_id is not None:
             if ignore_entity_id is not None and entity_id == ignore_entity_id:
                  return True, None
             
             return False, ActionReason(code=ReasonCode.OCCUPANCY_VIOLATION, metadata={"occupant_id": entity_id}, is_rejection=True)
        
        return True, None

    @staticmethod
    def get_occupant_id(pos: Vector2, world: WorldState | Snapshot) -> int | None:
        """Authoritative occupant lookup. [Milestone 1]"""
        return world.get_entity_at(pos)

    @staticmethod
    def check_aoe_legality(origin: Vector2, impact: Vector2, range: int, world: WorldState | Snapshot) -> bool:
        """Verify if an AoE impact point is legal (range + LOS)."""
        # 1. Range check to impact center
        if origin.manhattan(impact) > range:
            return False
        
        # 2. LOS check to impact center
        if not world.grid.has_line_of_sight(origin.x, origin.y, impact.x, impact.y):
            return False
            
        return True

    @staticmethod
    def get_affected_by_aoe(impact: Vector2, radius: int, world: WorldState | Snapshot) -> list[int]:
        """Return list of entity IDs within Manhattan radius of impact."""
        # Use spatial index to find nearby candidates
        if hasattr(world, "entities_at_radius"):
             candidates = world.entities_at_radius(impact, radius)
        else:
             # Snapshot uses nearby_entity_ids
             ids = world.nearby_entity_ids(impact.x, impact.y, radius)
             candidates = [world.entities[eid] for eid in ids if eid in world.entities]
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

    @staticmethod
    def check_high_ground(attacker_pos: Vector2, defender_pos: Vector2, world: WorldState | Snapshot) -> bool:
        """Verify if attacker has clear elevation advantage (Terrain-based). [Milestone 2]"""
        from src.core.models.enums import Material
        attacker_tile = world.grid.get(attacker_pos)
        defender_tile = world.grid.get(defender_pos)
        
        # Binary High Ground: MOUNTAIN (9) vs anything else.
        return attacker_tile == Material.MOUNTAIN and defender_tile != Material.MOUNTAIN

    @staticmethod
    def check_flanking(defender_id: int, world: WorldState | Snapshot) -> bool:
        """Authoritative geometric flanking check. [Milestone 2]
        
        Criteria: At least two enemies must be on opposite cardinal sides (N/S or E/W).
        """
        defender = world.entities.get(defender_id)
        if not defender or not defender.combat.alive:
            return False
            
        pos = defender.spatial.pos
        north = world.get_entity_at(pos + Vector2(0, -1))
        south = world.get_entity_at(pos + Vector2(0, 1))
        east = world.get_entity_at(pos + Vector2(1, 0))
        west = world.get_entity_at(pos + Vector2(-1, 0))
        
        def is_hostile(eid: int | None) -> bool:
            if eid is None: return False
            ent = world.entities.get(eid)
            if not ent or not ent.combat.alive: return False
            # Basic faction check
            return ent.identity.faction != defender.identity.faction

        # Check opposites: (North & South) OR (East & West)
        has_ns = is_hostile(north) and is_hostile(south)
        has_ew = is_hostile(east) and is_hostile(west)
        
        return has_ns or has_ew

    @staticmethod
    def check_cover(attacker_pos: Vector2, defender_pos: Vector2, world: WorldState | Snapshot) -> bool:
        """Verify if defender is behind wall cover relative to attacker. [Milestone 2]
        
        Constraint: Apply only against ranged attacks (dist > 1).
        """
        if attacker_pos.manhattan(defender_pos) <= 1:
            return False
            
        dx = defender_pos.x - attacker_pos.x
        dy = defender_pos.y - attacker_pos.y
        
        from src.core.models.enums import Material
        
        # Check adjacent wall between them
        # Simplified: if attacker is mainly West, check West of defender.
        if abs(dx) > abs(dy):
            # Horizontal bias
            check_x = defender_pos.x - (1 if dx > 0 else -1)
            if world.grid.get_xy(check_x, defender_pos.y) == Material.WALL:
                return True
        else:
            # Vertical bias
            check_y = defender_pos.y - (1 if dy > 0 else -1)
            if world.grid.get_xy(defender_pos.x, check_y) == Material.WALL:
                return True
                
        return False
