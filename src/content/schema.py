# Compliance IDs: WORLD-CAT-001, WORLD-CAT-002, WORLD-CAT-003
from __future__ import annotations

from typing import Optional, Any, Dict, List, Tuple
from pydantic import BaseModel, Field, ConfigDict, field_validator


class CatalogBaseDefinition(BaseModel):
    """Base class for all content catalog definitions."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(..., min_length=1, description="Unique content identifier")
    display_name: Optional[str] = Field(None, description="User-friendly display name")
    description: Optional[str] = Field(None, description="Optional textual description")
    tags: List[str] = Field(default_factory=list, description="Associated semantic classification tags")
    schema_version: Optional[str] = Field(None, description="Schema version identifier")
    deprecated: bool = Field(False, description="Whether this definition is deprecated")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom extensible metadata dict")
    extension: Dict[str, Any] = Field(default_factory=dict, description="Custom extensible compatibility dict")
    design_notes: Optional[str] = Field(None, description="Developer design notes")


# ==========================================
# 1. Foundation Models
# ==========================================

class MaterialDefinition(CatalogBaseDefinition):
    """Schema for raw raw materials."""
    categories: List[str] = Field(default_factory=list, description="Material classifications")
    common_regions: List[str] = Field(default_factory=list, description="Regions where this material is found")
    source_materials: List[str] = Field(default_factory=list, description="Precursor materials if crafted")


class TraitDefinition(CatalogBaseDefinition):
    """Schema for entity qualitative traits."""
    pass


class ThemeDefinition(CatalogBaseDefinition):
    """Schema for aesthetic/semantic theme tags."""
    pass


class RelationshipAxisDefinition(CatalogBaseDefinition):
    """Schema for dimensions of social relationships."""
    pass


class AttributeDefinition(CatalogBaseDefinition):
    """Schema for basic entity attributes."""
    pass


class ElementDefinition(CatalogBaseDefinition):
    """Schema for elemental/damage types."""
    pass


# ==========================================
# 2. Living & Profile Models
# ==========================================

class NeedProfileDefinition(CatalogBaseDefinition):
    """Schema for entity drives and survival needs weights."""
    needs: Dict[str, str] = Field(default_factory=dict, description="Motivation/need values (e.g. high, medium)")


class SenseProfileDefinition(CatalogBaseDefinition):
    """Schema for sensory perception factors."""
    vision: Optional[str] = Field(None)
    hearing: Optional[str] = Field(None)
    smell: Optional[str] = Field(None)
    magic_sense: Optional[str] = Field(None)
    social_reading: Optional[str] = Field(None)
    vibration: Optional[str] = Field(None)
    life_sense: Optional[str] = Field(None)


class BodyModelDefinition(CatalogBaseDefinition):
    """Schema for anatomical structures and equipment slots."""
    traits: List[str] = Field(default_factory=list)
    movement_modes: List[str] = Field(default_factory=list)
    equipment_slots: List[str] = Field(default_factory=list)


class DriveProfileDefinition(CatalogBaseDefinition):
    """Schema for behavioral motivations and goals weights."""
    drives: Dict[str, str] = Field(default_factory=dict)


class CognitionProfileDefinition(CatalogBaseDefinition):
    """Schema for mental modeling and decision constraints."""
    planning_depth: Optional[str] = Field(None)
    abstraction: Optional[str] = Field(None)
    memory_span: Optional[str] = Field(None)
    language_capacity: Optional[str] = Field(None)
    tool_reasoning: Optional[str] = Field(None)
    social_reading: Optional[str] = Field(None)
    social_reasoning: Optional[str] = Field(None)
    risk_modeling: Optional[str] = Field(None)
    supports_adventure_routing: bool = Field(False)


class StatsProfileDefinition(CatalogBaseDefinition):
    """Schema for entity statistical properties defaults."""
    hp: int = Field(..., gt=0, description="Base starting HP")
    max_hp: int = Field(..., gt=0, description="Base maximum HP")
    atk: int = Field(..., ge=0, description="Base attack power")
    def_stat: int = Field(..., ge=0, description="Base defense power", alias="def")
    attack_range: int = Field(..., gt=0, description="Standard attack range in units")
    readiness: float = Field(100.0, ge=0.0, description="Default starting readiness")
    attribute_bias: Dict[str, str] = Field(default_factory=dict, description="Attribute priority biases")


class CombatProfileDefinition(CatalogBaseDefinition):
    """Schema for extra combat-specific coefficients and parameters."""
    accuracy: float = Field(1.0, ge=0.0, description="Base hit chance multiplier")
    crit_chance: float = Field(0.05, ge=0.0, le=1.0, description="Critical strike chance")
    crit_multiplier: float = Field(1.5, ge=1.0, description="Critical damage multiplier")
    damage_tags: List[str] = Field(default_factory=list, description="Damage type semantic tags")


class InventoryProfileDefinition(CatalogBaseDefinition):
    """Schema specifying starting item stacks and equipment rules."""
    starting_items: Dict[str, int] = Field(default_factory=dict, description="Mapping of item kind to amount")
    starting_gold: float = Field(0.0, ge=0.0, description="Starting pocket gold")


class SkillProfileDefinition(CatalogBaseDefinition):
    """Schema for skill levels and cooldown triggers."""
    skills: List[str] = Field(default_factory=list)


class RaceDefinition(CatalogBaseDefinition):
    """Schema for dynamic race/species definition."""
    body_model: str = Field(..., description="Referenced BodyModelDefinition ID")
    need_profile: str = Field(..., description="Referenced NeedProfileDefinition ID")
    sense_profile: str = Field(..., description="Referenced SenseProfileDefinition ID")
    cognition_profile: str = Field(..., description="Referenced CognitionProfileDefinition ID")
    drive_profile: str = Field(..., description="Referenced DriveProfileDefinition ID")
    intelligence_tier: str = Field(..., description="Species cognitive-sophistication classification: 'high' or 'low', anchored via tool_user presence in natural_traits (see docs/mechanics species-tier note if authored) with explicitly justified exceptions.")
    natural_traits: List[str] = Field(default_factory=list)
    attribute_tendencies: Dict[str, str] = Field(default_factory=dict)
    compatible_roles: List[str] = Field(default_factory=list)

    @field_validator("intelligence_tier")
    @classmethod
    def validate_intelligence_tier(cls, v: str) -> str:
        valid_tiers = {"high", "low"}
        if v not in valid_tiers:
            raise ValueError(f"intelligence_tier must be one of {valid_tiers}")
        return v


# ==========================================
# 3. Social & Faction Models
# ==========================================

class FactionDefinition(CatalogBaseDefinition):
    """Schema for Faction definitions inside content catalog."""
    alignment_bucket: str = Field(..., description="Faction moral or behavior alignment (e.g., defender, invader, neutral)")
    influence_role: str = Field(..., description="Influence role (e.g., sovereign, challenger, non_combatant)")
    relationship_group: Optional[str] = Field(None, description="Optional legacy relationship group")
    legacy_engine_bucket: str = Field(..., description="Legacy Faction enum name mapping")
    common_races: List[str] = Field(default_factory=list)
    themes: List[str] = Field(default_factory=list)
    hazard_immunities: List[str] = Field(default_factory=list, description="Hazard-kind tags this faction's members endure without harm (e.g. 'NATURAL_TERRAIN', 'CHAOS_CORRUPTION').")

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
    compatible_traits: List[str] = Field(default_factory=list)

    @field_validator("legacy_engine_role")
    @classmethod
    def validate_legacy_role(cls, v: str) -> str:
        valid_roles = {"HERO", "SHOPKEEPER", "MONSTER", "CITIZEN", "WORKER", "GUARD"}
        if v.upper() not in valid_roles:
            raise ValueError(f"legacy_engine_role must be one of {valid_roles}")
        return v.upper()


class PerspectiveDefinition(CatalogBaseDefinition):
    """Schema for a faction's point-of-view projections."""
    chosen_faction: str = Field(..., description="Referenced FactionDefinition ID")
    default_focus: str = Field(..., description="Primary goal driver")
    projected_labels: Dict[str, List[str]] = Field(default_factory=dict, description="Groups classified by hostily/ally labels")


