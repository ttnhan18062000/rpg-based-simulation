# Compliance IDs: WORLD-050, WORLD-051, WORLD-052
from src.worldbuilding.schema import (
    InvalidWorldSpecError,
    TopologySpec,
    RegionSpec,
    FactionSpec,
    PopulationSpec,
    ResourceNodeSpec,
    BuildingSpec,
    ValidationSpec,
    WorldSpec,
    load_world_spec_from_yaml
)
from src.worldbuilding.repository import (
    WorldRepository,
    WorldRepositoryError
)
from src.worldbuilding.validator import (
    WorldValidator,
    ValidationIssue,
    WorldValidationRule
)
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.recipe import (
    RegionRecipeSpec,
    PopulationRecipeSpec,
    ResourceRecipeSpec,
    BuildingRecipeSpec,
    WorldTemplateSpec,
    WorldTemplateExpander
)

__all__ = [
    "InvalidWorldSpecError",
    "TopologySpec",
    "RegionSpec",
    "FactionSpec",
    "PopulationSpec",
    "ResourceNodeSpec",
    "BuildingSpec",
    "ValidationSpec",
    "WorldSpec",
    "load_world_spec_from_yaml",
    "WorldRepository",
    "WorldRepositoryError",
    "WorldValidator",
    "ValidationIssue",
    "WorldValidationRule",
    "WorldCompiler",
    "RegionRecipeSpec",
    "PopulationRecipeSpec",
    "ResourceRecipeSpec",
    "BuildingRecipeSpec",
    "WorldTemplateSpec",
    "WorldTemplateExpander"
]




