from __future__ import annotations

from typing import TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState


class DomainView:
    """
    Builds deterministic local neighbor views and world state snapshots for domain action execution.
    """

    @staticmethod
    def get_neighbor_view(
        state: AuthoritativeState,
        subject: EntityState,
        radius: float = 10.0
    ) -> List[tuple[int, EntityState]]:
        """
        Produce a deterministic, ID-sorted view of nearby entities.
        Uses a spatial grid to optimize O(N^2) lookups.
        VERIFIED v2: spatial_query_optimization
        """
        grid = DomainView._get_cached_spatial_grid(state)
        candidate_ids = grid.get_neighbors(subject.navigation.position, radius)
        
        neighbors = []
        sx, sy = subject.navigation.position
        for e_id in candidate_ids:
            if e_id == subject.id:
                continue
            
            ent = state.entities[e_id]
            ex, ey = ent.navigation.position
            dist = ((ex - sx)**2 + (ey - sy)**2)**0.5
            if dist <= radius:
                neighbors.append((e_id, ent))
                
        # Sort by ID for determinism
        neighbors.sort(key=lambda x: x[0])
        return neighbors

    @staticmethod
    def _get_cached_spatial_grid(state: AuthoritativeState):
        """Internal helper to cache grid per tick."""
        if not hasattr(DomainView, "_grid_cache"):
            DomainView._grid_cache = (None, None) # (cache_key, grid)
            
        # Hardening: Include tick, count, and seed to avoid id() collisions
        cache_key = (id(state), state.tick, len(state.entities), state.seed)
        if DomainView._grid_cache[0] != cache_key:
            from src.engine.spatial import SpatialGrid
            DomainView._grid_cache = (cache_key, SpatialGrid(state.entities))
            
        return DomainView._grid_cache[1]

    @staticmethod
    def get_region_trauma(
        state: AuthoritativeState,
        pos: Tuple[float, float]
    ) -> float:
        """
        Finds the trauma score of the region containing the given position.
        """
        px, py = pos
        for region in state.regions.values():
            xmin, ymin, xmax, ymax = region.bounds
            if xmin <= px <= xmax and ymin <= py <= ymax:
                return region.trauma_score
        return 0.0
