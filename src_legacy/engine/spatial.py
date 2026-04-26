# src/engine/spatial.py
from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List, Set, Tuple, Optional

if TYPE_CHECKING:
    from src_legacy.core.state import EntityState, AuthoritativeState

class SpatialIndexV2:
    """
    Grid-based spatial index for V2 simulation.
    Provides O(1) point queries and O(K) radius queries.
    """

    def __init__(self):
        self._grid: Dict[Tuple[int, int], Set[int]] = {}
        self._entity_to_pos: Dict[int, Tuple[int, int]] = {}

    def clear(self):
        self._grid.clear()
        self._entity_to_pos.clear()

    def add(self, entity_id: int, pos: Tuple[float, float]):
        grid_pos = (int(pos[0]), int(pos[1]))
        self._grid.setdefault(grid_pos, set()).add(entity_id)
        self._entity_to_pos[entity_id] = grid_pos

    def remove(self, entity_id: int):
        if entity_id in self._entity_to_pos:
            grid_pos = self._entity_to_pos.pop(entity_id)
            if grid_pos in self._grid:
                self._grid[grid_pos].discard(entity_id)
                if not self._grid[grid_pos]:
                    del self._grid[grid_pos]

    def update(self, entity_id: int, new_pos: Tuple[float, float]):
        self.remove(entity_id)
        self.add(entity_id, new_pos)

    def get_occupants(self, pos: Tuple[float, float]) -> Set[int]:
        grid_pos = (int(pos[0]), int(pos[1]))
        return self._grid.get(grid_pos, set())

    def query_radius(self, center: Tuple[float, float], radius: int) -> List[int]:
        """
        Returns entity IDs within Manhattan distance of radius.
        """
        center_x, center_y = int(center[0]), int(center[1])
        results = []
        
        # Grid-based optimization: only check cells within the bounding box of the radius
        for dx in range(-radius, radius + 1):
            for dy in range(-(radius - abs(dx)), (radius - abs(dx)) + 1):
                grid_pos = (center_x + dx, center_y + dy)
                if grid_pos in self._grid:
                    results.extend(list(self._grid[grid_pos]))
        return results

    @classmethod
    def build_from_state(cls, state: AuthoritativeState) -> SpatialIndexV2:
        index = cls()
        for e_id, entity in state.entities.items():
            if entity.active:
                index.add(e_id, entity.position)
        return index
