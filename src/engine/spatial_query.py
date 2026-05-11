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
        if hasattr(state, "occupancy_map") and state.occupancy_map is not None:
            return state.occupancy_map
            
        mapping = getattr(state, cache_key, None)
        if mapping is None:
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
    def _get_building_map(state: AuthoritativeState) -> Dict[tuple[int, int], BuildingState]:
        cache_key = "_building_map_cache"
        if hasattr(state, "building_map") and state.building_map is not None:
            return state.building_map
            
        mapping = getattr(state, cache_key, None)
        if mapping is None:
            mapping = {b.position: b for b in state.buildings.values()}
            object.__setattr__(state, cache_key, mapping)
        return mapping
