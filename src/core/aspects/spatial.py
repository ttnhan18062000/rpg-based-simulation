from __future__ import annotations
from pydantic import Field
from src.core.models.base import Aspect
from src.core.models.vectors import Vector2

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


# Rebuild Model to finalize Pydantic setup
SpatialAspect.model_rebuild()
