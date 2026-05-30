# Compliance IDs: WORLD-CAT-004, WORLD-CAT-005
from __future__ import annotations

import os
import yaml
import hashlib
from typing import Dict, List, Optional, Any, Type, TypeVar
from pydantic import BaseModel

from src.content.schema import (
    CatalogBaseDefinition,
    MaterialDefinition,
    TraitDefinition,
    ThemeDefinition,
    RelationshipAxisDefinition,
    AttributeDefinition,
    ElementDefinition,
    NeedProfileDefinition,
    SenseProfileDefinition,
    BodyModelDefinition,
    DriveProfileDefinition,
    CognitionProfileDefinition,
    StatsProfileDefinition,
    CombatProfileDefinition,
    InventoryProfileDefinition,
    SkillProfileDefinition,
    RaceDefinition,
    FactionDefinition,
    RoleDefinition,
    PerspectiveDefinition,
    FactionRelationshipDefinition,
    EntityArchetypeDefinition,
    PopulationRecipeDefinition,
    LegacyEnemyProjectionDefinition,
    ResourceDefinition,
    BuildingDefinition,
    ServiceProfileDefinition,
    TerrainDefinition,
    SpawnTableDefinition,
    DefaultCompileProfile,
    ItemDefinition,
    RecipeDefinition,
    RuntimeRegionDefinition,
    BiomeDefinition,
    EcologyDefinition,
)

T = TypeVar("T", bound=CatalogBaseDefinition)


