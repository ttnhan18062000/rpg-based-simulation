from typing import Dict, List, Tuple
from src.core.state import EntityState

class SpatialGrid:
    """
    Utility for $O(1)$ spatial lookups.
    """
    def __init__(self, entities: Dict[int, EntityState], cell_size: int = 5):
        self.grid: Dict[Tuple[int, int], List[int]] = {}
        self.grid_tuples: Dict[Tuple[int, int], List[Tuple[int, EntityState]]] = {}
        self.cell_size = cell_size
        
        for eid, ent in entities.items():
            cx = int(ent.navigation.position[0] // cell_size)
            cy = int(ent.navigation.position[1] // cell_size)
            cell = (cx, cy)
            if cell not in self.grid:
                self.grid[cell] = []
                self.grid_tuples[cell] = []
            self.grid[cell].append(eid)
            self.grid_tuples[cell].append((eid, ent))

    def get_neighbors(self, pos: Tuple[float, float], radius: float) -> List[int]:
        cx = int(pos[0] // self.cell_size)
        cy = int(pos[1] // self.cell_size)
        
        # Determine cell range
        cell_radius = int(radius // self.cell_size) + 1
        
        results = []
        for x in range(cx - cell_radius, cx + cell_radius + 1):
            for y in range(cy - cell_radius, cy + cell_radius + 1):
                if (x, y) in self.grid:
                    results.extend(self.grid[(x, y)])
        return results

    def get_neighbor_tuples(self, pos: Tuple[float, float], radius: float, ignore_id: int) -> List[Tuple[int, EntityState]]:
        cx = int(pos[0] // self.cell_size)
        cy = int(pos[1] // self.cell_size)
        cell_radius = int(radius // self.cell_size) + 1
        
        r2 = radius * radius
        px, py = pos[0], pos[1]
        results = []
        for x in range(cx - cell_radius, cx + cell_radius + 1):
            for y in range(cy - cell_radius, cy + cell_radius + 1):
                if (x, y) in self.grid_tuples:
                    for eid, ent in self.grid_tuples[(x, y)]:
                        if eid != ignore_id:
                            dx = ent.navigation.position[0] - px
                            if -radius <= dx <= radius:
                                dy = ent.navigation.position[1] - py
                                if -radius <= dy <= radius:
                                    if dx*dx + dy*dy <= r2:
                                        results.append((eid, ent))
        return results

    def get_in_bounds(self, bounds: Tuple[float, float, float, float]) -> List[int]:
        """Returns IDs of entities within the rectangular bounds (xmin, ymin, xmax, ymax)."""
        xmin, ymin, xmax, ymax = bounds
        cx_min = int(xmin // self.cell_size)
        cy_min = int(ymin // self.cell_size)
        cx_max = int(xmax // self.cell_size)
        cy_max = int(ymax // self.cell_size)
        
        results = []
        for x in range(cx_min, cx_max + 1):
            for y in range(cy_min, cy_max + 1):
                if (x, y) in self.grid:
                    results.extend(self.grid[(x, y)])
        return results
