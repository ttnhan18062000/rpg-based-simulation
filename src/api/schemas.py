"""Pydantic response models for the REST API."""

from typing import Any, Union, Optional
from pydantic import BaseModel, Field


# --- Entity ---

class AttributeSchema(BaseModel):
    str_: int = Field(5, alias="str")
    agi: int = 5
    vit: int = 5
    int_: int = Field(5, alias="int")
    spi: int = 5
    wis: int = 5
    end: int = 5
    per: int = 5
    cha: int = 5
    # Training progression (0.0 to 1.0 fractional toward next point)
    str_frac: float = 0.0
    agi_frac: float = 0.0
    vit_frac: float = 0.0
    int_frac: float = 0.0
    spi_frac: float = 0.0
    wis_frac: float = 0.0
    end_frac: float = 0.0
    per_frac: float = 0.0
    cha_frac: float = 0.0

    model_config = {
        "populate_by_name": True
    }


class AttributeCapSchema(BaseModel):
    str_cap: int = 15
    agi_cap: int = 15
    vit_cap: int = 15
    int_cap: int = 15
    spi_cap: int = 15
    wis_cap: int = 15
    end_cap: int = 15
    per_cap: int = 15
    cha_cap: int = 15


class SkillSchema(BaseModel):
    skill_id: str
    name: str = ""
    cooldown_remaining: int = 0
    mastery: float = 0.0
    times_used: int = 0
    skill_type: str = "active"
    target: str = "self"
    stamina_cost: int = 0
    cooldown: int = 0
    power: float = 1.0
    description: str = ""
    damage_type: str = "physical"   # "physical" | "magical"
    element: str = "none"           # "none" | "fire" | "ice" | "lightning" | "dark" | "holy"


class EffectSchema(BaseModel):
    effect_type: str
    source: str = ""
    remaining_ticks: int = 0
    atk_mult: float = 1.0
    def_mult: float = 1.0
    spd_mult: float = 1.0
    crit_mult: float = 1.0
    evasion_mult: float = 1.0
    hp_per_tick: int = 0


class QuestSchema(BaseModel):
    quest_id: str
    quest_type: str
    title: str
    description: str = ""
    target_kind: str = ""
    target_x: int | None = None
    target_y: int | None = None
    target_count: int = 1
    progress: int = 0
    completed: bool = False
    gold_reward: int = 0
    xp_reward: int = 0


class SocialBondSchema(BaseModel):
    """Visual representation of a directed social bond. [PHASE 2]"""
    target_id: int
    target_name: str
    trust: float
    fear: float
    rivalry: float
    familiarity: float = 0.0
    loyalty: float = 0.0
    resentment: float = 0.0
    admiration: float = 0.0
    debt: float = 0.0
    narrative_summary: str | None = None
    social_impacts: list[str] = Field(default_factory=list) # [PHASE 2] High-level "why" bullets


class RoutineStateSchema(BaseModel):
    """Current biological needs and schedule. [PHASE 3]"""
    sleep_debt: float
    hunger_level: float
    is_sleeping: bool
    active_hours: str  # e.g. "06:00 - 22:00"


class MemoryLogSchema(BaseModel):
    """A single high-salience narrative event. [PHASE 2]"""
    tick: int
    type: str
    impact: float
    message: str
    details: dict = Field(default_factory=dict)

class TurningPointSchema(BaseModel):
    """A durable record of a life-defining moment. [PHASE 2]"""
    kind: str
    tick: int
    impact: float
    summary: str
    involved_names: list[str] = Field(default_factory=list)

class ReputationProfileSchema(BaseModel):
    """Authoritative public scores and tags. [PHASE 2]"""
    heroism: float
    cowardice: float
    threat_notoriety: float
    trustworthiness: float
    tags: list[str] = Field(default_factory=list)


# --- Behavioral Realism [PHASE 1] ---

