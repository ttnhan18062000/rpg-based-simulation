"""A* Pathfinding with terrain cost awareness (epic-09).

Provides a `Pathfinder` class that computes optimal paths through the grid,
respecting walkability, terrain movement costs, and an occupied-tile set.

Usage:
    pf = Pathfinder(grid)
    path = pf.find_path(start, goal)          # list[Vector2] or None
    next_step = pf.next_step(start, goal)     # Vector2 or None
"""

from __future__ import annotations

import heapq
from typing import TYPE_CHECKING

from src.core.enums import Material
from src.core.models import Vector2

if TYPE_CHECKING:
    from src.core.grid import Grid

# ---------------------------------------------------------------------------
# Terrain movement cost registry (F2)
# ---------------------------------------------------------------------------
# Cost 1.0 = baseline.  Lower = faster (roads).  Higher = slower.
# Impassable tiles (WALL, WATER, LAVA) are handled by Grid.is_walkable().

TERRAIN_MOVE_COST: dict[Material, float] = {
    Material.FLOOR:             1.0,
    Material.TOWN:              1.0,
    Material.CAMP:              1.0,
    Material.SANCTUARY:         1.0,
    Material.RUINS:             1.0,
    Material.DUNGEON_ENTRANCE:  1.0,
    Material.ROAD:              0.7,
    Material.BRIDGE:            0.7,
    Material.FOREST:            1.3,
    Material.DESERT:            1.2,
    Material.SWAMP:             1.5,
    Material.MOUNTAIN:          1.4,
}

# Cardinal directions (no diagonals — Manhattan grid)
_DIRS = (Vector2(1, 0), Vector2(-1, 0), Vector2(0, 1), Vector2(0, -1))


def tile_cost(grid: Grid, pos: Vector2) -> float:
    """Return the movement cost for stepping onto *pos*."""
    mat = grid.get(pos)
    return TERRAIN_MOVE_COST.get(mat, 1.0)


# ---------------------------------------------------------------------------
# A* Pathfinder
# ---------------------------------------------------------------------------

class Pathfinder:
    """A* pathfinder operating on the simulation Grid.

    Thread-safe: reads only from the immutable snapshot grid.
    Performance-bounded: explores at most `max_nodes` before giving up.
    """

    __slots__ = ("_grid", "_max_nodes")

    def __init__(self, grid: Grid, max_nodes: int = 200) -> None:
        self._grid = grid
        self._max_nodes = max_nodes

    def find_path(
        self,
        start: Vector2,
        goal: Vector2,
        occupied: frozenset[tuple[int, int]] | set[tuple[int, int]] | None = None,
        exclude_goal_from_occupied: bool = True,
    ) -> list[Vector2] | None:
        """Compute an A* path from *start* to *goal*.

        Returns a list of Vector2 positions (excluding *start*, including *goal*),
        or None if no path exists within the node budget.

        *occupied* is a set of (x, y) tuples that are blocked by other entities.
        The *goal* tile is always considered reachable even if occupied (the
        entity intends to move *toward* it, not necessarily onto it).
        """
        if start == goal:
            return []

        grid = self._grid
        if not grid.is_walkable(goal):
            return None

        occ = occupied or set()

        # A* open set: (f_score, counter, x, y)
        counter = 0
        open_heap: list[tuple[float, int, int, int]] = []
        heapq.heappush(open_heap, (0.0, counter, start.x, start.y))

        g_score: dict[tuple[int, int], float] = {(start.x, start.y): 0.0}
        came_from: dict[tuple[int, int], tuple[int, int]] = {}
        closed: set[tuple[int, int]] = set()
        nodes_explored = 0

        gx, gy = goal.x, goal.y

        while open_heap and nodes_explored < self._max_nodes:
            _, _, cx, cy = heapq.heappop(open_heap)
            ckey = (cx, cy)

            if cx == gx and cy == gy:
                # Reconstruct path
                return self._reconstruct(came_from, ckey)

            if ckey in closed:
                continue
            closed.add(ckey)
            nodes_explored += 1

            current_g = g_score[ckey]

            for d in _DIRS:
                nx, ny = cx + d.x, cy + d.y
                nkey = (nx, ny)

                if nkey in closed:
                    continue

                npos = Vector2(nx, ny)
                if not grid.is_walkable(npos):
                    continue

                # Occupied check (skip goal tile)
                if nkey in occ and not (exclude_goal_from_occupied and nx == gx and ny == gy):
                    continue

                step_cost = tile_cost(grid, npos)
                tentative_g = current_g + step_cost

                if tentative_g < g_score.get(nkey, float("inf")):
                    g_score[nkey] = tentative_g
                    came_from[nkey] = ckey
                    h = abs(nx - gx) + abs(ny - gy)  # Manhattan heuristic
                    f = tentative_g + h
                    counter += 1
                    heapq.heappush(open_heap, (f, counter, nx, ny))

        return None  # No path found within budget

    def next_step(
        self,
        start: Vector2,
        goal: Vector2,
        occupied: frozenset[tuple[int, int]] | set[tuple[int, int]] | None = None,
    ) -> Vector2 | None:
        """Return the first step of the A* path, or None if no path exists."""
        path = self.find_path(start, goal, occupied)
        if path and len(path) > 0:
            return path[0]
        return None

    @staticmethod
    def _reconstruct(
        came_from: dict[tuple[int, int], tuple[int, int]],
        current: tuple[int, int],
    ) -> list[Vector2]:
        """Walk back through came_from to build the path."""
        path: list[Vector2] = []
        while current in came_from:
            path.append(Vector2(current[0], current[1]))
            current = came_from[current]
        path.reverse()
        return path
