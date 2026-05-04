from typing import Dict, List, Tuple
from src.core.state import EntityState

class SpatialGrid:
    """
    Utility for $O(1)$ spatial lookups.
    """
    def __init__(self, entities: Dict[int, EntityState], cell_size: int = 5):
        self.grid: Dict[Tuple[int, int], List[int]] = {}
        self.cell_size = cell_size
        
        for eid, ent in entities.items():
            cx = int(ent.navigation.position[0] // cell_size)
            cy = int(ent.navigation.position[1] // cell_size)
            if (cx, cy) not in self.grid:
                self.grid[(cx, cy)] = []
            self.grid[(cx, cy)].append(eid)

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
