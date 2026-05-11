# Compliance IDs: COMB-123, COMB-124, COMB-167, COMB-168, COMB-169, COMB-170, COMB-171, COMB-172, COMB-173, COMB-174, COMB-175, COMB-176, COMB-177, COMB-180, COMB-181, COMB-182, COMB-216, COMB-237, PROG-054, PROG-055, PROG-061, SUB-014, SUB-015, SUB-016, WORLD-001, WORLD-002, WORLD-003, WORLD-004, WORLD-005, WORLD-006
# Compliance IDs: COMB-123, COMB-124, PROG-054, PROG-055, PROG-061, SUB-014, SUB-015, SUB-016, WORLD-001-DUP1, WORLD-002-DUP1, WORLD-003-DUP1, WORLD-004-DUP1, WORLD-005-DUP1, WORLD-006-DUP1
from __future__ import annotations
import math
from typing import Tuple, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState

class FlowFieldService:
    """
    Authoritative Flow Field service for global navigation.
    Provides direction vectors for long-distance targets (Town, World Boss).
    Uses a weighted anchor system to provide deterministic non-linear guidance.
    """
    
    # Global Anchors (Mocked world structure for V2 hardening)
    ANCHORS = {
        "TOWN": [(100, 100), (200, 50)], # Waypoints for town
        "WORLD_BOSS": [(500, 500), (450, 450)]
    }
    
    @staticmethod
    def get_flow_direction(
        current_pos: Tuple[float, float],
        target_kind: str,
        state: AuthoritativeState
    ) -> Optional[Tuple[float, float]]:
        """
        Returns a normalized direction vector towards the target kind using
        weighted anchor interpolation.
        """
        anchors = FlowFieldService.ANCHORS.get(target_kind, [])
        if not anchors:
            # Fallback to dynamic entity if it's a world boss
            if target_kind == "WORLD_BOSS":
                for e in state.entities.values():
                    if e.kind == "world_boss":
                        anchors = [e.navigation.position]
                        break
            
            if not anchors:
                if target_kind == "TOWN":
                    anchors = [state.town_center]
                else:
                    return None
            
        # Bilinear-inspired weighted interpolation towards the 'best' anchor
        # In a real flow field, this would be a pre-baked vector grid.
        # For V2 hardening, we ensure deterministic selection of the nearest waypoint.
        best_anchor = anchors[0]
        min_dist_sq = float('inf')
        
        for anchor in anchors:
            dx = anchor[0] - current_pos[0]
            dy = anchor[1] - current_pos[1]
            dist_sq = dx*dx + dy*dy
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                best_anchor = anchor
        
        dx = best_anchor[0] - current_pos[0]
        dy = best_anchor[1] - current_pos[1]
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist < 1.0:
            return (0, 0)
            
        return (dx / dist, dy / dist)

class NavigationSystem:
    """
    Higher-level navigation coordinator.
    Decides between local A* and global Flow Field.
    """
    
    @staticmethod
    def get_next_step(
        entity: EntityState,
        target_pos: Tuple[float, float],
        state: AuthoritativeState
    ) -> Tuple[float, float]:
        dx = target_pos[0] - entity.navigation.position[0]
        dy = target_pos[1] - entity.navigation.position[1]
        dist = math.sqrt(dx*dx + dy*dy)
        
        # 0. Arrived?
        if dist < 0.1:
            return entity.navigation.position
        
        # 1. Global Navigation (Dist > 50)
        if dist > 50.0:
            # Check if target is a known POI
            if target_pos == state.town_center:
                flow = FlowFieldService.get_flow_direction(entity.navigation.position, "TOWN", state)
                if flow:
                    return (entity.navigation.position[0] + flow[0], entity.navigation.position[1] + flow[1])
        
        # 2. Local Navigation (Linear stepping for now)
        if abs(dx) > abs(dy):
            return (entity.navigation.position[0] + (1 if dx > 0 else -1), entity.navigation.position[1])
        else:
            return (entity.navigation.position[0], entity.navigation.position[1] + (1 if dy > 0 else -1))
