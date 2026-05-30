# Compliance IDs: WORLD-CAT-001, WORLD-CAT-002, WORLD-CAT-003
from __future__ import annotations

from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


class CatalogBaseDefinition(BaseModel):
    """Base class for all content catalog definitions."""
    model_config = ConfigDict(frozen=True)

    id: str = Field(..., min_length=1, description="Unique content identifier")
    display_name: str = Field(..., min_length=1, description="User-friendly display name")
    description: Optional[str] = Field(None, description="Optional textual description")
    tags: List[str] = Field(default_factory=list, description="Associated semantic classification tags")
    schema_version: str = Field(..., description="Schema version identifier")
    deprecated: bool = Field(False, description="Whether this definition is deprecated")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom extensible metadata dict")


class FactionDefinition(CatalogBaseDefinition):
    """Schema for Faction definitions inside content catalog."""
    alignment_bucket: str = Field(..., description="Faction moral or behavior alignment (e.g., defender, invader, neutral)")
    influence_role: str = Field(..., description="Influence role (e.g., sovereign, challenger, non_combatant)")
    relationship_group: str = Field(..., description="Group classification for defaults and hostility rules")
    legacy_engine_bucket: str = Field(..., description="Legacy Faction enum name mapping")

    @field_validator("legacy_engine_bucket")
    @classmethod
    def validate_legacy_bucket(cls, v: str) -> str:
        valid_buckets = {"HERO_GUILD", "MONSTER_HORDE", "TOWN_COUNCIL", "NEUTRAL"}
        if v.upper() not in valid_buckets:
            raise ValueError(f"legacy_engine_bucket must be one of {valid_buckets}")
        return v.upper()


class RoleDefinition(CatalogBaseDefinition):
    """Schema for Entity Role definitions."""
    role_family: str = Field(..., description="Family class (e.g., combatant, worker, civilian)")
    legacy_engine_role: str = Field(..., description="Legacy EntityRole enum name mapping")
    default_stats_profile: Optional[str] = Field(None, description="Default stats template ID")
    default_inventory_profile: Optional[str] = Field(None, description="Default starting inventory profile ID")
    default_cognition_profile: Optional[str] = Field(None, description="Default memory profile ID")

    @field_validator("legacy_engine_role")
    @classmethod
    def validate_legacy_role(cls, v: str) -> str:
        valid_roles = {"HERO", "SHOPKEEPER", "MONSTER", "CITIZEN", "WORKER", "GUARD"}
        if v.upper() not in valid_roles:
            raise ValueError(f"legacy_engine_role must be one of {valid_roles}")
        return v.upper()


class StatsProfileDefinition(CatalogBaseDefinition):
    """Schema for entity statistical properties defaults."""
    hp: int = Field(..., gt=0, description="Base starting HP")
    max_hp: int = Field(..., gt=0, description="Base maximum HP")
    atk: int = Field(..., ge=0, description="Base attack power")
    def_stat: int = Field(..., ge=0, description="Base defense power", alias="def")
    attack_range: int = Field(..., gt=0, description="Standard attack range in units")
    readiness: float = Field(100.0, ge=0.0, description="Default starting readiness")


class CombatProfileDefinition(CatalogBaseDefinition):
    """Schema for extra combat-specific coefficients and parameters."""
    accuracy: float = Field(1.0, ge=0.0, description="Base hit chance multiplier")
    crit_chance: float = Field(0.05, ge=0.0, le=1.0, description="Critical strike chance")
    crit_multiplier: float = Field(1.5, ge=1.0, description="Critical damage multiplier")


class InventoryProfileDefinition(CatalogBaseDefinition):
    """Schema specifying starting item stacks and equipment rules."""
    starting_items: Dict[str, int] = Field(default_factory=dict, description="Mapping of item kind to amount")
    starting_gold: float = Field(0.0, ge=0.0, description="Starting pocket gold")


class CognitionProfileDefinition(CatalogBaseDefinition):
    """Schema for starting memories, sensory constraints, or goal profiles."""
    sensory_range: float = Field(10.0, gt=0.0, description="Sensory perception radius")
    initial_memories: List[Dict[str, Any]] = Field(default_factory=list, description="Prepopulated semantic memories")


class ResourceDefinition(CatalogBaseDefinition):
    """Schema for standard gatherable resource node types."""
    resource_type: str = Field(..., description="Resource item identifier")
    required_ticks: int = Field(10, gt=0, description="Standard ticks required to harvest one charge")
    default_charges: int = Field(10, gt=0, description="Default remaining charges")


class BuildingDefinition(CatalogBaseDefinition):
    """Schema for constructed regional building types."""
    hp: int = Field(500, gt=0, description="Standard starting HP")
    max_hp: int = Field(500, gt=0, description="Standard max HP")
    service_profile_id: Optional[str] = Field(None, description="Default service profile mapping")


class ServiceProfileDefinition(CatalogBaseDefinition):
    """Schema for commercial or healing services supplied by buildings."""
    provided_items: List[str] = Field(default_factory=list, description="Items sold or stocked")
    heal_amount: Optional[int] = Field(0, ge=0, description="Amount of health restored by service")
    gold_cost: float = Field(0.0, ge=0.0, description="Cost of service in gold")


class TerrainDefinition(CatalogBaseDefinition):
    """Schema for ground terrain speed, hazard multipliers and descriptions."""
    move_cost_multiplier: float = Field(1.0, gt=0.0, description="Cost factor for movement speed through this terrain")
    hazard_multiplier: float = Field(1.0, ge=0.0, description="Scaling factor for hazard damage")


class SpawnTableDefinition(CatalogBaseDefinition):
    """Schema for structural population spawning weights."""
    spawn_weights: Dict[str, float] = Field(..., description="Mapping of role id to spawning weight factor")


class DefaultCompileProfile(CatalogBaseDefinition):
    """Schema for global world compilation fallbacks and constraints."""
    default_entity_hp: int = Field(100, gt=0)
    default_entity_atk: int = Field(10, ge=0)
    default_entity_def: int = Field(0, ge=0)
    default_entity_range: int = Field(1, gt=0)
    default_entity_readiness: float = Field(100.0, ge=0.0)
    default_resource_required_ticks: int = Field(10, gt=0)
    default_building_hp: int = Field(500, gt=0)
    default_faction_starting_gold: float = Field(1000.0, ge=0.0)