class FactionRelationshipDefinition(CatalogBaseDefinition):
    """Schema for relationship values between two factions."""
    source_faction: str = Field(..., description="Source FactionDefinition ID")
    target_faction: str = Field(..., description="Target FactionDefinition ID")
    relationship_model: str = Field(..., description="Relationship classification")
    axes: Dict[str, str] = Field(default_factory=dict)


class RaceRelationRecord(CatalogBaseDefinition):
    """Schema for hostility/relationship axes between two races."""
    source_race: str = Field(..., description="Source RaceDefinition ID")
    target_race: str = Field(..., description="Target RaceDefinition ID")
    relationship_model: str = Field(..., description="Relationship classification")
    axes: Dict[str, str] = Field(default_factory=dict)


# ==========================================
# 4. Entity & World Models
# ==========================================

class EntityArchetypeDefinition(CatalogBaseDefinition):
    """Schema for the spawnable entity archetype templates."""
    race: str = Field(..., description="Referenced RaceDefinition ID")
    faction: str = Field(..., description="Referenced FactionDefinition ID")
    role: str = Field(..., description="Referenced RoleDefinition ID")
    stat_profile: str = Field(..., description="Referenced StatsProfileDefinition ID")
    combat_profile: str = Field(..., description="Referenced CombatProfileDefinition ID")
    cognition_profile: str = Field(..., description="Referenced CognitionProfileDefinition ID")
    drive_profile: str = Field(..., description="Referenced DriveProfileDefinition ID")
    inventory_profile: str = Field(..., description="Referenced InventoryProfileDefinition ID")
    skill_profile: Optional[str] = Field(None, description="Referenced SkillProfileDefinition ID")
    traits: List[str] = Field(default_factory=list)
    themes: List[str] = Field(default_factory=list)


