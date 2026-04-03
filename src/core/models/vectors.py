from __future__ import annotations
from typing import Any
from src.core.models.base import SimulationModel
from pydantic import ConfigDict

class Vector2(SimulationModel):
    """Immutable 2D integer coordinate (AOA Hardened)."""
    model_config = ConfigDict(frozen=True, slots=True, extra="ignore")

    x: int = 0
    y: int = 0

    def __init__(self, x: int = 0, y: int = 0, **kwargs: Any):
        """Supported positional and keyword initialization."""
        # Prioritize keyword args if present, otherwise use positional
        # This avoiding 'multiple values for argument' errors
        x_val = kwargs.pop("x", x)
        y_val = kwargs.pop("y", y)
        super().__init__(x=x_val, y=y_val, **kwargs)

    def __add__(self, other: Vector2) -> Vector2:
        return Vector2(x=self.x + other.x, y=self.y + other.y)

    def __sub__(self, other: Vector2) -> Vector2:
        return Vector2(x=self.x - other.x, y=self.y - other.y)

    def manhattan(self, other: Any) -> int:
        """Robust manhattan distance (AOA Hardened for dict-coercion)."""
        if not isinstance(other, Vector2):
            other = Vector2.from_any(other)
        return abs(self.x - other.x) + abs(self.y - other.y)

    @staticmethod
    def from_any(val: Any) -> Vector2:
        """Robustly convert dict, tuple, or Vector2 to Vector2."""
        if isinstance(val, Vector2):
            return val
        if isinstance(val, (tuple, list)) and len(val) >= 2:
            return Vector2(x=int(val[0]), y=int(val[1]))
        if isinstance(val, dict):
            return Vector2(x=int(val.get('x', 0)), y=int(val.get('y', 0)))
        return Vector2(x=0, y=0)

    def __repr__(self) -> str:
        return f"({self.x}, {self.y})"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Vector2):
            other = Vector2.from_any(other)
        return self.x == other.x and self.y == other.y

    def __hash__(self) -> int:
        return hash((self.x, self.y))


class FloatVector2(SimulationModel):
    """Immutable 2D float coordinate (AOA Hardened)."""
    model_config = ConfigDict(frozen=True, slots=True, extra="ignore")

    x: float = 0.0
    y: float = 0.0

    def __init__(self, x: float = 0.0, y: float = 0.0, **kwargs: Any):
        """Supported positional and keyword initialization."""
        x_val = kwargs.pop("x", x)
        y_val = kwargs.pop("y", y)
        super().__init__(x=x_val, y=y_val, **kwargs)

    def __add__(self, other: FloatVector2) -> FloatVector2:
        return FloatVector2(x=self.x + other.x, y=self.y + other.y)

    def __sub__(self, other: FloatVector2) -> FloatVector2:
        return FloatVector2(x=self.x - other.x, y=self.y - other.y)

    def length(self) -> float:
        import math
        return math.sqrt(self.x * self.x + self.y * self.y)

    def normalize(self) -> FloatVector2:
        L = self.length()
        if L < 1e-6: return FloatVector2(x=0.0, y=0.0)
        return FloatVector2(x=self.x / L, y=self.y / L)

    def __repr__(self) -> str:
        return f"f({self.x:.2f}, {self.y:.2f})"


# Direction offsets mapped to Direction enum values
DIRECTION_OFFSETS: dict[int, Vector2] = {
    0: Vector2(x=0, y=-1),  # NORTH
    1: Vector2(x=1, y=0),   # EAST
    2: Vector2(x=0, y=1),   # SOUTH
    3: Vector2(x=-1, y=0),  # WEST
}
