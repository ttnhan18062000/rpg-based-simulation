# Compliance IDs: WORLD-CAT-004, WORLD-CAT-005
from __future__ import annotations

import os
import yaml
import hashlib
from typing import Dict, List, Optional, Any, Type, TypeVar
from pydantic import BaseModel

from src.content.schema import (
    FactionDefinition,
    RoleDefinition,
    StatsProfileDefinition,
    CombatProfileDefinition,
    InventoryProfileDefinition,
    CognitionProfileDefinition,
    ResourceDefinition,
    BuildingDefinition,
    ServiceProfileDefinition,
    TerrainDefinition,
    SpawnTableDefinition,
    DefaultCompileProfile,
    CatalogBaseDefinition,
)

T = TypeVar("T", bound=CatalogBaseDefinition)


class CatalogRepository:
    """
    Thread-safe repository loader that coordinates static catalog schema configuration loading
    from data/content/*.yaml. Exposes clean lookup operations.
    """

    def __init__(self, content_dir: str):
        self.content_dir = content_dir
        
        # In-memory indices
        self.factions: Dict[str, FactionDefinition] = {}
        self.roles: Dict[str, RoleDefinition] = {}
        self.stats_profiles: Dict[str, StatsProfileDefinition] = {}
        self.combat_profiles: Dict[str, CombatProfileDefinition] = {}
        self.inventory_profiles: Dict[str, InventoryProfileDefinition] = {}
        self.cognition_profiles: Dict[str, CognitionProfileDefinition] = {}
        self.resources: Dict[str, ResourceDefinition] = {}
        self.buildings: Dict[str, BuildingDefinition] = {}
        self.services: Dict[str, ServiceProfileDefinition] = {}
        self.terrain: Dict[str, TerrainDefinition] = {}
        self.spawn_tables: Dict[str, SpawnTableDefinition] = {}
        self.defaults: Dict[str, DefaultCompileProfile] = {}
        
        # Raw parsed structures for diagnostic/validation tracking
        self.raw_data: Dict[str, List[Dict[str, Any]]] = {}
        self._fingerprint: str = ""
        self._version: str = "1.0.0"

    def load_all(self) -> None:
        """Loads and parses all files under the content directory into structured indices."""
        self.factions = self._load_file("factions.yaml", FactionDefinition)
        self.roles = self._load_file("roles.yaml", RoleDefinition)
        self.stats_profiles = self._load_file("profiles/stats.yaml", StatsProfileDefinition)
        self.combat_profiles = self._load_file("profiles/combat.yaml", CombatProfileDefinition)
        self.inventory_profiles = self._load_file("profiles/inventory.yaml", InventoryProfileDefinition)
        self.cognition_profiles = self._load_file("profiles/cognition.yaml", CognitionProfileDefinition)
        self.resources = self._load_file("resources.yaml", ResourceDefinition)
        self.buildings = self._load_file("buildings.yaml", BuildingDefinition)
        self.services = self._load_file("services.yaml", ServiceProfileDefinition)
        self.terrain = self._load_file("terrain.yaml", TerrainDefinition)
        self.spawn_tables = self._load_file("spawn_tables.yaml", SpawnTableDefinition)
        self.defaults = self._load_file("defaults.yaml", DefaultCompileProfile)

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
        # We assume standard catalog YAML files are lists of definitions
        if isinstance(data, dict):
            # If formatted as { "items": [...] } or similar
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
        # Sort files and items within them to remain deterministic
        for filename in sorted(self.raw_data.keys()):
            sha.update(filename.encode("utf-8"))
            items = self.raw_data[filename]
            # Convert dict keys deterministically to string representations
            serialized = str(sorted(str(sorted(d.items())) for d in items if isinstance(d, dict)))
            sha.update(serialized.encode("utf-8"))
        self._fingerprint = sha.hexdigest()

    # Read-only Lookup API
    def get_faction(self, def_id: str) -> Optional[FactionDefinition]:
        return self.factions.get(def_id)

    def get_role(self, def_id: str) -> Optional[RoleDefinition]:
        return self.roles.get(def_id)

    def get_stats_profile(self, def_id: str) -> Optional[StatsProfileDefinition]:
        return self.stats_profiles.get(def_id)

    def get_combat_profile(self, def_id: str) -> Optional[CombatProfileDefinition]:
        return self.combat_profiles.get(def_id)

    def get_inventory_profile(self, def_id: str) -> Optional[InventoryProfileDefinition]:
        return self.inventory_profiles.get(def_id)

    def get_cognition_profile(self, def_id: str) -> Optional[CognitionProfileDefinition]:
        return self.cognition_profiles.get(def_id)

    def get_resource(self, def_id: str) -> Optional[ResourceDefinition]:
        return self.resources.get(def_id)

    def get_building(self, def_id: str) -> Optional[BuildingDefinition]:
        return self.buildings.get(def_id)

    def get_service_profile(self, def_id: str) -> Optional[ServiceProfileDefinition]:
        return self.services.get(def_id)

    def get_terrain(self, def_id: str) -> Optional[TerrainDefinition]:
        return self.terrain.get(def_id)

    def get_spawn_table(self, def_id: str) -> Optional[SpawnTableDefinition]:
        return self.spawn_tables.get(def_id)

    def get_default_profile(self, def_id: str) -> Optional[DefaultCompileProfile]:
        return self.defaults.get(def_id)

    # Repository Metadata Queries
    def get_all_ids_by_type(self, type_name: str) -> List[str]:
        mapping = {
            "faction": self.factions,
            "role": self.roles,
            "stats_profile": self.stats_profiles,
            "combat_profile": self.combat_profiles,
            "inventory_profile": self.inventory_profiles,
            "cognition_profile": self.cognition_profiles,
            "resource": self.resources,
            "building": self.buildings,
            "service_profile": self.services,
            "terrain": self.terrain,
            "spawn_table": self.spawn_tables,
            "defaults": self.defaults
        }
        return list(mapping.get(type_name.lower(), {}).keys())

    def get_deprecated_ids(self) -> Dict[str, List[str]]:
        deprecated_map: Dict[str, List[str]] = {}
        for cat_name, registry in [
            ("faction", self.factions),
            ("role", self.roles),
            ("stats_profile", self.stats_profiles),
            ("combat_profile", self.combat_profiles),
            ("inventory_profile", self.inventory_profiles),
            ("cognition_profile", self.cognition_profiles),
            ("resource", self.resources),
            ("building", self.buildings),
            ("service_profile", self.services),
            ("terrain", self.terrain),
            ("spawn_table", self.spawn_tables),
            ("defaults", self.defaults)
        ]:
            deprecated_map[cat_name] = [item_id for item_id, obj in registry.items() if obj.deprecated]
        return deprecated_map

    @property
    def fingerprint(self) -> str:
        return self._fingerprint

    @property
    def version(self) -> str:
        return self._version
