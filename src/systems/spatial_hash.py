"""Spatial hashing for O(1) neighbor lookups."""

from __future__ import annotations

from collections import defaultdict

from src.core.models import Vector2


class SpatialHash:
    """Grid-based spatial index mapping cell keys to sets of entity IDs."""

    __slots__ = ("_cell_size", "_cells")

    def __init__(self, cell_size: int = 8) -> None:
        self._cell_size = cell_size
        self._cells: dict[tuple[int, int], set[int]] = defaultdict(set)

    def _key(self, pos: Vector2) -> tuple[int, int]:
        return pos.x // self._cell_size, pos.y // self._cell_size

    def insert(self, entity_id: int, pos: Vector2) -> None:
        self._cells[self._key(pos)].add(entity_id)

    def remove(self, entity_id: int, pos: Vector2) -> None:
        key = self._key(pos)
        bucket = self._cells.get(key)
        if bucket is not None:
            bucket.discard(entity_id)
            if not bucket:
                del self._cells[key]

    def move(self, entity_id: int, old_pos: Vector2, new_pos: Vector2) -> None:
        old_key = self._key(old_pos)
        new_key = self._key(new_pos)
        if old_key != new_key:
            self.remove(entity_id, old_pos)
            self.insert(entity_id, new_pos)

    def query_cell(self, pos: Vector2) -> set[int]:
        """Return entity IDs in the same cell as *pos*."""
        return set(self._cells.get(self._key(pos), set()))

    def query_radius(self, pos: Vector2, radius: int) -> set[int]:
        """Return entity IDs within *radius* cells of *pos*."""
        cx, cy = self._key(pos)
        r = (radius // self._cell_size) + 1
        result: set[int] = set()
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                bucket = self._cells.get((cx + dx, cy + dy))
                if bucket:
                    result.update(bucket)
        return result

    def clear(self) -> None:
        self._cells.clear()