class PersonalityProfileSchema(BaseModel):
    aggression: float
    greed: float
    caution: float
    loyalty: float
    ambition: float
    curiosity: float

class PersonalMotiveSchema(BaseModel):
    kind: str
    priority: float
    progress: float
    frustration: float
    active: bool

class ThreatEstimateSchema(BaseModel):
    overall: float
    melee_threat: float
    ranged_threat: float
    survivability: float
    confidence: float

class BeliefRecordSchema(BaseModel):
    entity_id: int
    pos: tuple[int, int]
    last_seen_tick: int
    stale_ticks: int
    confidence: float
    apparent_faction: str | None = None
    apparent_role: str | None = None
    apparent_class: str | None = None
    visible_weapon: str | None = None
    visible_injury: float = 0.0
    threat: ThreatEstimateSchema


class EntitySlimSchema(BaseModel):
    """Minimal entity data for rendering (non-selected entities)."""
    id: int
    kind: str
    display_name: str = ""
    x: int
    y: int
    hp: int
    max_hp: int
    state: str
    level: int = 1
    tier: int = 0
    faction: str = "hero_guild"
    weapon_range: int = 1
    combat_target_id: int | None = None
    loot_progress: int = 0
    loot_duration: int = 3

    model_config = {
        "frozen": True
    }


class EntitySchema(BaseModel):
    id: int
    kind: str
    display_name: str = ""
    x: int
    y: int
    hp: int
    max_hp: int
    atk: int
    def_: int = Field(0, alias="def")
    spd: int
    luck: int = 0
    crit_rate: float = 0.05
    evasion: float = 0.0
    matk: int = 0
    mdef: int = 0
    level: int = 1
    xp: int = 0
    xp_to_next: int = 100
    gold: int = 0
    tier: int = 0
    faction: str = "hero_guild"
    state: str
    weapon: str | None = None
    armor: str | None = None
    accessory: str | None = None
    inventory_count: int = 0
    inventory_max_slots: int = 0
    inventory_items: list[str] = Field(default_factory=list)
    inventory_weight: float = 0.0
    inventory_max_weight: float = 0.0
    vision_range: int = 6
    terrain_memory: dict[str, int] = Field(default_factory=dict)
    entity_memory: list[BeliefRecordSchema] = Field(default_factory=list)
    personality: PersonalityProfileSchema | None = None
    motives: list[PersonalMotiveSchema] = Field(default_factory=list)
    motive_utility_biases: dict[str, float] = Field(default_factory=dict)
    decision_drivers: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    loot_progress: int = 0
    loot_duration: int = 3
    known_recipes: list[str] = Field(default_factory=list)
    craft_target: str | None = None
    # RPG attributes
    stamina: int = 50
    max_stamina: int = 50
    attributes: AttributeSchema | None = None
    attribute_caps: AttributeCapSchema | None = None
    # Class & skills
    hero_class: str = "none"
    skills: list[SkillSchema] = Field(default_factory=list)
    class_mastery: float = 0.0
    active_effects: list[EffectSchema] = Field(default_factory=list)
    quests: list[QuestSchema] = Field(default_factory=list)
    
    # Social & Routine [PHASE 2 & 3]
    routine: RoutineStateSchema | None = None
    reputation: ReputationProfileSchema | None = None
    turning_points: list[TurningPointSchema] = Field(default_factory=list)
    memory_log: list[MemoryLogSchema] = Field(default_factory=list)
    traits: list[int] = Field(default_factory=list)
    # Base stats (before equipment/effects) for detailed breakdown
    base_atk: int = 0
    base_def: int = 0
    base_spd: int = 0
    base_matk: int = 0
    base_mdef: int = 0
    base_crit_rate: float = 0.05
    base_evasion: float = 0.0
    # Secondary / non-combat derived stats
    hp_regen: float = 1.0
    cooldown_reduction: float = 1.0
    loot_bonus: float = 1.0
    trade_bonus: float = 1.0
    interaction_speed: float = 1.0
    rest_efficiency: float = 1.0
    # Speed delay stats (computed from SPD + action type)
    speed_delay_move: float = 1.0
    speed_delay_attack: float = 0.9
    speed_delay_skill: float = 1.2
    speed_delay_harvest: float = 0.7
    # Elemental damage multipliers (from traits)
    fire_dmg_mult: float = 1.0
    ice_dmg_mult: float = 1.0
    lightning_dmg_mult: float = 1.0
    dark_dmg_mult: float = 1.0
    # Elemental vulnerability (from stats)
    elem_vuln_fire: float = 1.0
    elem_vuln_ice: float = 1.0
    elem_vuln_lightning: float = 1.0
    elem_vuln_dark: float = 1.0
    # Region (epic-15)
    region_id: str = ""
    difficulty_tier: int = 1
    current_region_id: str = ""
    # Combat visualization (epic-05)
    weapon_range: int = 1
    combat_target_id: int | None = None
    # Home storage
    home_storage_used: int = 0
    home_storage_max: int = 0
    home_storage_level: int = 0
    # Macro-Interest (Phase 4 Integration)
    routine: RoutineStateSchema | None = None
    social_bonds: list[SocialBondSchema] = Field(default_factory=list)

