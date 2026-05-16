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
        tuples = grid.get_neighbor_tuples(subject.navigation.position, radius, subject.id)
        # Sort by entity ID for absolute determinism in tactical selection
        tuples.sort(key=lambda item: item[0])
        return tuples

    @staticmethod
    def _get_cached_spatial_grid(state: AuthoritativeState) -> SpatialGrid:
        """
        Retrieves or creates a SpatialGrid for the given state.
        Uses a per-object cache to ensure thread-safety and avoid collisions.
        """
        grid = getattr(state, "_spatial_grid_cache", None)
        if grid is not None:
            return grid
            
        if getattr(state, "spatial_grid", None) is not None:
            return state.spatial_grid

        grid = SpatialGrid(state.entities)
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
        region_list = getattr(state, "_region_list_cache", None)
        if region_list is None:
            if getattr(state, "region_list", None) is not None:
                region_list = state.region_list
            else:
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
