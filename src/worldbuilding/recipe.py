# Compliance IDs: WORLD-070, WORLD-071, WORLD-072
from __future__ import annotations

from typing import Optional, Any, List, Union
from pydantic import BaseModel, Field, model_validator, field_validator, ConfigDict

from src.worldbuilding.schema import TerrainVariantSpec

# Idea 66 (Region/Place foundational rebuild): the same 7 kinds as
# src/core/state.py's PlaceKind, mirrored here as plain strings since
# content-authoring recipes are Pydantic models, not runtime dataclasses.
PLACE_RECIPE_KINDS = {"CITY", "CAMP", "NEST", "LAIR", "RUIN", "DUNGEON", "LANDMARK"}

# TCK-20260904-CAMPSTATE-PLACE-BRIDGE: Camp + Nest creature races per the
# classification table in docs/mechanics/05_world_evolution.md Sec.6.
CAMP_NEST_CREATURE_RACES = frozenset({"goblin", "orc", "wolf", "spider", "troll", "slime"})


class PlaceRecipeSpec(BaseModel):
    """
    Idea 66: content-authoring declaration of a Place within a region recipe.
    Resolved into a real PlaceState by WorldCompiler.compile() at build time --
    see TCK-20260902-WORLDCOMPILER-PLACE-WIRING. Schema only in this ticket; no
    existing content declares `places:` yet (that is the pilot tickets' job,
    TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT onward).
    """
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(..., min_length=1, description="Unique identifier for the place")
    kind: str = Field(..., description="PlaceKind value: CITY | CAMP | NEST | LAIR | RUIN | DUNGEON | LANDMARK")
    position: tuple[int, int] = Field(..., description="Point location within the parent region's bounds")
    footprint: Optional[tuple[int, int, int, int]] = Field(None, description="Sub-bounds, multi-tile CITY-kind only")
    owner_faction_id: Optional[str] = Field(None, description="Sovereignty override; defaults to the parent region's")
    scale: Optional[float] = Field(None, description="CITY-kind only: settlement size scalar")
    maturity: Optional[float] = Field(None, description="CAMP/NEST-kind: growth-over-time value")
    hazard_level: Optional[float] = Field(None, description="RUIN/DUNGEON-kind: local hazard override")
    creature_kind: Optional[str] = Field(
        None,
        description="CAMP/NEST-kind only: creature race driving CampState.kind "
                    "(goblin/orc/wolf/spider/troll/slime); None for all other kinds "
                    "and for CAMP/NEST content not yet migrated to the world-gen Camp bridge",
    )

    @field_validator("kind")
    @classmethod
    def validate_kind(cls, v: str) -> str:
        upper = v.upper()
        if upper not in PLACE_RECIPE_KINDS:
            raise ValueError(f"kind '{v}' is invalid. Supported: {PLACE_RECIPE_KINDS}")
        return upper

    @field_validator("creature_kind")
    @classmethod
    def validate_creature_kind(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        lower = v.lower()
        if lower not in CAMP_NEST_CREATURE_RACES:
            raise ValueError(f"creature_kind '{v}' is invalid. Supported: {CAMP_NEST_CREATURE_RACES}")
        return lower


class RegionRecipeSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(..., min_length=1, description="Unique identifier for the region")
    type: str = Field(..., min_length=1, description="Ecological type of the region")
    grid_bounds: tuple[int, int, int, int] = Field(..., description="Bounds as [min_x, min_y, max_x, max_y]")
    terrain: Optional[str] = Field("GRASS", description="Terrain type")
    hazard_level: Optional[float] = Field(0.0, description="Hazard difficulty rating")
    hazard_kind: Optional[str] = Field("PHYSICAL", description="Semantic type of this region's passive hazard drain (e.g. 'PHYSICAL', 'NATURAL_TERRAIN', 'TOXIC_GAS').")
    tags: List[str] = Field(default_factory=list, description="Semantic labels for quest routing (e.g. mine, forest, ruins, settlement)")
    terrain_variants: Optional[List[TerrainVariantSpec]] = Field(None, description="Optional set of terrain fill variants for organic in-region terrain; inert until consumed by TCK-20260821-COMPILER-NOISE-FILL")
    places: List[PlaceRecipeSpec] = Field(default_factory=list, description="Idea 66: Places contained within this region. Empty for all existing content -- new, opt-in only.")

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