class PopulationRecipeDefinition(CatalogBaseDefinition):
    """Schema for grouping entity archetypes together in biomes/ecologies."""
    members: Dict[str, int] = Field(..., description="Mapping of EntityArchetypeDefinition IDs to counts")
    preferred_regions: List[str] = Field(default_factory=list)


class LegacyEnemyProjectionDefinition(CatalogBaseDefinition):
    """Schema defining translation layers back to legacy EnemyDef objects."""
    archetype_id: str = Field(..., description="Referenced EntityArchetypeDefinition ID")
    legacy_enemy_id: str = Field(..., description="Referenced legacy EnemyRegistry ID key")
    danger_hint: str = Field(..., description="Legacy threat level (e.g. MEDIUM, BOSS)")
    loot_table: Dict[str, float] = Field(default_factory=dict, description="Mapping of ItemDefinition ID to chance")
    spawn_regions: List[str] = Field(default_factory=list)


class ResourceDefinition(CatalogBaseDefinition):
    """Schema for gatherable resource node types."""
    resource_type: str = Field(..., description="Resource item identifier")
    required_ticks: int = Field(10, gt=0, description="Standard ticks required to harvest one charge")
    default_charges: int = Field(10, gt=0, description="Default remaining charges")
    material: Optional[str] = Field(None, description="Material ID yielded by harvesting")
    preferred_biomes: List[str] = Field(default_factory=list, description="Biomes where this resource commonly spawns")
    runtime_kind: Optional[str] = Field(None, description="Explicit runtime resource type")
    legacy_id: Optional[str] = Field(None, description="Explicit legacy ID mapping")
    required_tool: Optional[str] = Field(None, description="Explicit required tool")


class BuildingDefinition(CatalogBaseDefinition):
    """Schema for constructed regional building types."""
    hp: int = Field(500, gt=0, description="Standard starting HP")
    max_hp: int = Field(500, gt=0, description="Standard max HP")
    service_profile_id: Optional[str] = Field(None, description="Default service profile mapping")
    themes: List[str] = Field(default_factory=list, description="Aesthetic/functional themes of the building")