# --- Introspection (Phase 4) ---

class StatSourceSchema(BaseModel):
    source_name: str
    flat_bonus: int = 0
    mult_bonus: float = 1.0

class StatBreakdownSchema(BaseModel):
    stat_name: str
    final_value: float
    base_value: float
    sources: list[StatSourceSchema] = Field(default_factory=list)

class CombatTraceSchema(BaseModel):
    tick: int
    attacker_id: int
    defender_id: int
    skill_used: str
    raw_damage: int
    mitigation: int
    elemental_mult: float = 1.0
    is_crit: bool = False
    is_evasion: bool = False
    trauma: float = 0.0
    threat: float = 0.0
    explanation: str = ""

class GoalScoreSchema(BaseModel):
    goal_name: str
    score: float
    status: str = "considering" # "executing" | "considering"

# SocialBondSchema merged above

class DecisionDriverSchema(BaseModel):
    kind: str
    label: str
    weight: float

class AIDecisionSchema(BaseModel):
    entity_id: int
    current_state: str
    winning_goal: str
    goal_scores: list[GoalScoreSchema] = Field(default_factory=list)
    personality: dict[str, float] | None = None
    motives: list[dict[str, Any]] = Field(default_factory=list)
    beliefs: list[dict[str, Any]] = Field(default_factory=list)
    social_bonds: list[SocialBondSchema] = Field(default_factory=list) # [PHASE 2]
    faction_standing: dict[str, float] = Field(default_factory=dict) # [PHASE 2]
    motive_biases: dict[str, float] = Field(default_factory=dict)
    decision_drivers: list[str] = Field(default_factory=list) # [STAGE 1/2] Legacy string list
    driver_details: list[DecisionDriverSchema] = Field(default_factory=list) # [PHASE 1] New structured list
    nearest_enemy_dist: float | None = None
    nearest_target_id: int | None = None
    narrative_impacts: list[str] = Field(default_factory=list) # [PHASE 2] Global recent life shifts

class SchedulerTimelineItemSchema(BaseModel):
    entity_id: int
    display_name: str
    next_act_tick: int
    wait_ticks: int
    action_type: str = "unknown"

class EntityInspectionSchema(BaseModel):
    entity: EntitySchema
    routine: RoutineStateSchema | None = None
    reputation: ReputationProfileSchema | None = None
    stat_breakdowns: dict[str, StatBreakdownSchema] = Field(default_factory=dict)
    combat_history: list[CombatTraceSchema] = Field(default_factory=list)
    ai_explanation: AIDecisionSchema | None = None
    narrative_history: list[MemoryLogSchema] = Field(default_factory=list)
    turning_points: list[TurningPointSchema] = Field(default_factory=list)


