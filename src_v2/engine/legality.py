# src_v2/engine/legality.py
from __future__ import annotations
from typing import TYPE_CHECKING, Tuple, Optional, Any

if TYPE_CHECKING:
    from src_v2.core.state import AuthoritativeState, EntityState

class LegalityServiceV2:
    """ Authoritative simulation laws for V2. """

    @staticmethod
    def get_manhattan_dist(a: Tuple[float, float], b: Tuple[float, float]) -> int:
        return int(abs(a[0] - b[0]) + abs(a[1] - b[1]))

    @staticmethod
    def is_adjacent(a: Tuple[float, float], b: Tuple[float, float]) -> bool:
        return LegalityServiceV2.get_manhattan_dist(a, b) == 1

    @staticmethod
    def verify_occupancy(
        pos: Tuple[float, float], 
        state_or_context: Any, 
        ignore_entity_id: Optional[int] = None
    ) -> Tuple[bool, str]:
        """
        V2 Authoritative Occupancy Rule:
        Enforces Static Terrain (WALL), Buildings, and Dynamic Entities.
        """
        target_grid_pos = (int(pos[0]), int(pos[1]))
        
        # 1. Static Terrain (WALL)
        terrain = getattr(state_or_context, 'terrain', {})
        if terrain.get(target_grid_pos) == "WALL":
            return False, "PATH_NOT_FOUND"

        # 2. Buildings (Solid structures)
        buildings = getattr(state_or_context, 'buildings', {})
        if buildings:
            # If buildings is a dict {id: BuildingState}
            for b in buildings.values():
                if (int(b.position[0]), int(b.position[1])) == target_grid_pos:
                    return False, "BUILDING_OBSTRUCTION"

        # 3. Dynamic Claims (Position claimed this tick)
        claims = getattr(state_or_context, 'transient_claims', [])
        if target_grid_pos in claims:
            return False, "OCCUPANCY_VIOLATION"

        # 4. Dynamic Entities
        entities = getattr(state_or_context, 'entities', None)
        if entities is None:
            entities_list = getattr(state_or_context, 'neighbor_view', [])
            for eid, entity in entities_list:
                if eid == ignore_entity_id: continue
                if not entity.active: continue
                if (int(entity.position[0]), int(entity.position[1])) == target_grid_pos:
                    return False, "OCCUPANCY_VIOLATION"
        else:
            for eid, entity in entities.items():
                if eid == ignore_entity_id: continue
                if not entity.active: continue
                if (int(entity.position[0]), int(entity.position[1])) == target_grid_pos:
                    return False, "OCCUPANCY_VIOLATION"

        return True, "ADVANCING"

    @staticmethod
    def get_engaged_hostiles(
        actor: EntityState,
        state_or_context: Any
    ) -> list[int]:
        """
        Returns a list of hostile entity IDs adjacent to the actor.
        AOA Stabilization: Engagement is bit-identical to adjacency in V2.
        """
        engaged = []
        entities = getattr(state_or_context, 'entities', None)
        if entities is None:
            # Try neighbor_view (WorkerPacket)
            entities_list = getattr(state_or_context, 'neighbor_view', [])
            for eid, entity in entities_list:
                if eid == actor.id: continue
                if not entity.active: continue
                if entity.identity.faction != actor.identity.faction:
                    if LegalityServiceV2.is_adjacent(actor.position, entity.position):
                        engaged.append(eid)
        else:
            # Handle Dictionary (AuthoritativeState)
            for eid, entity in entities.items():
                if eid == actor.id: continue
                if not entity.active: continue
                if entity.identity.faction != actor.identity.faction:
                    if LegalityServiceV2.is_adjacent(actor.position, entity.position):
                        engaged.append(eid)
        return engaged

    @staticmethod
    def verify_attack_legality(
        attacker: EntityState,
        target: EntityState,
        state_or_context: Any
    ) -> Tuple[bool, str]:
        """
        Authoritative validation for a combat interaction.
        """
        # 1. State Validity
        if not attacker.active or not attacker.combat.alive:
            return False, "ATTACKER_INCAPACITATED"
        if not target.active or not target.combat.alive:
            return False, "TARGET_INCAPACITATED"
        if attacker.id == target.id:
            return False, "SELF_ATTACK_ILLEGAL"

        # 2. Faction Validity
        if attacker.identity.faction == target.identity.faction:
            return False, "FRIENDLY_FIRE_ILLEGAL"

        # 3. Range Validity
        dist = LegalityServiceV2.get_manhattan_dist(attacker.position, target.position)
        if dist > attacker.combat.range:
            return False, "OUT_OF_RANGE"

        # 4. LoS / Obstruction
        if not LegalityServiceV2.has_line_of_sight(attacker.position, target.position, state_or_context):
            return False, "LOS_OBSTRUCTED"

        return True, "LEGAL"

    @staticmethod
    def has_line_of_sight(
        a: Tuple[float, float], 
        b: Tuple[float, float], 
        state_or_context: Any
    ) -> bool:
        """
        Simple Bresenham-like LoS check for WALL/Building obstructions.
        """
        x0, y0 = int(a[0]), int(a[1])
        x1, y1 = int(b[0]), int(b[1])
        
        terrain = getattr(state_or_context, 'terrain', {})
        buildings = getattr(state_or_context, 'buildings', {})
        
        # Manhattan path check (simpler for tile-based RPG)
        # We check all tiles between A and B
        dx = x1 - x0
        dy = y1 - y0
        step_x = 1 if dx > 0 else -1 if dx < 0 else 0
        step_y = 1 if dy > 0 else -1 if dy < 0 else 0
        
        curr_x, curr_y = x0, y0
        
        # Check X steps
        while curr_x != x1:
            curr_x += step_x
            if (curr_x, curr_y) == (x1, y1): break
            if terrain.get((curr_x, curr_y)) == "WALL": return False
            for build in buildings.values():
                if (int(build.position[0]), int(build.position[1])) == (curr_x, curr_y): return False
                
        # Check Y steps
        curr_x = x1
        while curr_y != y1:
            curr_y += step_y
            if (curr_x, curr_y) == (x1, y1): break
            if terrain.get((curr_x, curr_y)) == "WALL": return False
            for build in buildings.values():
                if (int(build.position[0]), int(build.position[1])) == (curr_x, curr_y): return False
                
        return True