class ServiceProfileDefinition(CatalogBaseDefinition):
    """Schema for commercial or healing services supplied by buildings."""
    provided_items: List[str] = Field(default_factory=list, description="Items sold or stocked")
    heal_amount: Optional[int] = Field(0, ge=0, description="Amount of health restored by service")
    gold_cost: float = Field(0.0, ge=0.0, description="Cost of service in gold")
    service_type: Optional[str] = Field(None, description="Role/type of the service")
    provided_recipes: List[str] = Field(default_factory=list, description="Recipes supported by this service station")
    resource_bias: List[str] = Field(default_factory=list, description="Associated resources for extraction bias")
    affordances: List[str] = Field(default_factory=list, description="Explicit service affordances")


class TerrainDefinition(CatalogBaseDefinition):
    """Schema for ground terrain speed, hazard multipliers and descriptions."""
    move_cost_multiplier: float = Field(1.0, gt=0.0, description="Cost factor for movement speed through this terrain")
    hazard_multiplier: float = Field(1.0, ge=0.0, description="Scaling factor for hazard damage")


class SpawnTableDefinition(CatalogBaseDefinition):
    """Schema for structural population spawning weights."""
    spawn_weights: Dict[str, float] = Field(..., description="Mapping of role id to spawning weight factor")


class ClassTableDefinition(CatalogBaseDefinition):
    """Schema for class assignment tables mapping entity roles to eligible class IDs."""
    class_id_by_role: Dict[str, List[str]] = Field(..., description="Mapping of role id to list of eligible class IDs")


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


class ItemDefinition(CatalogBaseDefinition):
    """Schema for item definitions under the dynamic content catalog."""
    categories: List[str] = Field(..., description="Category tags (e.g. weapon, melee, material)")
    rarity: str = Field("COMMON", description="Item rarity")
    base_value: float = Field(0.0, ge=0.0, description="Base value in gold")
    materials: List[str] = Field(default_factory=list, description="Materials composing this item")
    use_kind: Optional[str] = Field(None, description="Explicit runtime usage kind")
    class_fit: List[str] = Field(default_factory=list, description="Explicit class fit tags")
    equipment_slot: Optional[str] = Field(None, description="Explicit equipment slot")


class RecipeDefinition(CatalogBaseDefinition):
    """Schema for crafting and manufacturing recipes."""
    ingredients: Dict[str, int] = Field(..., description="Input item ingredients required (mapping of item_id to quantity)")
    required_service: Optional[str] = Field(None, description="Referenced ServiceProfileDefinition ID required")
    gold_cost: float = Field(0.0, ge=0.0, description="Required gold fee to craft")
    outputs: Dict[str, int] = Field(..., description="Resulting output items produced (mapping of item_id to quantity)")
    required_level: int = Field(1, ge=1, description="Required crafting skill level")


class RuntimeRegionDefinition(CatalogBaseDefinition):
    """Schema describing adventure progression, danger zones, and threat metadata."""
    danger_level: int = Field(0, ge=0, description="Threat danger index of the region")
    allowed_enemy_ids: List[str] = Field(default_factory=list, description="Referenced EnemyDefinition IDs allowed to spawn")
    resource_bias: Dict[str, float] = Field(default_factory=dict, description="Probability biases for different resource spawns")
    travel_cost: float = Field(0.0, ge=0.0, description="Gold or tick cost to travel to this region")
    biome: Optional[str] = Field(None, description="Primary biome of this runtime region")
    controlling_faction: Optional[str] = Field(None, description="Faction that owns or controls this region")


class BiomeDefinition(CatalogBaseDefinition):
    """Schema describing regional biomes, terrain profiles, and danger defaults."""
    themes: List[str] = Field(default_factory=list)
    terrain_mix: List[str] = Field(default_factory=list)
    common_materials: List[str] = Field(default_factory=list)
    default_factions: List[str] = Field(default_factory=list)
    danger_level: int = Field(0, ge=0)


class EcologyDefinition(CatalogBaseDefinition):
    """Schema tying together biomes, factions, populations, and resources into local ecologies."""
    biomes: List[str] = Field(default_factory=list)
    dominant_factions: List[str] = Field(default_factory=list)
    populations: List[str] = Field(default_factory=list)
    resources: List[str] = Field(default_factory=list)
    relationship_models: List[str] = Field(default_factory=list)
    services: List[str] = Field(default_factory=list)
