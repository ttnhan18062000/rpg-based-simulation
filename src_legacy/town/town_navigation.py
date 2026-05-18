from __future__ import annotations
import math
from typing import Optional
from src_legacy.core.state import AuthoritativeState, EntityState, BuildingState

class TownNavigation:
    """Helpers for entities to locate and navigate to town services."""

    @staticmethod
    def get_nearest_service(
        entity: EntityState, 
        service_kind: str, 
        state: AuthoritativeState
    ) -> Optional[BuildingState]:
        """Find the closest functional building of the requested kind."""
        nearest = None
        min_dist = float('inf')
        
        ex, ey = entity.position
        
        for b in state.buildings.values():
            if b.kind == service_kind and b.functional:
                bx, by = b.position
                dist = math.sqrt((bx - ex)**2 + (by - ey)**2)
                if dist < min_dist:
                    min_dist = dist
                    nearest = b
                    
        return nearest

    @staticmethod
    def is_in_town(entity: EntityState, state: AuthoritativeState) -> bool:
        """Simple check if entity is within town radius (landmark based)."""
        tx, ty = state.town_center
        ex, ey = entity.position
        dist = math.sqrt((tx - ex)**2 + (ty - ey)**2)
        # Town radius threshold (placeholder 50 units)
        return dist < 50.0
