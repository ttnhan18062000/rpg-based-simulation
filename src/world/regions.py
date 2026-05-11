# Compliance IDs: SUB-275, SUB-276, SUB-277, SUB-278, SUB-279, WORLD-038, WORLD-041, WORLD-043, WORLD-052, WORLD-053, WORLD-054, WORLD-055, WORLD-056, WORLD-057, WORLD-058, WORLD-059
from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from src.core.state import RegionState
from src.world.spawn_config import DIFFICULTY_ZONES

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState

class RegionService:
    """
    Authoritative service for regional topology and point-of-interest logic.
    """

    @staticmethod
    def find_region_at(state: AuthoritativeState, pos: tuple[float, float]) -> Optional[RegionState]:
        """
        Finds the region containing the given position. 
        Uses bounds if defined, otherwise falls back to nearest region center.
        """
        if not state.regions:
            return None

        # 1. Try exact bounds match
        px, py = pos
        for region in state.regions.values():
            xmin, ymin, xmax, ymax = region.bounds
            if xmin <= px <= xmax and ymin <= py <= ymax:
                return region

        # 2. Fallback: Nearest region center (Voronoi-like)
        best_region = None
        min_dist_sq = float('inf')
        
        for region in state.regions.values():
            cx, cy = region.center
            dist_sq = (cx - px)**2 + (cy - py)**2
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                best_region = region
                
        return best_region

    @staticmethod
    def get_difficulty_tier_at(pos: tuple[float, float], town_center: tuple[float, float] = (0, 0)) -> int:
        """
        Calculates difficulty tier based on distance from town center.
        """
        dx = pos[0] - town_center[0]
        dy = pos[1] - town_center[1]
        dist = (dx**2 + dy**2)**0.5
        
        for threshold, tier in DIFFICULTY_ZONES:
            if dist <= threshold:
                return tier
        return 4 # Max tier fallback
