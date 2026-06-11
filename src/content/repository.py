# Compliance IDs: WORLD-CAT-004, WORLD-CAT-005
from __future__ import annotations

import os
import yaml
import hashlib
from dataclasses import dataclass
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


@dataclass(frozen=True)
class ContentFamilySpec:
    family: str
    path: str
    schema: Type[BaseModel]
    repository_index: str
    required: bool = True
    state_policy: str = "active"


@dataclass
class CatalogLoadReport:
    loaded_families: List[str]
    loaded_files: List[str]
    record_counts: Dict[str, int]
    missing_required_files: List[str]
    missing_optional_files: List[str]
    ignored_files: List[str]
    duplicate_ids: List[str]
    schema_errors: Dict[str, Any]
    fingerprint: str


CANONICAL_FAMILIES: List[ContentFamilySpec] = [
    # 1. Foundation
    ContentFamilySpec("foundation.materials", "foundation/materials.yaml", MaterialDefinition, "materials"),
    ContentFamilySpec("foundation.traits", "foundation/traits.yaml", TraitDefinition, "traits"),
    ContentFamilySpec("foundation.themes", "foundation/themes.yaml", ThemeDefinition, "themes"),
    ContentFamilySpec("foundation.relationship_axes", "foundation/relationship_axes.yaml", RelationshipAxisDefinition, "relationship_axes"),
    ContentFamilySpec("foundation.attributes", "foundation/attributes.yaml", AttributeDefinition, "attributes"),
    ContentFamilySpec("foundation.elements", "foundation/elements.yaml", ElementDefinition, "elements"),

    # 2. Living
    ContentFamilySpec("living.races", "living/races.yaml", RaceDefinition, "races"),
    ContentFamilySpec("living.need_profiles", "living/need_profiles.yaml", NeedProfileDefinition, "need_profiles"),
    ContentFamilySpec("living.sense_profiles", "living/sense_profiles.yaml", SenseProfileDefinition, "sense_profiles"),
    ContentFamilySpec("living.body_models", "living/body_models.yaml", BodyModelDefinition, "body_models"),
    ContentFamilySpec("living.drive_profiles", "living/drive_profiles.yaml", DriveProfileDefinition, "drive_profiles"),
    ContentFamilySpec("living.cognition_profiles", "living/cognition_profiles.yaml", CognitionProfileDefinition, "cognition_profiles"),

    # 3. Social
    ContentFamilySpec("social.roles", "social/roles.yaml", RoleDefinition, "roles"),
    ContentFamilySpec("social.factions", "social/factions.yaml", FactionDefinition, "factions"),
    ContentFamilySpec("social.perspectives", "social/perspectives.yaml", PerspectiveDefinition, "perspectives"),
    ContentFamilySpec("social.faction_relationships", "social/faction_relationships.yaml", FactionRelationshipDefinition, "faction_relationships"),

    # 4. Entities
    ContentFamilySpec("entities.stat_profiles", "entities/stat_profiles.yaml", StatsProfileDefinition, "stats_profiles"),
    ContentFamilySpec("entities.combat_profiles", "entities/combat_profiles.yaml", CombatProfileDefinition, "combat_profiles"),
    ContentFamilySpec("entities.inventory_profiles", "entities/inventory_profiles.yaml", InventoryProfileDefinition, "inventory_profiles"),
    ContentFamilySpec("entities.skill_profiles", "entities/skill_profiles.yaml", SkillProfileDefinition, "skill_profiles"),
    ContentFamilySpec("entities.populations", "entities/populations.yaml", PopulationRecipeDefinition, "populations"),
    ContentFamilySpec("entities.entity_archetypes", "entities/entity_archetypes.yaml", EntityArchetypeDefinition, "entity_archetypes"),

    # 5. World
    ContentFamilySpec("world.buildings", "world/buildings.yaml", BuildingDefinition, "buildings"),
    ContentFamilySpec("world.terrain", "world/terrain.yaml", TerrainDefinition, "terrain"),
    ContentFamilySpec("world.services", "world/services.yaml", ServiceProfileDefinition, "services"),
    ContentFamilySpec("world.regions", "world/runtime_regions.yaml", RuntimeRegionDefinition, "regions"),
    ContentFamilySpec("world.recipes", "world/recipes.yaml", RecipeDefinition, "recipes"),
    ContentFamilySpec("world.resources", "world/resources.yaml", ResourceDefinition, "resources"),
    ContentFamilySpec("world.items", "world/items.yaml", ItemDefinition, "items"),
    ContentFamilySpec("world.biomes", "world/biomes.yaml", BiomeDefinition, "biomes"),
    ContentFamilySpec("world.ecologies", "world/ecologies.yaml", EcologyDefinition, "ecologies"),

    # 6. Defaults & Legacy
    ContentFamilySpec("defaults", "defaults.yaml", DefaultCompileProfile, "defaults", required=False),
    ContentFamilySpec("spawn_tables", "spawn_tables.yaml", SpawnTableDefinition, "spawn_tables", required=False),

    # 7. Compatibility
    ContentFamilySpec("compatibility.legacy_enemy_projection", "compatibility/legacy_enemy_projection.yaml", LegacyEnemyProjectionDefinition, "legacy_enemy_projections", required=False, state_policy="compatibility"),
]


