"""Historical legacy objects."""
from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.models import Vector2

@dataclass(slots=True)
class Monument:
    monument_id: str
    hero_name: str
    hero_class: str
    level: int
    pos: Vector2
    buff_type: str
    buff_value: float
