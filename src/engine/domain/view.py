from __future__ import annotations

from typing import TYPE_CHECKING, List, Tuple, Optional, Any

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState
from src.engine.spatial import SpatialGrid

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
        Produce a deterministic view of nearby entities.
        Uses a spatial grid to optimize O(N^2) lookups.
        VERIFIED v2: spatial_query_optimization
        """
        grid = DomainView._get_cached_spatial_grid(state)
        candidate_ids = grid.get_neighbors(subject.navigation.position, radius)
        
        results: List[tuple[int, EntityState]] = []
        for e_id in candidate_ids:
            if e_id == subject.id:
                continue
            
            ent = state.entities.get(e_id)
            if ent:
                results.append((e_id, ent))
        
        # Sort by ID for absolute determinism in tactical selection
        results.sort(key=lambda x: x[0])
        return results

    @staticmethod
    def _get_cached_spatial_grid(state: AuthoritativeState) -> SpatialGrid:
        """
        Retrieves or creates a SpatialGrid for the given state.
        Uses a per-object cache to ensure thread-safety and avoid collisions.
        """
        # Milestone 8: Per-object caching for multi-threaded safety.
        # This prevents race conditions in MultiThreadedExecutor where different
        # threads might be processing different states (or the same state) concurrently.
        
        # Check if it's a WorkerPacket with a pre-computed grid
        if hasattr(state, "spatial_grid") and state.spatial_grid is not None:
            return state.spatial_grid

        grid = getattr(state, "_spatial_grid_cache", None)
        if grid is None:
            grid = SpatialGrid(state.entities)
            # Use object.__setattr__ to bypass frozen dataclass restrictions
            object.__setattr__(state, "_spatial_grid_cache", grid)
        return grid

    @staticmethod
    def get_region_for_position(
        state: AuthoritativeState,
        pos: Tuple[float, float]
    ) -> Optional[Any]:
        """
        Fast lookup for the region containing a position.
        Uses a per-object regional list cache for isolation and safety.
        """
        # Milestone 8: Per-object caching for regional lookups.
        if hasattr(state, "region_list") and state.region_list is not None:
            region_list = state.region_list
        else:
            region_list = getattr(state, "_region_list_cache", None)
            if region_list is None:
                region_list = list(state.regions.values())
                object.__setattr__(state, "_region_list_cache", region_list)
            
        px, py = pos
        for region in region_list:
            x_min, y_min, x_max, y_max = region.bounds
            if x_min <= px <= x_max and y_min <= py <= y_max:
                return region
        return None

    @staticmethod
    def get_region_trauma(
        state: AuthoritativeState,
        pos: Tuple[float, float]
    ) -> float:
        """
        Finds the trauma score of the region containing the given position.
        """
        region = DomainView.get_region_for_position(state, pos)
        return region.trauma_score if region else 0.0
