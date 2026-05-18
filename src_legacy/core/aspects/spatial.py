from __future__ import annotations
from typing import Any
from pydantic import Field, model_validator
from src_legacy.core.models.base import Aspect
from src_legacy.core.models.vectors import Vector2

class SpatialAspect(Aspect):
    """Aspect handling entity position, regions, and leash constraints."""
    pos: Vector2 = Field(default_factory=lambda: Vector2(0, 0))
    region_id: str = ""
    current_region_id: str = ""
    home_pos: Vector2 | None = None
    leash_radius: int = 0
    difficulty_tier: int = 1
    facing: Vector2 = Field(default_factory=lambda: Vector2(0, 1))
    is_hidden: bool = False
    
    # Sensory limits
    vision_range: int = 6
    
    # Movement tracking [Milestone 2]
    moved_this_tick: bool = False

    def on_tick(self, tick: int) -> None:
        """Reset tick-based movement flag."""
        self.moved_this_tick = False

    @model_validator(mode="before")
    @classmethod
    def coerce_vectors(cls, data: Any) -> Any:
        """Harden against dictionary-based position data from scenarios."""
        if isinstance(data, dict):
            if "pos" in data and isinstance(data["pos"], dict):
                data["pos"] = Vector2.from_any(data["pos"])
            if "facing" in data and isinstance(data["facing"], dict):
                data["facing"] = Vector2.from_any(data["facing"])
            if "home_pos" in data and isinstance(data["home_pos"], dict):
                data["home_pos"] = Vector2.from_any(data["home_pos"])
        return data


# Rebuild Model to finalize Pydantic setup
SpatialAspect.model_rebuild()