# --- Map ---

class MapResponse(BaseModel):
    width: int
    height: int
    grid: list[int] = Field(description="RLE-encoded flat grid: [value, count, value, count, ...]")


# --- World State ---

class EventSchema(BaseModel):
    tick: int
    category: str
    message: str
    entity_ids: list[int] = Field(default_factory=list)
    metadata: dict | None = None


class GroundItemSchema(BaseModel):
    x: int
    y: int
    items: list[str]


class BuildingSchema(BaseModel):
    building_id: str
    name: str
    x: int
    y: int
    building_type: str
    owner_entity_id: int | None = None


class BuildingStateSchema(BaseModel):
    building_id: str
    storage_items: list[str] = Field(default_factory=list)
    storage_used: int = 0
    storage_max: int = 0
    storage_level: int = 0


class RecipeSchema(BaseModel):
    recipe_id: str
    output_item: str
    output_name: str
    gold_cost: int
    materials: dict[str, int]
    description: str = ""


class ShopItemSchema(BaseModel):
    item_id: str
    buy_price: int


class ResourceNodeSchema(BaseModel):
    node_id: int
    resource_type: str
    name: str
    x: int
    y: int
    terrain: int
    yields_item: str
    max_harvests: int
    respawn_cooldown: int
    harvest_ticks: int


class ResourceNodeStateSchema(BaseModel):
    node_id: int
    remaining: int
    is_available: bool


class TreasureChestSchema(BaseModel):
    chest_id: int
    x: int
    y: int
    tier: int


class TreasureChestStateSchema(BaseModel):
    chest_id: int
    looted: bool
    guard_entity_id: int | None = None


class LocationSchema(BaseModel):
    location_id: str
    name: str
    location_type: str
    x: int
    y: int
    region_id: str


class RegionSchema(BaseModel):
    region_id: str
    name: str
    terrain: int
    center_x: int
    center_y: int
    radius: int
    difficulty: int
    owner_faction: str | None = None
    influence: float = 0.0
    locations: list[LocationSchema] = Field(default_factory=list)


class WorldStateResponse(BaseModel):
    tick: int
    alive_count: int
    entities: list[EntitySlimSchema] = Field(default_factory=list)
    selected_entity: EntitySchema | None = None
    events: list[EventSchema] = Field(default_factory=list)
    ground_items: list[GroundItemSchema] = Field(default_factory=list)
    # Dynamic world object state (Audit Point 3 follow-up)
    resource_nodes: list[ResourceNodeStateSchema] = Field(default_factory=list)
    treasure_chests: list[TreasureChestStateSchema] = Field(default_factory=list)
    buildings: list[BuildingStateSchema] = Field(default_factory=list)
    # Strategic State (Milestone 11)
    war_status: dict[str, bool] = Field(default_factory=dict)
    faction_aggression: dict[str, float] = Field(default_factory=dict)


class StaticDataResponse(BaseModel):
    """Static world data fetched once after map load."""
    buildings: list[BuildingSchema] = Field(default_factory=list)
    resource_nodes: list[ResourceNodeSchema] = Field(default_factory=list)
    treasure_chests: list[TreasureChestSchema] = Field(default_factory=list)
    regions: list[RegionSchema] = Field(default_factory=list)


# --- Control ---

class ControlResponse(BaseModel):
    status: str
    message: str
    tick: int = 0


# --- Config ---

class SimulationConfigResponse(BaseModel):
    world_seed: int
    grid_width: int
    grid_height: int
    max_ticks: int
    num_workers: int
    initial_entity_count: int
    generator_spawn_interval: int
    generator_max_entities: int
    vision_range: int
    flee_hp_threshold: float
    tick_rate: float


# --- Stats ---

class SimulationStats(BaseModel):
    tick: int
    world_day: int
    alive_count: int
    total_spawned: int
    total_deaths: int
    running: bool
    paused: bool
