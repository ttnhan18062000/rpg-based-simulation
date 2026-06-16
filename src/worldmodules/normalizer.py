from dataclasses import dataclass
from typing import Optional, List, Any, Dict, Tuple, Union

from src.worldmodules.schema import ModuleParameterSpec, WorldModuleSpec
from src.worldbuilding.recipe import (
    RegionRecipeSpec,
    PopulationRecipeSpec,
    ResourceRecipeSpec,
    BuildingRecipeSpec,
)
from src.worldbuilding.schema import QuestDefinition


class NormalizationError(ValueError):
    """Raised when a module field cannot be normalized to a typed ref collection."""


@dataclass(frozen=True)
class NormalizedWorldModule:
    """Stable internal representation of a world module contribution."""
    module_id: str
    module_type: str
    display_name: str
    description: Optional[str]
    version: str
    requires: List[str]
    provides: List[str]
    parameters: List[ModuleParameterSpec]
    regions: List[RegionRecipeSpec]
    population_recipes: List[PopulationRecipeSpec]
    resource_recipes: List[ResourceRecipeSpec]
    building_recipes: List[BuildingRecipeSpec]
    biome_refs: Tuple[str, ...]
    ecology_refs: Tuple[str, ...]
    population_refs: Tuple[str, ...]
    relationship_refs: Tuple[str, ...]
    resources: Dict[str, int]
    buildings: Dict[str, int]
    services: Dict[str, int]
    factions: List[str]
    quest_definitions: Tuple[QuestDefinition, ...]


def _normalize_ref_list(value: List[Any], *, field_name: str) -> Tuple[str, ...]:
    """
    Normalize a raw ref list to an immutable tuple of string IDs.
    - List[str]: validate no duplicates, return as tuple.
    - List[dict] with 'id' key: extract IDs, validate no duplicates, return as tuple.
    - List[dict] without 'id' key: raise NormalizationError.
    - Other element types: raise NormalizationError.
    """
    seen: set = set()
    result: list = []
    for item in value:
        if isinstance(item, str):
            item_id = item
        elif isinstance(item, dict):
            item_id = item.get("id")
            if not item_id or not isinstance(item_id, str):
                raise NormalizationError(
                    f"Dict entry in '{field_name}' has no valid 'id' key: {item!r}"
                )
        else:
            raise NormalizationError(
                f"Unexpected element type {type(item).__name__!r} in '{field_name}': {item!r}"
            )
        if item_id in seen:
            raise NormalizationError(
                f"Duplicate ref '{item_id}' in '{field_name}' is rejected."
            )
        seen.add(item_id)
        result.append(item_id)
    return tuple(result)


def normalize_count_map(value: Any, *, field_name: str) -> Dict[str, int]:
    """Helper to convert resource/building/service list or dict to count dict, validating bounds."""
    if isinstance(value, dict):
        res = {}
        for k, v in value.items():
            if not isinstance(k, str):
                raise ValueError(f"Non-string key '{k}' rejected in {field_name}.")
            if not isinstance(v, int) or isinstance(v, bool):
                raise ValueError(f"Count for '{k}' must be an integer in {field_name}.")
            if v <= 0:
                raise ValueError(f"Non-positive count {v} for '{k}' rejected in {field_name}.")
            res[k] = v
        return res
    elif isinstance(value, list):
        res = {}
        seen = set()
        for item in value:
            # Handle list elements which could be simple strings or dictionaries/objects
            if isinstance(item, str):
                if item in seen:
                    raise ValueError(f"Duplicate list value '{item}' in {field_name} is rejected.")
                seen.add(item)
                res[item] = 1
            elif isinstance(item, dict):
                # If it's a dict representing a recipe, try to get key/count
                # e.g. {"resource_type": "wood_node", "count": 2}
                # But if it's just raw dict-based refs, evaluate:
                item_id = item.get("resource_type") or item.get("building_type") or item.get("service_type") or item.get("id")
                if not item_id or not isinstance(item_id, str):
                    raise ValueError(f"Invalid item reference in {field_name}: {item}")
                if item_id in seen:
                    raise ValueError(f"Duplicate value '{item_id}' in {field_name} is rejected.")
                seen.add(item_id)
                count = item.get("count", 1)
                if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
                    raise ValueError(f"Non-positive count {count} for '{item_id}' rejected in {field_name}.")
                res[item_id] = count
            else:
                # Fallback for typed objects with attributes
                item_id = getattr(item, "resource_type", None) or getattr(item, "building_type", None) or getattr(item, "id", None)
                if not item_id or not isinstance(item_id, str):
                    raise ValueError(f"Invalid item reference in {field_name}: {item}")
                if item_id in seen:
                    raise ValueError(f"Duplicate value '{item_id}' in {field_name} is rejected.")
                seen.add(item_id)
                count = getattr(item, "count", 1)
                if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
                    raise ValueError(f"Non-positive count {count} for '{item_id}' rejected in {field_name}.")
                res[item_id] = count
        return res
    else:
        raise TypeError(f"Expected dict or list for {field_name}, got {type(value)}")


class WorldModuleAuthoringNormalizer:
    """Normalizes raw WorldModuleSpec versions (v1, v2) into a unified internal model."""

    @staticmethod
    def normalize(spec: WorldModuleSpec) -> NormalizedWorldModule:
        return NormalizedWorldModule(
            module_id=spec.module_id,
            module_type=spec.module_type,
            display_name=spec.display_name,
            description=spec.description,
            version=spec.version,
            requires=list(spec.requires),
            provides=list(spec.provides),
            parameters=list(spec.parameters),
            regions=list(spec.regions),
            population_recipes=list(spec.population_recipes),
            resource_recipes=list(spec.resource_recipes),
            building_recipes=list(spec.building_recipes),
            biome_refs=_normalize_ref_list(list(spec.biomes), field_name="biomes"),
            ecology_refs=_normalize_ref_list(list(spec.ecologies), field_name="ecologies"),
            population_refs=_normalize_ref_list(list(spec.populations), field_name="populations"),
            relationship_refs=_normalize_ref_list(list(spec.relationships), field_name="relationships"),
            resources=normalize_count_map(spec.resources, field_name="resources"),
            buildings=normalize_count_map(spec.buildings, field_name="buildings"),
            services=normalize_count_map(spec.services, field_name="services"),
            factions=list(spec.factions),
            quest_definitions=tuple(spec.quest_definitions),
        )
