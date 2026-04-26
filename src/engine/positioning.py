from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional, Tuple
from src.engine.legality import LegalityServiceV2

if TYPE_CHECKING:
    from src.core.state import EntityState, AuthoritativeState

class PositioningService:
    """
    Tactical spatial analysis for V2 engine.
    Implements cover-seeking, chokepoint identification, and bracketing.
    """

    @staticmethod
    def find_nearest_cover(
        entity: EntityState, 
        threat: EntityState, 
        state: AuthoritativeState,
        max_dist: int = 5
    ) -> Optional[Tuple[float, float]]:
        """
        Finds the nearest walkable tile that has NO line of sight to the threat.
        Used by Skirmishers or low-HP entities when facing ranged threats.
        """
        start_x, start_y = int(entity.position[0]), int(entity.position[1])
        best_tile = None
        min_dist = float('inf')

        for dx in range(-max_dist, max_dist + 1):
            for dy in range(-max_dist, max_dist + 1):
                tx, ty = start_x + dx, start_y + dy
                dist = abs(dx) + abs(dy)
                if dist > max_dist or dist == 0:
                    continue
                
                # 1. Walkable check
                is_walkable, _ = LegalityServiceV2.verify_occupancy((tx, ty), state, ignore_entity_id=entity.id)
                if not is_walkable:
                    continue

                # 2. Cover check: No LoS to threat
                if not LegalityServiceV2.has_line_of_sight((tx, ty), threat.position, state):
                    if dist < min_dist:
                        min_dist = dist
                        best_tile = (float(tx), float(ty))

        return best_tile

    @staticmethod
    def identify_chokepoints(
        entity: EntityState, 
        state: AuthoritativeState,
        radius: int = 8
    ) -> List[Tuple[float, float]]:
        """
        Identifies 'chokepoints' (1-tile gaps between walls) within a radius.
        """
        center_x, center_y = int(entity.position[0]), int(entity.position[1])
        chokepoints = []

        terrain = getattr(state, 'terrain', {})

        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                tx, ty = center_x + dx, center_y + dy
                
                # Only check walkable tiles
                if terrain.get((tx, ty)) == "WALL":
                    continue

                # Check for 1-tile gap (horizontal or vertical)
                # Vertical gap: Wall at (tx-1, ty) and (tx+1, ty)
                if terrain.get((tx - 1, ty)) == "WALL" and terrain.get((tx + 1, ty)) == "WALL":
                    chokepoints.append((float(tx), float(ty)))
                    continue

                # Horizontal gap: Wall at (tx, ty-1) and (tx, ty+1)
                if terrain.get((tx, ty - 1)) == "WALL" and terrain.get((tx, ty + 1)) == "WALL":
                    chokepoints.append((float(tx), float(ty)))

        return chokepoints

    @staticmethod
    def get_bracketing_position(
        entity: EntityState, 
        ally: EntityState, 
        target: EntityState
    ) -> Tuple[float, float]:
        """
        Calculates a position to 'bracket' the target (opposite side from the ally).
        Formula: target_pos + (target_pos - ally_pos)
        """
        tx, ty = target.position
        ax, ay = ally.position
        
        # Direction from ally to target
        dx = tx - ax
        dy = ty - ay
        
        # Target position + that direction
        # Limit to 1 tile away from target
        mag = (dx*dx + dy*dy)**0.5
        if mag > 0:
            ux, uy = dx/mag, dy/mag
            return (tx + round(ux), ty + round(uy))
        
        return (tx + 1, ty) # Fallback
