# Compliance IDs: WORLD-050, WORLD-051, WORLD-052
from __future__ import annotations

import yaml
from pathlib import Path
from typing import Optional, Any, Dict, List, Literal
from pydantic import BaseModel, Field, model_validator, field_validator, ConfigDict, ValidationError

class InvalidWorldSpecError(Exception):
    """Custom exception raised when a world specification is malformed or invalid."""
    pass

class TopologySpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    width: int = Field(..., gt=0, description="Width of the map topology")
    height: int = Field(..., gt=0, description="Height of the map topology")
    coordinate_system: str = Field(..., description="Coordinate system style, strictly 'grid'")

    @field_validator("coordinate_system")
    @classmethod
    def validate_coordinate_system(cls, v: str) -> str:
        if v != "grid":
            raise ValueError("coordinate_system must strictly be 'grid'")
        return v

class RegionSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(..., min_length=1, description="Unique identifier for the region")
    type: str = Field(..., min_length=1, description="Atmospheric or ecological type of the region")
    bounds: tuple[int, int, int, int] = Field(..., description="Bounds of the region as [min_x, min_y, max_x, max_y]")
    terrain: Optional[str] = Field("GRASS", description="Ecological terrain type of the region")
    hazard_level: Optional[float] = Field(0.0, description="Hazard difficulty factor of the region")
    hazard_kind: Optional[str] = Field("PHYSICAL", description="Semantic type of this region's passive hazard drain (e.g. 'PHYSICAL', 'NATURAL_TERRAIN', 'TOXIC_GAS').")
    tags: List[str] = Field(default_factory=list, description="Semantic labels for quest routing (e.g. mine, forest, ruins, settlement)")

    @model_validator(mode="after")
    def validate_bounds(self) -> RegionSpec:
        min_x, min_y, max_x, max_y = self.bounds
        if min_x > max_x:
            raise ValueError(f"Region '{self.id}' bounds min_x ({min_x}) cannot be greater than max_x ({max_x})")
        if min_y > max_y:
            raise ValueError(f"Region '{self.id}' bounds min_y ({min_y}) cannot be greater than max_y ({max_y})")
        return self

class FactionSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(..., min_length=1, description="Unique identifier for the faction")
    type: str = Field(..., min_length=1, description="Architectural or behavior type of the faction")

class PopulationSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(..., min_length=1, description="Unique population category identifier")
    count: int = Field(..., ge=0, description="Initial count of entities in this population group")
    role: str = Field(..., min_length=1, description="Combat or societal role of the entities")
    faction: str = Field(..., min_length=1, description="Faction affiliation")
    spawn_region: str = Field(..., min_length=1, description="Region where entities are spawned")
    archetype_id: Optional[str] = Field(
        default=None,
        description="Archetype that originated this population entry; set at assembly time, never inferred from the id string."
    )

class ResourceNodeSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(..., min_length=1, description="Unique resource node identifier")
    resource_type: str = Field(..., min_length=1, description="Resource item type spawned")
    count: int = Field(..., gt=0, description="Total resource charges / stock available")
    region: str = Field(..., min_length=1, description="Region where this node resides")
    regen_rate: int = Field(1, ge=0, description="Charges regenerated per ecology cycle (0 = static node)")

class BuildingSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(..., min_length=1, description="Unique building identifier")
    type: str = Field(..., min_length=1, description="Building construction category")
    region: str = Field(..., min_length=1, description="Region containing this building")

class BudgetSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    max_entities: Optional[int] = Field(None, ge=0, description="Maximum total entities allowed")
    max_regions: Optional[int] = Field(None, ge=0, description="Maximum total regions allowed")
    max_resource_nodes: Optional[int] = Field(None, ge=0, description="Maximum total resource nodes allowed")
    max_buildings: Optional[int] = Field(None, ge=0, description="Maximum total buildings allowed")
    max_expected_artifact_mb: Optional[float] = Field(None, ge=0.0, description="Maximum expected artifact size in MB")

class ValidationSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    expected_min_entities: int = Field(1, ge=0, description="Ceiling check for combined entity populations")
    allow_overlapping_regions: bool = Field(False, description="Whether regional overlap is tolerated")

