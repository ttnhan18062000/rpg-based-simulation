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

    # -- copy --

    def copy(self) -> Grid:
        new = Grid.__new__(Grid)
        new.width = self.width
        new.height = self.height
        new._tiles = list(self._tiles)
        return new
