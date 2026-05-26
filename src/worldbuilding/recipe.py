# Compliance IDs: WORLD-070, WORLD-071, WORLD-072
from __future__ import annotations

import random
from typing import Optional, Any
from pydantic import BaseModel, Field, model_validator, ConfigDict

from src.worldbuilding.schema import TopologySpec, FactionSpec, WorldSpec, InvalidWorldSpecError
from src.worldbuilding.validator import WorldValidator


class RegionRecipeSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(..., min_length=1, description="Unique identifier for the region")
    type: str = Field(..., min_length=1, description="Ecological type of the region")
    grid_bounds: tuple[int, int, int, int] = Field(..., description="Bounds as [min_x, min_y, max_x, max_y]")
    terrain: Optional[str] = Field("GRASS", description="Terrain type")
    hazard_level: Optional[float] = Field(0.0, description="Hazard difficulty rating")

    @model_validator(mode="after")
    def validate_bounds(self) -> RegionRecipeSpec:
        min_x, min_y, max_x, max_y = self.grid_bounds
        if min_x > max_x:
            raise ValueError(f"Region '{self.id}' bounds min_x ({min_x}) cannot exceed max_x ({max_x})")
        if min_y > max_y:
            raise ValueError(f"Region '{self.id}' bounds min_y ({min_y}) cannot exceed max_y ({max_y})")
        return self


class PopulationRecipeSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    role: str = Field(..., min_length=1, description="Societal role")
    count: int = Field(..., ge=0, description="Number of entities to spawn")
    faction: str = Field(..., min_length=1, description="Faction affiliation")
    spawn_region: Optional[str] = Field(None, description="Optional spawn region")
    spawn_distribution: Optional[dict[str, Any]] = Field(None, description="Optional spawn distribution")
    stats_profile: Optional[str] = Field(None, description="Optional stats attributes template")
    inventory_profile: Optional[str] = Field(None, description="Optional starting items profile")
    cognition_profile: Optional[str] = Field(None, description="Optional memory profiles")


class ResourceRecipeSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    resource_type: str = Field(..., min_length=1, description="Type of resource node")
    count: int = Field(..., gt=0, description="Number of nodes to place")
    region: str = Field(..., min_length=1, description="Target region placement")
    density: Optional[str] = Field(None, description="Resource node placement clustering factor")
    respawn_policy: Optional[str] = Field(None, description="Optional dynamic replenishment behavior")


class BuildingRecipeSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    building_type: str = Field(..., min_length=1, description="Constructed type of the building")
    count: int = Field(..., gt=0, description="Number of buildings to place")
    region: str = Field(..., min_length=1, description="Target region placement")
    service_profile: Optional[str] = Field(None, description="Optional functional profile definition")


class WorldTemplateEntitiesSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    populations: list[PopulationRecipeSpec] = Field(default_factory=list, description="List of population recipes")


class WorldTemplateSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = Field(..., description="Schema version, strictly 'worldtemplate.v1'")
    world_id: str = Field(..., min_length=1, description="Unique world ID")
    name: str = Field(..., min_length=1, description="Descriptive template name")
    description: Optional[str] = Field(None, description="Optional text description")

    topology: TopologySpec
    regions: list[RegionRecipeSpec] = Field(default_factory=list)
    factions: list[FactionSpec] = Field(default_factory=list)
    entities: WorldTemplateEntitiesSpec = Field(default_factory=WorldTemplateEntitiesSpec)
    resources: list[ResourceRecipeSpec] = Field(default_factory=list)
    buildings: list[BuildingRecipeSpec] = Field(default_factory=list)
    quests: list[dict[str, Any]] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_schema_version(self) -> WorldTemplateSpec:
        if self.schema_version != "worldtemplate.v1":
            raise ValueError("schema_version must strictly be 'worldtemplate.v1'")
        return self


