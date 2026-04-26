# src/engine/legality.py
from __future__ import annotations
from typing import TYPE_CHECKING, Tuple, Optional, Any

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState

class LegalityServiceV2:
    """ Authoritative simulation laws for V2. """

    @staticmethod
    def get_manhattan_dist(a: Tuple[float, float], b: Tuple[float, float]) -> int:
        return int(abs(a[0] - b[0]) + abs(a[1] - b[1]))

    @staticmethod
    def get_region_for_position(pos: Tuple[float, float], state: AuthoritativeState) -> Optional[RegionState]:
        """Returns the region containing the given position."""
        from src.core.state import RegionState
        for region in state.regions.values():
            x_min, y_min, x_max, y_max = region.bounds
            if x_min <= pos[0] <= x_max and y_min <= pos[1] <= y_max:
                return region
        return None

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
        
        # 1. Static Terrain (WALL / blocked_tiles)
        terrain = getattr(state_or_context, 'terrain', {})
        if terrain.get(target_grid_pos) == "WALL":
            return False, "PATH_NOT_FOUND"
            
        blocked_tiles = getattr(state_or_context, 'blocked_tiles', set())
        if target_grid_pos in blocked_tiles:
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
        engaged.sort()
        return engaged

    @staticmethod
    def verify_action_legality(
        actor: EntityState,
        action_kind: str,
        state: AuthoritativeState
    ) -> Tuple[bool, str]:
        """
        Phase 9: Regional Suppression.
        Checks if the current region suppresses specific actions.
        """
        region = LegalityServiceV2.get_region_for_position(actor.position, state)
        if region and region.suppression_active:
            # High-level suppression blocks disruptive/strategic actions
            if action_kind in ["SABOTAGE", "RECRUIT", "THEFT"]:
                 return False, "REGIONAL_SUPPRESSION"
        return True, "LEGAL"

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

    @staticmethod
    def verify_aoe_legality(
        attacker: EntityState,
        target_pos: Tuple[float, float],
        max_range: int,
        state_or_context: Any
    ) -> Tuple[bool, str]:
        """
        Authoritative validation for Area-of-Effect targeting.
        Impact center must be in range and visible.
        """
        dist = LegalityServiceV2.get_manhattan_dist(attacker.position, target_pos)
        if dist > max_range:
            return False, "OUT_OF_RANGE"
            
        if not LegalityServiceV2.has_line_of_sight(attacker.position, target_pos, state_or_context):
            return False, "LOS_OBSTRUCTED"
            
        return True, "LEGAL"

    @staticmethod
    def check_high_ground(attacker_pos: Tuple[float, float], defender_pos: Tuple[float, float], state: AuthoritativeState) -> bool:
        """Verify if attacker has clear elevation advantage (Terrain-based)."""
        atk_pos = (int(attacker_pos[0]), int(attacker_pos[1]))
        def_pos = (int(defender_pos[0]), int(defender_pos[1]))
        
        attacker_tile = state.terrain.get(atk_pos, "PLAIN")
        defender_tile = state.terrain.get(def_pos, "PLAIN")
        
        # Binary High Ground: HILL or MOUNTAIN vs anything else.
        high_ground_tiles = {"HILL", "MOUNTAIN"}
        return attacker_tile in high_ground_tiles and defender_tile not in high_ground_tiles

    @staticmethod
    def check_flanking(defender_id: int, state: AuthoritativeState) -> bool:
        """
        Authoritative geometric flanking check.
        Criteria: At least two enemies must be on opposite cardinal sides (N/S or E/W).
        """
        defender = state.entities.get(defender_id)
        if not defender or not defender.combat.alive:
            return False
            
        x, y = int(defender.position[0]), int(defender.position[1])
        
        # Helper to find if a hostile is at a position
        def has_hostile_at(pos: Tuple[int, int]) -> bool:
            for entity in state.entities.values():
                if not entity.active or not entity.combat.alive: continue
                if (int(entity.position[0]), int(entity.position[1])) == pos:
                    return entity.identity.faction != defender.identity.faction
            return False

        has_ns = has_hostile_at((x, y - 1)) and has_hostile_at((x, y + 1))
        has_ew = has_hostile_at((x - 1, y)) and has_hostile_at((x + 1, y))
        
        return has_ns or has_ew

    @staticmethod
    def check_cover(attacker_pos: Tuple[float, float], defender_pos: Tuple[float, float], state: AuthoritativeState) -> bool:
        """Verify if defender is behind wall cover relative to attacker."""
        if LegalityServiceV2.get_manhattan_dist(attacker_pos, defender_pos) <= 1:
            return False
            
        dx = defender_pos[0] - attacker_pos[0]
        dy = defender_pos[1] - attacker_pos[1]
        
        x, y = int(defender_pos[0]), int(defender_pos[1])
        
        # Check adjacent wall between them
        if abs(dx) > abs(dy):
            # Horizontal bias
            check_x = x - (1 if dx > 0 else -1)
            if state.terrain.get((check_x, y)) == "WALL":
                return True
        else:
            # Vertical bias
            check_y = y - (1 if dy > 0 else -1)
            if state.terrain.get((x, check_y)) == "WALL":
                return True
                
        return False