class CatalogRepository:
    """
    Thread-safe repository loader that coordinates static catalog schema configuration loading
    from data/content/**/*.yaml. Exposes clean lookup operations.
    """

    def __init__(self, content_dir: str):
        self.content_dir = content_dir
        
        # In-memory indices
        # Foundational
        self.materials: Dict[str, MaterialDefinition] = {}
        self.traits: Dict[str, TraitDefinition] = {}
        self.themes: Dict[str, ThemeDefinition] = {}
        self.relationship_axes: Dict[str, RelationshipAxisDefinition] = {}
        self.attributes: Dict[str, AttributeDefinition] = {}
        self.elements: Dict[str, ElementDefinition] = {}
        
        # Living Profiles
        self.races: Dict[str, RaceDefinition] = {}
        self.need_profiles: Dict[str, NeedProfileDefinition] = {}
        self.sense_profiles: Dict[str, SenseProfileDefinition] = {}
        self.body_models: Dict[str, BodyModelDefinition] = {}
        self.drive_profiles: Dict[str, DriveProfileDefinition] = {}
        self.cognition_profiles: Dict[str, CognitionProfileDefinition] = {}
        
        # Entity Profiles
        self.stats_profiles: Dict[str, StatsProfileDefinition] = {}
        self.combat_profiles: Dict[str, CombatProfileDefinition] = {}
        self.inventory_profiles: Dict[str, InventoryProfileDefinition] = {}
        self.skill_profiles: Dict[str, SkillProfileDefinition] = {}
        self.populations: Dict[str, PopulationRecipeDefinition] = {}
        self.entity_archetypes: Dict[str, EntityArchetypeDefinition] = {}
        
        # Social & Factions
        self.roles: Dict[str, RoleDefinition] = {}
        self.factions: Dict[str, FactionDefinition] = {}
        self.perspectives: Dict[str, PerspectiveDefinition] = {}
        self.faction_relationships: Dict[str, FactionRelationshipDefinition] = {}
        
        # World
        self.buildings: Dict[str, BuildingDefinition] = {}
        self.terrain: Dict[str, TerrainDefinition] = {}
        self.services: Dict[str, ServiceProfileDefinition] = {}
        self.regions: Dict[str, RuntimeRegionDefinition] = {}
        self.recipes: Dict[str, RecipeDefinition] = {}
        self.resources: Dict[str, ResourceDefinition] = {}
        self.items: Dict[str, ItemDefinition] = {}
        self.biomes: Dict[str, BiomeDefinition] = {}
        self.ecologies: Dict[str, EcologyDefinition] = {}
        
        # Legacy Spawns/Defaults
        self.spawn_tables: Dict[str, SpawnTableDefinition] = {}
        self.defaults: Dict[str, DefaultCompileProfile] = {}
        
        # Compatibility Projection
        self.legacy_enemy_projections: Dict[str, LegacyEnemyProjectionDefinition] = {}
        
        # Raw parsed structures for diagnostic/validation tracking
        self.raw_data: Dict[str, List[Dict[str, Any]]] = {}
        self._fingerprint: str = ""
        self._version: str = "2.0.0"

    def load_all(self) -> None:
        """Loads and parses all files under the content directory into structured indices."""
        # 1. Foundation
        self.materials = self._load_file("foundation/materials.yaml", MaterialDefinition)
        self.traits = self._load_file("foundation/traits.yaml", TraitDefinition)
        self.themes = self._load_file("foundation/themes.yaml", ThemeDefinition)
        self.relationship_axes = self._load_file("foundation/relationship_axes.yaml", RelationshipAxisDefinition)
        self.attributes = self._load_file("foundation/attributes.yaml", AttributeDefinition)
        self.elements = self._load_file("foundation/elements.yaml", ElementDefinition)

        # 2. Living
        self.races = self._load_file("living/races.yaml", RaceDefinition)
        self.need_profiles = self._load_file("living/need_profiles.yaml", NeedProfileDefinition)
        self.sense_profiles = self._load_file("living/sense_profiles.yaml", SenseProfileDefinition)
        self.body_models = self._load_file("living/body_models.yaml", BodyModelDefinition)
        self.drive_profiles = self._load_file("living/drive_profiles.yaml", DriveProfileDefinition)
        self.cognition_profiles = self._load_file("living/cognition_profiles.yaml", CognitionProfileDefinition)

        # 3. Social
        self.roles = self._load_file("social/roles.yaml", RoleDefinition)
        self.factions = self._load_file("social/factions.yaml", FactionDefinition)
        self.perspectives = self._load_file("social/perspectives.yaml", PerspectiveDefinition)
        self.faction_relationships = self._load_file("social/faction_relationships.yaml", FactionRelationshipDefinition)

        # 4. Entities
        self.stats_profiles = self._load_file("entities/stat_profiles.yaml", StatsProfileDefinition)
        self.combat_profiles = self._load_file("entities/combat_profiles.yaml", CombatProfileDefinition)
        self.inventory_profiles = self._load_file("entities/inventory_profiles.yaml", InventoryProfileDefinition)
        self.skill_profiles = self._load_file("entities/skill_profiles.yaml", SkillProfileDefinition)
        self.populations = self._load_file("entities/populations.yaml", PopulationRecipeDefinition)
        self.entity_archetypes = self._load_file("entities/entity_archetypes.yaml", EntityArchetypeDefinition)

        # 5. World
        self.buildings = self._load_file("world/buildings.yaml", BuildingDefinition)
        self.terrain = self._load_file("world/terrain.yaml", TerrainDefinition)
        self.services = self._load_file("world/services.yaml", ServiceProfileDefinition)
        self.regions = self._load_file("world/runtime_regions.yaml", RuntimeRegionDefinition)
        self.recipes = self._load_file("world/recipes.yaml", RecipeDefinition)
        self.resources = self._load_file("world/resources.yaml", ResourceDefinition)
        self.items = self._load_file("world/items.yaml", ItemDefinition)
        self.biomes = self._load_file("world/biomes.yaml", BiomeDefinition)
        self.ecologies = self._load_file("world/ecologies.yaml", EcologyDefinition)

        # 6. Legacy / Defaults
        self.spawn_tables = self._load_file("spawn_tables.yaml", SpawnTableDefinition)
        self.defaults = self._load_file("defaults.yaml", DefaultCompileProfile)

        # 7. Compatibility
        self.legacy_enemy_projections = self._load_file("compatibility/legacy_enemy_projection.yaml", LegacyEnemyProjectionDefinition)

        # Generate unique content fingerprint
        self._compute_fingerprint()

    def _load_file(self, filename: str, model_cls: Type[T]) -> Dict[str, T]:
        """Helper to read, load, and validate definitions from a target yaml file."""
        filepath = os.path.join(self.content_dir, filename)
        if not os.path.exists(filepath):
            return {}

        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            return {}

        # The yaml must contain a list of definitions under a root key or directly as a list/dict
        if isinstance(data, dict):
            items = data.get("items", []) or list(data.values())
        elif isinstance(data, list):
            items = data
        else:
            raise ValueError(f"Catalog file {filename} must contain a list or map of definitions")

        results: Dict[str, T] = {}
        self.raw_data[filename] = items

        for item in items:
            if not isinstance(item, dict) or "id" not in item:
                raise ValueError(f"Definition in {filename} is malformed or missing 'id'")
            
            def_id = item["id"]
            if def_id in results:
                raise ValueError(f"Duplicate definition ID '{def_id}' found in {filename}")

            validated = model_cls(**item)
            results[def_id] = validated

        return results

    def _compute_fingerprint(self) -> None:
        """Deterministically generates a hash signature of the active catalog repository data."""
        sha = hashlib.sha256()
        for filename in sorted(self.raw_data.keys()):
            sha.update(filename.encode("utf-8"))
            items = self.raw_data[filename]
            # Convert dict keys deterministically to string representations
            serialized = str(sorted(str(sorted(d.items())) for d in items if isinstance(d, dict)))
            sha.update(serialized.encode("utf-8"))
        self._fingerprint = sha.hexdigest()

    # Read-only Lookup API
    def get_material(self, def_id: str) -> Optional[MaterialDefinition]:
        return self.materials.get(def_id)

    def get_trait(self, def_id: str) -> Optional[TraitDefinition]:
        return self.traits.get(def_id)

    def get_theme(self, def_id: str) -> Optional[ThemeDefinition]:
        return self.themes.get(def_id)

    def get_relationship_axis(self, def_id: str) -> Optional[RelationshipAxisDefinition]:
        return self.relationship_axes.get(def_id)

    def get_attribute(self, def_id: str) -> Optional[AttributeDefinition]:
        return self.attributes.get(def_id)

    def get_element(self, def_id: str) -> Optional[ElementDefinition]:
        return self.elements.get(def_id)

    def get_race(self, def_id: str) -> Optional[RaceDefinition]:
        return self.races.get(def_id)

    def get_need_profile(self, def_id: str) -> Optional[NeedProfileDefinition]:
        return self.need_profiles.get(def_id)

    def get_sense_profile(self, def_id: str) -> Optional[SenseProfileDefinition]:
        return self.sense_profiles.get(def_id)

    def get_body_model(self, def_id: str) -> Optional[BodyModelDefinition]:
        return self.body_models.get(def_id)

    def get_drive_profile(self, def_id: str) -> Optional[DriveProfileDefinition]:
        return self.drive_profiles.get(def_id)

    def get_cognition_profile(self, def_id: str) -> Optional[CognitionProfileDefinition]:
        return self.cognition_profiles.get(def_id)

    def get_stats_profile(self, def_id: str) -> Optional[StatsProfileDefinition]:
        return self.stats_profiles.get(def_id)

    def get_combat_profile(self, def_id: str) -> Optional[CombatProfileDefinition]:
        return self.combat_profiles.get(def_id)

    def get_inventory_profile(self, def_id: str) -> Optional[InventoryProfileDefinition]:
        return self.inventory_profiles.get(def_id)

    def get_skill_profile(self, def_id: str) -> Optional[SkillProfileDefinition]:
        return self.skill_profiles.get(def_id)

    def get_population_recipe(self, def_id: str) -> Optional[PopulationRecipeDefinition]:
        return self.populations.get(def_id)

    def get_entity_archetype(self, def_id: str) -> Optional[EntityArchetypeDefinition]:
        return self.entity_archetypes.get(def_id)

    def get_role(self, def_id: str) -> Optional[RoleDefinition]:
        return self.roles.get(def_id)

    def get_faction(self, def_id: str) -> Optional[FactionDefinition]:
        return self.factions.get(def_id)

    def get_perspective(self, def_id: str) -> Optional[PerspectiveDefinition]:
        return self.perspectives.get(def_id)

    def get_faction_relationship(self, def_id: str) -> Optional[FactionRelationshipDefinition]:
        return self.faction_relationships.get(def_id)

    def get_building(self, def_id: str) -> Optional[BuildingDefinition]:
        return self.buildings.get(def_id)

    def get_terrain(self, def_id: str) -> Optional[TerrainDefinition]:
        return self.terrain.get(def_id)

    def get_service_profile(self, def_id: str) -> Optional[ServiceProfileDefinition]:
        return self.services.get(def_id)

    def get_region(self, def_id: str) -> Optional[RuntimeRegionDefinition]:
        return self.regions.get(def_id)

    def get_recipe(self, def_id: str) -> Optional[RecipeDefinition]:
        return self.recipes.get(def_id)

    def get_resource(self, def_id: str) -> Optional[ResourceDefinition]:
        return self.resources.get(def_id)

    def get_item(self, def_id: str) -> Optional[ItemDefinition]:
        return self.items.get(def_id)

    def get_biome(self, def_id: str) -> Optional[BiomeDefinition]:
        return self.biomes.get(def_id)

    def get_ecology(self, def_id: str) -> Optional[EcologyDefinition]:
        return self.ecologies.get(def_id)

    def get_spawn_table(self, def_id: str) -> Optional[SpawnTableDefinition]:
        return self.spawn_tables.get(def_id)

    def get_default_profile(self, def_id: str) -> Optional[DefaultCompileProfile]:
        return self.defaults.get(def_id)

    def get_legacy_enemy_projection(self, def_id: str) -> Optional[LegacyEnemyProjectionDefinition]:
        return self.legacy_enemy_projections.get(def_id)

    # Repository Metadata Queries
    def get_all_ids_by_type(self, type_name: str) -> List[str]:
        mapping = {
            "material": self.materials,
            "trait": self.traits,
            "theme": self.themes,
            "relationship_axis": self.relationship_axes,
            "attribute": self.attributes,
            "element": self.elements,
            "race": self.races,
            "need_profile": self.need_profiles,
            "sense_profile": self.sense_profiles,
            "body_model": self.body_models,
            "drive_profile": self.drive_profiles,
            "cognition_profile": self.cognition_profiles,
            "stats_profile": self.stats_profiles,
            "combat_profile": self.combat_profiles,
            "inventory_profile": self.inventory_profiles,
            "skill_profile": self.skill_profiles,
            "population": self.populations,
            "entity_archetype": self.entity_archetypes,
            "role": self.roles,
            "faction": self.factions,
            "perspective": self.perspectives,
            "faction_relationship": self.faction_relationships,
            "building": self.buildings,
            "terrain": self.terrain,
            "service_profile": self.services,
            "region": self.regions,
            "recipe": self.recipes,
            "resource": self.resources,
            "item": self.items,
            "biome": self.biomes,
            "ecology": self.ecologies,
            "spawn_table": self.spawn_tables,
            "defaults": self.defaults,
            "legacy_enemy_projection": self.legacy_enemy_projections,
        }
        return list(mapping.get(type_name.lower(), {}).keys())

    def get_deprecated_ids(self) -> Dict[str, List[str]]:
        deprecated_map: Dict[str, List[str]] = {}
        for cat_name, registry in [
            ("material", self.materials),
            ("trait", self.traits),
            ("theme", self.themes),
            ("relationship_axis", self.relationship_axes),
            ("attribute", self.attributes),
            ("element", self.elements),
            ("race", self.races),
            ("need_profile", self.need_profiles),
            ("sense_profile", self.sense_profiles),
            ("body_model", self.body_models),
            ("drive_profile", self.drive_profiles),
            ("cognition_profile", self.cognition_profiles),
            ("stats_profile", self.stats_profiles),
            ("combat_profile", self.combat_profiles),
            ("inventory_profile", self.inventory_profiles),
            ("skill_profile", self.skill_profiles),
            ("population", self.populations),
            ("entity_archetype", self.entity_archetypes),
            ("role", self.roles),
            ("faction", self.factions),
            ("perspective", self.perspectives),
            ("faction_relationship", self.faction_relationships),
            ("building", self.buildings),
            ("terrain", self.terrain),
            ("service_profile", self.services),
            ("region", self.regions),
            ("recipe", self.recipes),
            ("resource", self.resources),
            ("item", self.items),
            ("biome", self.biomes),
            ("ecology", self.ecologies),
            ("spawn_table", self.spawn_tables),
            ("defaults", self.defaults),
            ("legacy_enemy_projection", self.legacy_enemy_projections),
        ]:
            deprecated_map[cat_name] = [item_id for item_id, obj in registry.items() if obj.deprecated]
        return deprecated_map

    @property
    def fingerprint(self) -> str:
        return self._fingerprint

    @property
    def version(self) -> str:
        return self._version
