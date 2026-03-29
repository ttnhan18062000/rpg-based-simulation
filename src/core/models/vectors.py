from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Vector2:
    """Immutable 2D integer coordinate."""

    x: int = 0
    y: int = 0

    def __add__(self, other: Vector2) -> Vector2:
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vector2) -> Vector2:
        return Vector2(self.x - other.x, self.y - other.y)

    def manhattan(self, other: Vector2) -> int:
        return abs(self.x - other.x) + abs(self.y - other.y)

    def __repr__(self) -> str:
        return f"({self.x}, {self.y})"


@dataclass(frozen=True, slots=True)
class FloatVector2:
    """Immutable 2D float coordinate for physics and smoothing."""
    x: float = 0.0
    y: float = 0.0

    def __add__(self, other: FloatVector2) -> FloatVector2:
        return FloatVector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: FloatVector2) -> FloatVector2:
        return FloatVector2(self.x - other.x, self.y - other.y)

    def length(self) -> float:
        import math
        return math.sqrt(self.x * self.x + self.y * self.y)

    def normalize(self) -> FloatVector2:
        L = self.length()
        if L < 1e-6: return FloatVector2(0, 0)
        return FloatVector2(self.x / L, self.y / L)

    def __repr__(self) -> str:
        return f"f({self.x:.2f}, {self.y:.2f})"


# Direction offsets mapped to Direction enum values
DIRECTION_OFFSETS: dict[int, Vector2] = {
    0: Vector2(0, -1),  # NORTH
    1: Vector2(1, 0),   # EAST
    2: Vector2(0, 1),   # SOUTH
    3: Vector2(-1, 0),  # WEST
}
