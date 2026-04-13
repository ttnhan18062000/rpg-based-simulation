"""Grid / map system."""

from __future__ import annotations
from typing import TYPE_CHECKING, Any

from src.core.models.enums import Material
from src.core.models import Vector2

# Pre-cache Material objects to avoid the high overhead of Material(int_value) 
# during frequent grid lookups (Clean Code: Performance Optimization)
_MATERIAL_CACHE = [Material.WALL] * 256
for m in Material:
    _MATERIAL_CACHE[int(m)] = m


from src.core.models.base import SimulationModel
from pydantic import ConfigDict, model_validator, model_serializer

class Grid(SimulationModel):
    """2D tile grid backed by a flat list for cache-friendly access."""
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    width: int
    height: int
    tiles: bytearray | bytes

    @model_serializer(mode='plain')
    def _serialize_grid(self) -> dict[str, Any]:
        """AOA Phase 6: Canonical hex serialization for grid tiles."""
        return {
            "width": self.width,
            "height": self.height,
            "tiles": self.tiles.hex() if hasattr(self.tiles, "hex") else bytes(self.tiles).hex()
        }

    @model_validator(mode='before')
    @classmethod
    def _coerce_tiles(cls, data: Any) -> Any:
        """Support deserialization from hex string or list (AOA Stabilization)."""
        if not isinstance(data, dict):
            return data
        tiles = data.get("tiles")
        if isinstance(tiles, str):
            # Decode hex
            data["tiles"] = bytearray.fromhex(tiles)
        elif isinstance(tiles, (list, tuple)):
            data["tiles"] = bytearray(tiles)
        return data

    def __init__(self, width: int = 0, height: int = 0, default: Material = Material.FLOOR, **data: Any) -> None:
        """AOA Hardened: Support both manual and Pydantic initialization."""
        if "width" not in data and width > 0: data["width"] = width
        if "height" not in data and height > 0: data["height"] = height
        if "tiles" not in data and "width" in data and "height" in data:
            data["tiles"] = bytearray([int(default)]) * (data["width"] * data["height"])
        
        # Ensure tiles is bytearray if passed via data
        if "tiles" in data and isinstance(data["tiles"], (bytes, list, tuple)):
            data["tiles"] = bytearray(data["tiles"])
            
        super().__init__(**data)

    # -- access --

    def _idx(self, x: int, y: int) -> int:
        return y * self.width + x

    def in_bounds(self, pos: Vector2) -> bool:
        return 0 <= pos.x < self.width and 0 <= pos.y < self.height

    def get(self, pos: Vector2) -> Material:
        if not self.in_bounds(pos):
            return Material.WALL
        val = self.tiles[self._idx(pos.x, pos.y)]
        return _MATERIAL_CACHE[val]

    def set(self, pos: Vector2, material: Material) -> None:
        if self.in_bounds(pos):
            self.tiles[self._idx(pos.x, pos.y)] = int(material)

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
            val = self.tiles[y * self.width + x]
            return _MATERIAL_CACHE[val]
        return Material.WALL

    # -- copy --

    def copy(self) -> Grid:
        """Standard deep copy for snapshots."""
        return Grid(
            width=self.width,
            height=self.height,
            tiles=bytearray(self.tiles)
        )

Grid.model_rebuild()