class WorldTemplateExpander:
    """
    Deterministic expander that takes a WorldTemplateSpec and expansions recipes
    and returns a fully parsed, validated standard WorldSpec.
    """

    @staticmethod
    def expand(template: WorldTemplateSpec, seed: int) -> WorldSpec:
        """
        Deterministic expansion of WorldTemplateSpec into WorldSpec.
        """
        # Ensure repeatable stable generations using RNG initialized with seed
        rng = random.Random(seed)

        # Base layout data mapping
        expanded_data = {
            "schema_version": "worldspec.v1",
            "world_id": template.world_id,
            "name": template.name,
            "description": template.description,
            "topology": {
                "width": template.topology.width,
                "height": template.topology.height,
                "coordinate_system": template.topology.coordinate_system
            },
            "regions": [],
            "factions": [],
            "entities": [],
            "resources": [],
            "buildings": [],
            "quests": list(template.quests)
        }

        # 1. Expand Regions and validate containment limits
        region_ids = set()
        for reg in template.regions:
            min_x, min_y, max_x, max_y = reg.grid_bounds
            
            # Topological boundary enforcement
            if min_x < 0 or min_y < 0 or max_x >= template.topology.width or max_y >= template.topology.height:
                raise ValueError(
                    f"Region '{reg.id}' bounds {reg.grid_bounds} exceed map topology dimensions "
                    f"[{template.topology.width}x{template.topology.height}]"
                )
            
            region_ids.add(reg.id)
            expanded_data["regions"].append({
                "id": reg.id,
                "type": reg.type,
                "bounds": reg.grid_bounds,
                "terrain": reg.terrain or "GRASS",
                "hazard_level": reg.hazard_level or 0.0
            })

        # 2. Map Factions
        for fac in template.factions:
            expanded_data["factions"].append({
                "id": fac.id,
                "type": fac.type
            })

        # 3. Expand Populations and generate stable IDs
        pop_counts = {}
        for pop in template.entities.populations:
            # Extract spawn region directly or from spawn_distribution nested object
            region = pop.spawn_region
            if not region and pop.spawn_distribution:
                region = pop.spawn_distribution.get("region")
            
            if not region:
                raise ValueError(f"Population recipe for role '{pop.role}' must specify spawn_region or spawn_distribution.region")
            
            if region not in region_ids:
                raise ValueError(f"Population recipe references nonexistent region '{region}'")

            base_key = f"pop_{pop.role}_{pop.faction}_{region}".lower().replace("-", "_")
            if base_key not in pop_counts:
                pop_counts[base_key] = 0
                group_id = base_key
            else:
                pop_counts[base_key] += 1
                group_id = f"{base_key}_{pop_counts[base_key]}"

            expanded_data["entities"].append({
                "id": group_id,
                "count": pop.count,
                "role": pop.role,
                "faction": pop.faction,
                "spawn_region": region
            })

        # 4. Expand Resources and generate stable traceable node list
        res_counts = {}
        for res in template.resources:
            if res.region not in region_ids:
                raise ValueError(f"Resource recipe references nonexistent region '{res.region}'")

            base_key = f"res_{res.resource_type}_{res.region}".lower().replace("-", "_")
            if base_key not in res_counts:
                res_counts[base_key] = 0

            for _ in range(res.count):
                node_id = f"{base_key}_{res_counts[base_key]}"
                res_counts[base_key] += 1

                expanded_data["resources"].append({
                    "id": node_id,
                    "resource_type": res.resource_type,
                    "count": 10,  # Default charges per resource node
                    "region": res.region
                })

        # 5. Expand Buildings
        bld_counts = {}
        for bld in template.buildings:
            if bld.region not in region_ids:
                raise ValueError(f"Building recipe references nonexistent region '{bld.region}'")

            base_key = f"bld_{bld.building_type}_{bld.region}".lower().replace("-", "_")
            if base_key not in bld_counts:
                bld_counts[base_key] = 0

            for _ in range(bld.count):
                bld_id = f"{base_key}_{bld_counts[base_key]}"
                bld_counts[base_key] += 1

                expanded_data["buildings"].append({
                    "id": bld_id,
                    "type": bld.building_type,
                    "region": bld.region
                })

        # Model validation
        try:
            expanded_spec = WorldSpec.model_validate(expanded_data)
        except Exception as e:
            raise InvalidWorldSpecError(f"Expanded spec is structurally invalid: {e}") from e

        # Integrity Validation Rules Check (ensures no rules are bypassed)
        validator = WorldValidator()
        validator.validate(expanded_spec, strict=True)

        return expanded_spec
