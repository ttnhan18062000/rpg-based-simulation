from __future__ import annotations
from typing import List, Tuple, Optional, TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState, ResourceNodeState, BuildingState

class SpatialQueryService:
    """
    Optimized spatial queries using cached indices.
    Logic ID: PERF-007 (Spatial Query Service)
    """

    @staticmethod
    def get_entities_near(state: AuthoritativeState, pos: tuple[float, float], radius: float) -> List[int]:
        """Returns IDs of entities within radius of pos."""
        from src.engine.domain.view import DomainView
        grid = DomainView._get_cached_spatial_grid(state)
        return grid.get_neighbors(pos, radius)

    @staticmethod
    def get_entities_in_bounds(state: AuthoritativeState, bounds: Tuple[float, float, float, float]) -> List[int]:
        """Returns IDs of entities within the rectangular bounds."""
        from src.engine.domain.view import DomainView
        grid = DomainView._get_cached_spatial_grid(state)
        return grid.get_in_bounds(bounds)

    @staticmethod
    def get_nodes_near(state: AuthoritativeState, pos: tuple[float, float], radius: float) -> List[int]:
        """Returns IDs of resource nodes within radius of pos."""
        # For now, resource nodes are few, so brute force is fine if not cached.
        # But we should eventually index them too.
        res = []
        r2 = radius * radius
        for n_id, node in state.resource_nodes.items():
            dx = node.position[0] - pos[0]
            dy = node.position[1] - pos[1]
            if dx*dx + dy*dy <= r2:
                res.append(n_id)
        return res

    @staticmethod
    def get_building_at(state: AuthoritativeState, pos: tuple[int, int]) -> Optional[BuildingState]:
        """Returns the building at a specific tile coordinate."""
        # state.building_tiles gives the type, but not the building object.
        # state.buildings is a dict. We can build a spatial map for it.
        mapping = SpatialQueryService._get_building_map(state)
        return mapping.get(pos)

    @staticmethod
    def get_occupancy_map(state: AuthoritativeState) -> Dict[tuple[int, int], int]:
        """Returns a map of (x, y) to entity ID for all active/alive entities."""
        cache_key = "_occupancy_map_cache"
        mapping = getattr(state, cache_key, None)
        if mapping is not None:
            return mapping
            
        if getattr(state, "occupancy_map", None) is not None:
            return state.occupancy_map
            
        mapping = {}
        for e_id, entity in state.entities.items():
            if entity.lifecycle.active and entity.combat.alive:
                pos = (int(entity.navigation.position[0]), int(entity.navigation.position[1]))
                mapping[pos] = e_id
        object.__setattr__(state, cache_key, mapping)
        return mapping

    @staticmethod
    def get_node_at(state: AuthoritativeState, pos: tuple[float, float]) -> Optional[ResourceNodeState]:
        """Returns the resource node at a specific position."""
        mapping = SpatialQueryService._get_node_map(state)
        return mapping.get(pos)

    @staticmethod
    def get_corpse_at(state: AuthoritativeState, pos: tuple[float, float]) -> Optional[Any]:
        """Returns the corpse at a specific position."""
        mapping = SpatialQueryService._get_corpse_map(state)
        return mapping.get(pos)

    @staticmethod
    def get_ground_item_at(state: AuthoritativeState, pos: tuple[float, float]) -> Optional[Any]:
        """Returns the ground item at a specific position."""
        mapping = SpatialQueryService._get_ground_item_map(state)
        return mapping.get(pos)

    @staticmethod
    def _get_node_map(state: AuthoritativeState) -> Dict[tuple[float, float], ResourceNodeState]:
        cache_key = "_node_map_cache"
        mapping = getattr(state, cache_key, None)
        if mapping is None:
            mapping = {n.position: n for n in state.resource_nodes.values()}
            object.__setattr__(state, cache_key, mapping)
        return mapping

    @staticmethod
    def _get_corpse_map(state: AuthoritativeState) -> Dict[tuple[float, float], Any]:
        cache_key = "_corpse_map_cache"
        mapping = getattr(state, cache_key, None)
        if mapping is None:
            mapping = {c.position: c for c in state.corpses.values()}
            object.__setattr__(state, cache_key, mapping)
        return mapping

    @staticmethod
    def _get_ground_item_map(state: AuthoritativeState) -> Dict[tuple[float, float], Any]:
        cache_key = "_ground_item_map_cache"
        mapping = getattr(state, cache_key, None)
        if mapping is None:
            mapping = {g.position: g for g in state.ground_items.values()}
            object.__setattr__(state, cache_key, mapping)
        return mapping

    @staticmethod
    def get_region_at(state: AuthoritativeState, pos: tuple[float, float]) -> Optional[RegionState]:
        """Returns the region containing the given position."""
        if not state.regions:
            return None
        # Quick exit if outside all regions
        bounds = SpatialQueryService._get_regions_global_bounds(state)
        if bounds:
             if not (bounds[0] <= pos[0] < bounds[2] and bounds[1] <= pos[1] < bounds[3]):
                 return None
                 
        index = SpatialQueryService._get_region_index(state)
        if index:
             cell_size = 50.0
             cx = int(pos[0] // cell_size)
             cy = int(pos[1] // cell_size)
             r_ids = index.get((cx, cy), [])
             for r_id in r_ids:
                 r = state.regions.get(r_id)
                 if r:
                     x_min, y_min, x_max, y_max = r.bounds
                     if x_min <= pos[0] < x_max and y_min <= pos[1] < y_max:
                         return r
        return None

    @staticmethod
    def _get_region_index(state: AuthoritativeState) -> Any:
        cache_key = "_region_index_cache"
        index = getattr(state, cache_key, None)
        if index is None:
            if not state.regions:
                return None
            
            # Use a simple grid index
            cell_size = 50.0
            index = {}
            for r_id, r in state.regions.items():
                x_min, y_min, x_max, y_max = r.bounds
                cx_start = int(x_min // cell_size)
                cy_start = int(y_min // cell_size)
                cx_end = int(x_max // cell_size)
                cy_end = int(y_max // cell_size)
                
                for cx in range(cx_start, cx_end + 1):
                    for cy in range(cy_start, cy_end + 1):
                        index.setdefault((cx, cy), []).append(r_id)
            
            object.__setattr__(state, cache_key, index)
        return index

    @staticmethod
    def _get_regions_global_bounds(state: AuthoritativeState) -> Optional[tuple[float, float, float, float]]:
        cache_key = "_regions_global_bounds"
        bounds = getattr(state, cache_key, None)
        if bounds is False:
            return None
        if bounds is None:
            if not state.regions:
                object.__setattr__(state, cache_key, False)
                return None
            x_min = y_min = float('inf')
            x_max = y_max = float('-inf')
            for r in state.regions.values():
                x_min = min(x_min, r.bounds[0])
                y_min = min(y_min, r.bounds[1])
                x_max = max(x_max, r.bounds[2])
                y_max = max(y_max, r.bounds[3])
            bounds = (x_min, y_min, x_max, y_max)
            object.__setattr__(state, cache_key, bounds)
        return bounds

    @staticmethod
    def get_building_region(state: AuthoritativeState, building_id: int) -> Optional[RegionState]:
        """Returns the region containing a building, using a cached map."""
        mapping = SpatialQueryService._get_building_region_map(state)
        region_id = mapping.get(building_id)
        return state.regions.get(region_id) if region_id else None

    @staticmethod
    def _get_building_region_map(state: AuthoritativeState) -> Dict[int, str]:
        cache_key = "_building_region_map_cache"
        mapping = getattr(state, cache_key, None)
        if mapping is None:
            mapping = {}
            for b_id, b in state.buildings.items():
                r = SpatialQueryService.get_region_at(state, b.position)
                if r:
                    mapping[b_id] = r.id
            object.__setattr__(state, cache_key, mapping)
        return mapping

    @staticmethod
    def _get_building_map(state: AuthoritativeState) -> Dict[tuple[int, int], BuildingState]:
        cache_key = "_building_map_cache"
        mapping = getattr(state, cache_key, None)
        if mapping is not None:
            return mapping
            
        if getattr(state, "building_map", None) is not None:
            return state.building_map
            
        mapping = {b.position: b for b in state.buildings.values()}
        object.__setattr__(state, cache_key, mapping)
        return mapping
