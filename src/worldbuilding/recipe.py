# Compliance IDs: WORLD-070, WORLD-071, WORLD-072
from __future__ import annotations

from typing import Optional, Any, List, Union
from pydantic import BaseModel, Field, model_validator, ConfigDict


class RegionRecipeSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(..., min_length=1, description="Unique identifier for the region")
    type: str = Field(..., min_length=1, description="Ecological type of the region")
    grid_bounds: tuple[int, int, int, int] = Field(..., description="Bounds as [min_x, min_y, max_x, max_y]")
    terrain: Optional[str] = Field("GRASS", description="Terrain type")
    hazard_level: Optional[float] = Field(0.0, description="Hazard difficulty rating")
    hazard_kind: Optional[str] = Field("PHYSICAL", description="Semantic type of this region's passive hazard drain (e.g. 'PHYSICAL', 'NATURAL_TERRAIN', 'TOXIC_GAS').")
    tags: List[str] = Field(default_factory=list, description="Semantic labels for quest routing (e.g. mine, forest, ruins, settlement)")

    @model_validator(mode="after")
    def validate_bounds(self) -> RegionRecipeSpec:
        min_x, min_y, max_x, max_y = self.grid_bounds
        if min_x > max_x:
            raise ValueError(f"Region '{self.id}' bounds min_x ({min_x}) cannot exceed max_x ({max_x})")
        if min_y > max_y:
            raise ValueError(f"Region '{self.id}' bounds min_y ({min_y}) cannot exceed max_y ({max_y})")
        return self


class PopulationRecipeSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    role: str = Field(..., min_length=1, description="Societal role")
    count: Union[int, str] = Field(..., description="Number of entities to spawn; may be a parameter template expression")
    faction: str = Field(..., min_length=1, description="Faction affiliation")

    @model_validator(mode="after")
    def _validate_count(self) -> "PopulationRecipeSpec":
        if isinstance(self.count, int) and self.count < 0:
            raise ValueError("count must be >= 0")
        return self
    spawn_region: Optional[str] = Field(None, description="Optional spawn region")
    spawn_distribution: Optional[dict[str, Any]] = Field(None, description="Optional spawn distribution")
    stats_profile: Optional[str] = Field(None, description="Optional stats attributes template")
    inventory_profile: Optional[str] = Field(None, description="Optional starting items profile")
    cognition_profile: Optional[str] = Field(None, description="Optional memory profiles")


class ResourceRecipeSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    resource_type: str = Field(..., min_length=1, description="Type of resource node")
    count: Union[int, str] = Field(..., description="Number of nodes to place; may be a parameter template expression")
    region: str = Field(..., min_length=1, description="Target region placement")

    @model_validator(mode="after")
    def _validate_count(self) -> "ResourceRecipeSpec":
        if isinstance(self.count, int) and self.count <= 0:
            raise ValueError("count must be > 0")
        return self
    density: Optional[str] = Field(None, description="Resource node placement clustering factor")
    respawn_policy: Optional[str] = Field(None, description="Optional dynamic replenishment behavior")


class BuildingRecipeSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    building_type: str = Field(..., min_length=1, description="Constructed type of the building")
    count: Union[int, str] = Field(..., description="Number of buildings to place; may be a parameter template expression")
    region: str = Field(..., min_length=1, description="Target region placement")

    @model_validator(mode="after")
    def _validate_count(self) -> "BuildingRecipeSpec":
        if isinstance(self.count, int) and self.count <= 0:
            raise ValueError("count must be > 0")
        return self
    service_profile: Optional[str] = Field(None, description="Optional functional profile definition")


