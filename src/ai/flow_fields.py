"""Vector Flow Fields (Dijkstra Maps) for global navigation.

A Flow Field is a grid of vectors pointing toward a specific target location.
It allows O(1) pathfinding for many entities targeting the same destination
(e.g., all heroes returning to town).

Performance:
- Calculation: O(N log N) or O(N) using Breadth-First Search (Dijkstra).
- Lookup: O(1) per entity.
- Memory: 512x512 grid = 262,144 vectors (approx 2MB as float16).
"""

from __future__ import annotations
import math
from typing import TYPE_CHECKING
from src.core.models import Vector2, FloatVector2
from src.ai.pathfinding import tile_cost

if TYPE_CHECKING:
    from src.core.models.snapshot import SnapshotGrid

class FlowField:
    """A pre-calculated grid of direction vectors toward a single target."""
    
    __slots__ = ("target", "vectors", "width", "height", "created_at")
    
    def __init__(self, target: Vector2, width: int, height: int, tick: int = 0):
        self.target = target
        self.width = width
        self.height = height
        self.created_at = tick
        # Store as a flat list for performance: idx = y * width + x
        # Each element is a tuple (dx, dy) or None if unreachable
        self.vectors: list[tuple[int, int] | None] = [None] * (width * height)

    def get_vector(self, pos: Vector2 | FloatVector2) -> FloatVector2 | None:
        """Get the direction vector at the given position using bilinear interpolation for smoothing."""
        if not (0 <= pos.x < self.width - 1 and 0 <= pos.y < self.height - 1):
            # Fallback for boundaries
            x, y = int(max(0, min(self.width-1, pos.x))), int(max(0, min(self.height-1, pos.y)))
            v = self.vectors[y * self.width + x]
            return FloatVector2(v[0], v[1]).normalize() if v else None
            
        x0, y0 = int(pos.x), int(pos.y)
        x1, y1 = x0 + 1, y0 + 1
        fx, fy = pos.x - x0, pos.y - y0
        
        # Get vectors at the 4 corners
        v00 = self.vectors[y0 * self.width + x0]
        v10 = self.vectors[y0 * self.width + x1]
        v01 = self.vectors[y1 * self.width + x0]
        v11 = self.vectors[y1 * self.width + x1]
        
        # Interpolation weights
        w00 = (1 - fx) * (1 - fy)
        w10 = fx * (1 - fy)
        w01 = (1 - fx) * fy
        w11 = fx * fy
        
        vx, vy = 0.0, 0.0
        total_w = 0.0
        
        for v, w in [(v00, w00), (v10, w10), (v01, w01), (v11, w11)]:
            if v:
                vx += v[0] * w
                vy += v[1] * w
                total_w += w
        
        if total_w < 0.01:
            return None
            
        return FloatVector2(vx / total_w, vy / total_w).normalize()


class FlowFieldManager:
    """Manages creation and caching of flow fields for static locations."""
    
    _instance: FlowFieldManager | None = None
    
    def __init__(self):
        # target_pos_tuple -> FlowField
        self._cache: dict[tuple[int, int], FlowField] = {}
        self.default_ttl = 5

    @classmethod
    def get_instance(cls) -> FlowFieldManager:
        if cls._instance is None:
            cls._instance = FlowFieldManager()
        return cls._instance

    def get_flow_field(self, target: Vector2, grid: SnapshotGrid, current_tick: int = 0) -> FlowField:
        """Returns a cached flow field for the target, or generates a new one."""
        key = (target.x, target.y)
        if key in self._cache:
            ff = self._cache[key]
            if self._is_static_target(target, grid) or (current_tick - ff.created_at < self.default_ttl):
                return ff
            
        field = self._generate_dijkstra_map(target, grid, current_tick)
        self._cache[key] = field
        return field

    def _is_static_target(self, target: Vector2, grid: SnapshotGrid) -> bool:
        """Returns True if the target is a permanent location (Town/Camp)."""
        # Towns and Camps are static and never expire from cache
        if hasattr(grid, 'is_town') and grid.is_town(target):
            return True
        if hasattr(grid, 'is_camp') and grid.is_camp(target):
            return True
        return False

    def _generate_dijkstra_map(self, target: Vector2, grid: SnapshotGrid, tick: int = 0) -> FlowField:
        """Generate a Dijkstra Map using Breadth-First Search."""
        width, height = grid.width, grid.height
        field = FlowField(target, width, height, tick)
        
        # 1. Distances grid (infinity default)
        distances = [float('inf')] * (width * height)
        distances[target.y * width + target.x] = 0
        
        # 2. Priority Queue (Dijkstra)
        import heapq
        queue = [(0.0, target.x, target.y)]
        
        # 3. Fill distances
        while queue:
            d, cx, cy = heapq.heappop(queue)
            
            if d > distances[cy * width + cx]:
                continue
            
            # Check 8 neighbors
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0: continue
                    nx, ny = cx + dx, cy + dy
                    
                    if 0 <= nx < width and 0 <= ny < height:
                        npos = Vector2(nx, ny)
                        if not grid.is_walkable(npos):
                            continue
                        
                        # Use tile_cost (terrain awareness)
                        t_cost = tile_cost(grid, npos)
                        
                        # Diagonal multiplier
                        move_cost = t_cost * (1.414 if dx != 0 and dy != 0 else 1.0)
                        new_dist = d + move_cost
                        
                        idx = ny * width + nx
                        if new_dist < distances[idx]:
                            distances[idx] = new_dist
                            heapq.heappush(queue, (new_dist, nx, ny))

        # 4. Generate vectors from distances (gradient descent)
        for y in range(height):
            for x in range(width):
                idx = y * width + x
                if distances[idx] == float('inf') or (x == target.x and y == target.y):
                    continue
                
                # Look for neighbor with lowest distance
                best_v = None
                min_d = distances[idx]
                
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < width and 0 <= ny < height:
                            nd = distances[ny * width + nx]
                            if nd < min_d:
                                min_d = nd
                                best_v = (dx, dy)
                
                field.vectors[idx] = best_v
                
        return field
