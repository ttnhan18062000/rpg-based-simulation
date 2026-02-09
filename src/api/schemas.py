"""Pydantic response models for the REST API."""

from __future__ import annotations

from pydantic import BaseModel, Field


# --- Entity ---

class AttributeSchema(BaseModel):
    str_: int = Field(5, alias="str")
    agi: int = 5
    vit: int = 5
    int_: int = Field(5, alias="int")
    wis: int = 5
    end: int = 5
    # Training progression (0.0 to 1.0 fractional toward next point)
    str_frac: float = 0.0
    agi_frac: float = 0.0
    vit_frac: float = 0.0
    int_frac: float = 0.0
    wis_frac: float = 0.0
    end_frac: float = 0.0

    class Config:
        populate_by_name = True


class AttributeCapSchema(BaseModel):
    str_cap: int = 15
    agi_cap: int = 15
    vit_cap: int = 15
    int_cap: int = 15
    wis_cap: int = 15
    end_cap: int = 15


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


class EffectSchema(BaseModel):
    effect_type: str
    source: str = ""
    remaining_ticks: int = 0
    atk_mult: float = 1.0
    def_mult: float = 1.0
    spd_mult: float = 1.0


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


class EntitySchema(BaseModel):
    id: int
    kind: str
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
    inventory_items: list[str] = Field(default_factory=list)
    vision_range: int = 6
    terrain_memory: dict[str, int] = Field(default_factory=dict)
    entity_memory: list[dict] = Field(default_factory=list)
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

    class Config:
        frozen = True
        populate_by_name = True


# --- Map ---

class MapResponse(BaseModel):
    width: int
    height: int
    grid: list[list[int]] = Field(description="2D array of Material enum values (0=Floor,1=Wall,2=Water)")


# --- World State ---

class EventSchema(BaseModel):
    tick: int
    category: str
    message: str


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
    remaining: int
    max_harvests: int
    is_available: bool
    harvest_ticks: int


class WorldStateResponse(BaseModel):
    tick: int
    alive_count: int
    entities: list[EntitySchema]
    events: list[EventSchema] = Field(default_factory=list)
    ground_items: list[GroundItemSchema] = Field(default_factory=list)
    buildings: list[BuildingSchema] = Field(default_factory=list)
    resource_nodes: list[ResourceNodeSchema] = Field(default_factory=list)


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
    alive_count: int
    total_spawned: int
    total_deaths: int
    running: bool
    paused: bool