class QuestDefinition(BaseModel):
    """Authoring-time blueprint for a procedural quest seed. Not a runtime quest instance."""
    model_config = ConfigDict(frozen=True)

    id: str = Field(..., min_length=1, description="Unique identifier for this quest definition")
    type: Literal["escort", "hunt", "fetch", "explore", "defend", "investigate"] = Field(
        ..., description="Quest archetype category"
    )
    required_participant_tags: List[str] = Field(
        default_factory=list,
        description="Entity tags that must exist in the world (e.g. ['hostile', 'humanoid'])"
    )
    required_location_tags: List[str] = Field(
        default_factory=list,
        description="Region/biome tags required (e.g. ['wilderness', 'dungeon'])"
    )
    reward_budget: int = Field(100, ge=0, description="Relative reward weight for downstream generation")
    procedural_hints: Dict[str, Any] = Field(
        default_factory=dict,
        description="Open-ended dict for procedural signals (difficulty, escalation, etc.)"
    )
    tags: List[str] = Field(default_factory=list, description="Freeform tags for filtering and module scoring")
    source_module: Optional[str] = Field(
        None, description="Set by assembly resolver at composition time; not authored directly"
    )


class WorldSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = Field(..., description="Schema version specification, strictly 'worldspec.v1'")
    world_id: str = Field(..., min_length=1, description="Unique world identifier")
    name: str = Field(..., min_length=1, description="Descriptive world name")
    description: Optional[str] = Field(None, description="Optional brief description of the world topology")

    topology: TopologySpec
    regions: list[RegionSpec] = Field(default_factory=list)
    factions: list[FactionSpec] = Field(default_factory=list)
    entities: list[PopulationSpec] = Field(default_factory=list)
    resources: list[ResourceNodeSpec] = Field(default_factory=list)
    buildings: list[BuildingSpec] = Field(default_factory=list)
    quest_definitions: List[QuestDefinition] = Field(
        default_factory=list,
        description="Authoring-time quest blueprints contributed by modules and compositions"
    )
    validation: ValidationSpec = Field(default_factory=ValidationSpec)
    budgets: Optional[BudgetSpec] = Field(None, description="Optional resource limits and budget controls")

    @model_validator(mode="before")
    @classmethod
    def _migrate_quests_field(cls, values: Any) -> Any:
        """Migrate legacy `quests` key to `quest_definitions` with no silent data loss."""
        if isinstance(values, dict) and "quests" in values and "quest_definitions" not in values:
            values["quest_definitions"] = values.pop("quests")
        return values

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, v: str) -> str:
        if v != "worldspec.v1":
            raise ValueError("schema_version must strictly be 'worldspec.v1'")
        return v

    @model_validator(mode="after")
    def validate_unique_identifiers(self) -> WorldSpec:
        # 1. Regions
        region_ids = set()
        for r in self.regions:
            if r.id in region_ids:
                raise ValueError(f"Duplicate region ID found: '{r.id}'")
            region_ids.add(r.id)

        # 2. Factions
        faction_ids = set()
        for f in self.factions:
            if f.id in faction_ids:
                raise ValueError(f"Duplicate faction ID found: '{f.id}'")
            faction_ids.add(f.id)

        # 3. Entities (populations)
        entity_ids = set()
        for e in self.entities:
            if e.id in entity_ids:
                raise ValueError(f"Duplicate population group ID found: '{e.id}'")
            entity_ids.add(e.id)

        # 4. Resources
        resource_ids = set()
        for res in self.resources:
            if res.id in resource_ids:
                raise ValueError(f"Duplicate resource node ID found: '{res.id}'")
            resource_ids.add(res.id)

        # 5. Buildings
        building_ids = set()
        for b in self.buildings:
            if b.id in building_ids:
                raise ValueError(f"Duplicate building ID found: '{b.id}'")
            building_ids.add(b.id)

        return self

def load_world_spec_from_yaml(file_path: str | Path) -> WorldSpec:
    """
    Safely opens a YAML file, loads it as a dictionary, and validates it against
    the WorldSpec schema. Raises InvalidWorldSpecError on schema or reading failures.
    """
    path = Path(file_path)
    if not path.is_file():
        raise InvalidWorldSpecError(f"World specification file not found: {file_path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        raise InvalidWorldSpecError(f"Failed to read or parse YAML file: {e}") from e

    if data is None:
        raise InvalidWorldSpecError("World specification file is empty")

    try:
        return WorldSpec.model_validate(data)
    except ValidationError as e:
        # Extract a clean, readable error summary from Pydantic
        errors_summary = []
        for error in e.errors():
            loc = ".".join(str(x) for x in error["loc"])
            msg = error["msg"]
            errors_summary.append(f"Field '{loc}': {msg}")
        joined_errors = "; ".join(errors_summary)
        raise InvalidWorldSpecError(f"WorldSpec validation failed: {joined_errors}") from e
