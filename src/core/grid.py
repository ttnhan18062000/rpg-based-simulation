"""Grid / map system."""

from __future__ import annotations

from src.core.enums import Material
from src.core.models import Vector2


class Grid:
    """2D tile grid backed by a flat list for cache-friendly access."""

    __slots__ = ("width", "height", "_tiles")

    def __init__(self, width: int, height: int, default: Material = Material.FLOOR) -> None:
        self.width = width
        self.height = height
        self._tiles: list[Material] = [default] * (width * height)

    # -- access --

    def _idx(self, x: int, y: int) -> int:
        return y * self.width + x

    def in_bounds(self, pos: Vector2) -> bool:
        return 0 <= pos.x < self.width and 0 <= pos.y < self.height

    def get(self, pos: Vector2) -> Material:
        if not self.in_bounds(pos):
            return Material.WALL
        return self._tiles[self._idx(pos.x, pos.y)]

    def set(self, pos: Vector2, material: Material) -> None:
        if self.in_bounds(pos):
            self._tiles[self._idx(pos.x, pos.y)] = material

    def is_walkable(self, pos: Vector2) -> bool:
        mat = self.get(pos)
        return mat not in (Material.WALL, Material.WATER, Material.LAVA)

    def is_forest(self, pos: Vector2) -> bool:
        return self.get(pos) == Material.FOREST

    def is_desert(self, pos: Vector2) -> bool:
        return self.get(pos) == Material.DESERT

    def is_swamp(self, pos: Vector2) -> bool:
        return self.get(pos) == Material.SWAMP

    def is_mountain(self, pos: Vector2) -> bool:
        return self.get(pos) == Material.MOUNTAIN

    def is_town(self, pos: Vector2) -> bool:
        return self.get(pos) == Material.TOWN

    def is_camp(self, pos: Vector2) -> bool:
        return self.get(pos) == Material.CAMP

    def is_sanctuary(self, pos: Vector2) -> bool:
        return self.get(pos) == Material.SANCTUARY

    def is_road(self, pos: Vector2) -> bool:
        return self.get(pos) == Material.ROAD

    def is_bridge(self, pos: Vector2) -> bool:
        return self.get(pos) == Material.BRIDGE

    def is_ruins(self, pos: Vector2) -> bool:
        return self.get(pos) == Material.RUINS

    def is_dungeon_entrance(self, pos: Vector2) -> bool:
        return self.get(pos) == Material.DUNGEON_ENTRANCE

    def is_lava(self, pos: Vector2) -> bool:
        return self.get(pos) == Material.LAVA

    # -- line-of-sight (Bresenham) --

    def has_line_of_sight(self, x0: int, y0: int, x1: int, y1: int) -> bool:
        """Check if there is a clear line of sight between two positions.

        Uses Bresenham's line algorithm. Returns False if any WALL tile
        lies on the line between (x0,y0) and (x1,y1), exclusive of endpoints.
        """
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        cx, cy = x0, y0
        while True:
            if cx == x1 and cy == y1:
                return True
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                cx += sx
            if e2 < dx:
                err += dx
                cy += sy
            # Check intermediate tile (skip start and end)
            if (cx != x1 or cy != y1) and self.get_xy(cx, cy) == Material.WALL:
                return False
        return True

    def has_adjacent_wall(self, x: int, y: int) -> bool:
        """Check if any of the 4 cardinal neighbors is a WALL tile (for cover)."""
        return (
            self.get_xy(x - 1, y) == Material.WALL
            or self.get_xy(x + 1, y) == Material.WALL
            or self.get_xy(x, y - 1) == Material.WALL
            or self.get_xy(x, y + 1) == Material.WALL
        )

    # -- fast raw-coordinate access (no Vector2 alloc, for hot loops) --

    def in_bounds_xy(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get_xy(self, x: int, y: int) -> Material:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self._tiles[y * self.width + x]
        return Material.WALL

    # -- copy --

    def copy(self) -> Grid:
        new = Grid.__new__(Grid)
        new.width = self.width
        new.height = self.height
        new._tiles = list(self._tiles)
        return new
