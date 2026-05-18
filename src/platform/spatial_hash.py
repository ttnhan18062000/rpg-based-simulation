# src/platform/spatial_hash.py
from __future__ import annotations
from typing import Dict, Set, Tuple, List, Optional
import math

class SpatialHashV2:
    """
    Deterministic spatial hash for RPG-core proximity and occupancy.
    Supports radius queries and cell-based lookups.
    VERIFIED v2: SpatialHashV2
    """

    def __init__(self, cell_size: int = 10):
        self.cell_size = cell_size
        self.grid: Dict[Tuple[int, int], Set[int]] = {}
        self.entity_pos: Dict[int, Tuple[float, float]] = {} # Precise positions

    def _get_cell(self, pos: Tuple[float, float]) -> Tuple[int, int]:
        return (int(pos[0] // self.cell_size), int(pos[1] // self.cell_size))

    def update_entity(self, entity_id: int, pos: Tuple[float, float]):
        new_cell = self._get_cell(pos)
        old_pos = self.entity_pos.get(entity_id)
        old_cell = self._get_cell(old_pos) if old_pos else None
        
        if old_cell != new_cell:
            if old_cell is not None:
                if old_cell in self.grid:
                    self.grid[old_cell].discard(entity_id)
                    if not self.grid[old_cell]: del self.grid[old_cell]
            if new_cell not in self.grid: self.grid[new_cell] = set()
            self.grid[new_cell].add(entity_id)
            
        self.entity_pos[entity_id] = pos

    def remove_entity(self, entity_id: int):
        old_pos = self.entity_pos.pop(entity_id, None)
        if old_pos:
            old_cell = self._get_cell(old_pos)
            if old_cell in self.grid:
                self.grid[old_cell].discard(entity_id)
                if not self.grid[old_cell]: del self.grid[old_cell]

    def query_radius(self, pos: Tuple[float, float], radius: float) -> List[int]:
        min_cell_x = int((pos[0] - radius) // self.cell_size)
        max_cell_x = int((pos[0] + radius) // self.cell_size)
        min_cell_y = int((pos[1] - radius) // self.cell_size)
        max_cell_y = int((pos[1] + radius) // self.cell_size)
        
        candidates = []
        for cx in range(min_cell_x, max_cell_x + 1):
            for cy in range(min_cell_y, max_cell_y + 1):
                cell = (cx, cy)
                if cell in self.grid: candidates.extend(self.grid[cell])
        
        # Exact distance check
        results = []
        r_sq = radius * radius
        for eid in candidates:
            epos = self.entity_pos[eid]
            dist_sq = (pos[0] - epos[0])**2 + (pos[1] - epos[1])**2
            if dist_sq <= r_sq:
                results.append(eid)
                
        return sorted(list(set(results)))
