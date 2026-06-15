# Compliance IDs: WORLD-MOD-001, WORLD-MOD-002, WORLD-MOD-003
from __future__ import annotations

from typing import Optional, Any, Dict, List, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

from src.worldbuilding.recipe import (
    RegionRecipeSpec,
    PopulationRecipeSpec,
    ResourceRecipeSpec,
    BuildingRecipeSpec,
)


class ModuleParameterSpec(BaseModel):
    """Configuration parameter exposed by a module for customization."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(..., min_length=1, description="Variable parameter identifier")
    type: str = Field(..., description="Primitive parameter type")
    default: Optional[Any] = Field(None, description="Optional default value")
    required: bool = Field(False, description="Whether supplying this parameter is mandatory")
    allowed_values: Optional[List[Any]] = Field(None, description="Enumerated range of valid values")
    min_value: Optional[Union[int, float]] = Field(None, description="Minimum numeric limit")
    max_value: Optional[Union[int, float]] = Field(None, description="Maximum numeric limit")
    description: Optional[str] = Field(None, description="Parameter intent explanation")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        valid_types = {"string", "integer", "float", "boolean", "enum", "id_reference"}
        if v.lower() not in valid_types:
            raise ValueError(f"Type '{v}' is invalid. Supported types: {valid_types}")
        return v.lower()

    @model_validator(mode="after")
    def validate_parameter_spec(self) -> ModuleParameterSpec:
        # Validate allowed value boundaries against default if configured
        if self.default is not None and self.allowed_values is not None:
            if self.default not in self.allowed_values:
                raise ValueError(f"Default value '{self.default}' must reside within allowed_values list.")
        return self


REGISTERED_MODULE_TYPES = {"terrain", "settlement", "ecology", "economy", "conflict", "population", "danger_zone"}


class WorldModuleSpec(BaseModel):
    """Pydantic model representing a reusable structural world building module configuration."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Optional[str] = Field(None, description="Module schema identifier (optional human-readable label)")
    module_id: str = Field(..., min_length=1, description="Unique module identifier")
    module_type: str = Field(..., description="The functional type category of the module")
    display_name: str = Field(..., min_length=1, description="User friendly display name")
    description: Optional[str] = Field(None, description="Description of layout contribution")
    version: str = Field("1.0.0", description="Semver identifier")

    # Dependency boundaries
    requires: List[str] = Field(default_factory=list, description="IDs of other modules required by this module")
    provides: List[str] = Field(default_factory=list, description="List of semantic aliases provided")

    # Exposed settings schema
    parameters: List[ModuleParameterSpec] = Field(default_factory=list, description="Exposed configurable variables")

    # Partial structural contributions
    regions: List[RegionRecipeSpec] = Field(default_factory=list, description="Associated region layout recipes")
    population_recipes: List[PopulationRecipeSpec] = Field(default_factory=list, description="Entity spawning recipes")
    resource_recipes: List[ResourceRecipeSpec] = Field(default_factory=list, description="Resource node recipes")
    building_recipes: List[BuildingRecipeSpec] = Field(default_factory=list, description="Building construct recipes")
    observability_tags: List[str] = Field(default_factory=list, description="Structural audit tags")

    # v2 layout contributions
    biomes: List[str] = Field(default_factory=list, description="Biome layout templates")
    ecologies: List[str] = Field(default_factory=list, description="Ecology layout templates")
    populations: List[str] = Field(default_factory=list, description="Population template specs")
    relationships: List[str] = Field(default_factory=list, description="Relationship layout definitions")
    resources: Union[Dict[str, int], List[Any]] = Field(default_factory=list, description="Resource node layout rules")
    buildings: Union[Dict[str, int], List[Any]] = Field(default_factory=list, description="Building layout templates")
    services: Union[Dict[str, int], List[Any]] = Field(default_factory=list, description="Service layout templates")
    factions: List[str] = Field(default_factory=list, description="Associated factions list")

    @classmethod
    def register_module_type(cls, module_type: str) -> None:
        REGISTERED_MODULE_TYPES.add(module_type.lower())

    @field_validator("module_type")
    @classmethod
    def validate_module_type(cls, v: str) -> str:
        if v.lower() not in REGISTERED_MODULE_TYPES:
            raise ValueError(f"module_type '{v}' is invalid. Supported: {REGISTERED_MODULE_TYPES}")
        return v.lower()
