# Compliance IDs: WORLD-GEN-001, WORLD-GEN-002
from __future__ import annotations

from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field, ConfigDict


class GenerationIntentSpec(BaseModel):
    """Pydantic specification detailing high-level configuration parameters for procedural generation."""
    model_config = ConfigDict(frozen=True)

    generation_id: str = Field(..., min_length=1, description="Unique generation run identifier")
    seed: int = Field(..., description="Deterministic RNG seed")
    target_world_size: tuple[int, int] = Field((100, 100), description="Target width and height of the map tile area")
    terrain_style: str = Field("temperate", description="Climatic style mapping, e.g. temperate, arid")
    settlement_style: str = Field("scattered", description="Distribution format of regions")
    danger_level: float = Field(1.0, description="Hazard difficulty scalar")
    resource_density: float = Field(0.5, description="Resource node generation density scalar")
    population_scale: float = Field(1.0, description="Entity population generation density scalar")
    required_modules: List[str] = Field(default_factory=list, description="Optional baseline layouts that must be merged")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Custom generation boundaries/constraints")
    budget_profile: str = Field("local_dev", description="Validator budget profile category")