from src.content.paths import ContentPathConfig

# Directories inside data/content/ that are managed by loaders other than CatalogRepository
# (WorldModuleRepository, composition loader, ScenarioLabOrchestrator). Files in these
# directories must not be reported as "ignored" by strict mode.
NON_CATALOG_DIRS: frozenset = frozenset({"world_modules", "world_compositions", "simulation_scenarios"})


class CatalogRepository:
    """
    Thread-safe repository loader that coordinates static catalog schema configuration loading
    from data/content/**/*.yaml. Exposes clean lookup operations.
    """

    def __init__(self, content_dir: Optional[str] = None):
        self.content_dir = content_dir or ContentPathConfig().content_root
        
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
        self.last_report: Optional[CatalogLoadReport] = None

    def load_all(self, strict: bool = False) -> CatalogLoadReport:
        """Loads and parses all files under the content directory into structured indices based on CANONICAL_FAMILIES."""
        # Check duplicate paths in specs
        seen_paths = set()
        for spec in CANONICAL_FAMILIES:
            if spec.path in seen_paths:
                if strict:
                    raise ValueError(f"Duplicate family path detected: {spec.path}")
            seen_paths.add(spec.path)

        loaded_families: List[str] = []
        loaded_files: List[str] = []
        record_counts: Dict[str, int] = {}
        missing_required_files: List[str] = []
        missing_optional_files: List[str] = []
        duplicate_ids: List[str] = []
        schema_errors: Dict[str, Any] = {}

        # Reset raw_data
        self.raw_data = {}

        for spec in CANONICAL_FAMILIES:
            filepath = os.path.join(self.content_dir, spec.path)
            if not os.path.exists(filepath):
                if spec.required:
                    missing_required_files.append(spec.path)
                else:
                    missing_optional_files.append(spec.path)
                setattr(self, spec.repository_index, {})
                record_counts[spec.family] = 0
                continue

            loaded_families.append(spec.family)
            loaded_files.append(spec.path)

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
            except Exception as e:
                schema_errors[spec.path] = str(e)
                setattr(self, spec.repository_index, {})
                record_counts[spec.family] = 0
                self.raw_data[spec.path] = []
                continue

            if not data:
                setattr(self, spec.repository_index, {})
                record_counts[spec.family] = 0
                self.raw_data[spec.path] = []
                continue

            items: List[Any] = []
            format_error = False
            if isinstance(data, dict):
                items = data.get("items", []) or list(data.values())
            elif isinstance(data, list):
                items = data
            else:
                format_error = True
                err_msg = f"Catalog file {spec.path} must contain a list or map of definitions"
                schema_errors[spec.path] = err_msg
                setattr(self, spec.repository_index, {})
                record_counts[spec.family] = 0
                self.raw_data[spec.path] = []

            if not format_error:
                self.raw_data[spec.path] = items
                results = {}
                for item in items:
                    if not isinstance(item, dict) or "id" not in item:
                        err_msg = f"Definition in {spec.path} is malformed or missing 'id'"
                        schema_errors[spec.path] = err_msg
                        continue

                    def_id = item["id"]
                    if def_id in results:
                        duplicate_ids.append(def_id)
                        continue

                    try:
                        validated = spec.schema(**item)
                        results[def_id] = validated
                    except Exception as e:
                        schema_errors[spec.path] = str(e)
                        continue

                setattr(self, spec.repository_index, results)
                record_counts[spec.family] = len(results)

        # Detect ignored files
        ignored_files: List[str] = []
        registered_paths = {spec.path for spec in CANONICAL_FAMILIES}
        if os.path.exists(self.content_dir):
            for root, _, files in os.walk(self.content_dir):
                for file in files:
                    if file.endswith((".yaml", ".yml")):
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, self.content_dir)
                        rel_path = rel_path.replace(os.sep, "/")
                        if rel_path.split("/")[0] in NON_CATALOG_DIRS:
                            continue
                        if rel_path not in registered_paths:
                            ignored_files.append(rel_path)

        # Generate unique content fingerprint
        self._compute_fingerprint()

        empty_required_families = []
        for spec in CANONICAL_FAMILIES:
            if spec.required and record_counts.get(spec.family, 0) == 0:
                empty_required_families.append(spec.family)

        report = CatalogLoadReport(
            loaded_families=loaded_families,
            loaded_files=loaded_files,
            record_counts=record_counts,
            missing_required_files=missing_required_files,
            missing_optional_files=missing_optional_files,
            ignored_files=sorted(ignored_files),
            duplicate_ids=duplicate_ids,
            schema_errors=schema_errors,
            fingerprint=self.fingerprint
        )
        self.last_report = report

        # Strict checks
        if strict:
            if missing_required_files:
                raise ValueError(f"Missing required catalog files: {missing_required_files}")
            if schema_errors:
                raise ValueError(f"Schema validation errors found: {schema_errors}")
            if duplicate_ids:
                raise ValueError(f"Duplicate IDs detected: {duplicate_ids}")
            if ignored_files:
                raise ValueError(f"Ignored active YAML files found in repository: {ignored_files}")
            if empty_required_families:
                raise ValueError(f"Empty required active families found: {empty_required_families}")

        return report

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
