"""Metadata endpoints — expose all game definitions so the frontend has zero hardcoded data.

Core models (ItemTemplate, SkillDef, ClassDef, BreakthroughDef, TraitDef) are pydantic
dataclasses defined in src/core/.  They are the single source of truth used by both the
game engine and the API.  This module adds only thin aggregate response wrappers and
the handful of definitions (enums, attributes, buildings) that live nowhere else.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from fastapi import APIRouter

from src.core.enums import (
    AIState, DamageType, Element, EnemyTier, EntityRole,
    ItemType, Material, Rarity,
)
from src.core.faction import Faction, FactionRelation, FactionRegistry
from src.core.items import ITEM_REGISTRY, ItemTemplate
from src.core.classes import (
    CLASS_DEFS, CLASS_SKILLS, BREAKTHROUGHS, SKILL_DEFS, RACE_SKILLS,
    SCALING_GRADES, SCALING_MULTIPLIER,
    HeroClass, SkillDef, ClassDef, BreakthroughDef,
    SkillTarget,
)
from src.core.traits import TRAIT_DEFS, TraitDef
from src.core.buildings import RECIPES
from src.core.resource_nodes import TERRAIN_RESOURCES

router = APIRouter(prefix="/metadata", tags=["Metadata"])


# ---------------------------------------------------------------------------
# Pydantic response schemas — only for data NOT already in core models
# ---------------------------------------------------------------------------

# -- /enums helpers --

class EnumEntry(BaseModel):
    id: int
    name: str
    description: str = ""


class MaterialEntry(BaseModel):
    id: int
    name: str
    walkable: bool


class FactionEntry(BaseModel):
    id: int
    name: str


class FactionRelationEntry(BaseModel):
    faction_a: int
    faction_b: int
    relation: str


class EntityKindEntry(BaseModel):
    kind: str
    faction: str


class EnumsResponse(BaseModel):
    materials: list[MaterialEntry]
    ai_states: list[EnumEntry]
    tiers: list[EnumEntry]
    rarities: list[EnumEntry]
    item_types: list[EnumEntry]
    damage_types: list[EnumEntry]
    elements: list[EnumEntry]
    entity_roles: list[EnumEntry]
    factions: list[FactionEntry]
    faction_relations: list[FactionRelationEntry]
    entity_kinds: list[EntityKindEntry]


# -- /classes helpers (thin wrappers for grouped attribute view) --

class AttrBonuses(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    str_: int = Field(0, alias="str")
    agi: int = 0
    vit: int = 0
    int_: int = Field(0, alias="int")
    spi: int = 0
    wis: int = 0
    end: int = 0
    per: int = 0
    cha: int = 0


class AttrScaling(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    str_: str = Field("E", alias="str")
    agi: str = "E"
    vit: str = "E"
    int_: str = Field("E", alias="int")
    spi: str = "E"
    wis: str = "E"
    end: str = "E"
    per: str = "E"
    cha: str = "E"


class BreakthroughView(BaseModel):
    """Thin view that restructures flat BreakthroughDef fields for the frontend."""
    from_class: str
    to_class: str
    level_req: int
    attr_req: str
    attr_threshold: int
    talent: str
    bonuses: AttrBonuses
    cap_bonuses: AttrBonuses


class ClassView(BaseModel):
    """Thin view that restructures flat ClassDef fields for the frontend."""
    id: str
    name: str
    description: str
    tier: int = 1
    role: str = ""
    lore: str = ""
    playstyle: str = ""
    attr_bonuses: AttrBonuses
    cap_bonuses: AttrBonuses
    scaling: AttrScaling
    skill_ids: list[str] = []
    breakthrough: BreakthroughView | None = None


class ScalingGradeEntry(BaseModel):
    grade: str
    multiplier: float


class MasteryTierEntry(BaseModel):
    name: str
    min_mastery: float
    power_bonus: str
    stamina_reduction: str
    cooldown_reduction: str


class ClassesResponse(BaseModel):
    classes: list[ClassView]
    skills: list[dict]           # Serialized SkillDef (core model)
    race_skills: dict[str, list[str]]
    scaling_grades: list[ScalingGradeEntry]
    mastery_tiers: list[MasteryTierEntry]
    skill_targets: list[EnumEntry]


# -- /attributes & /buildings (no core model exists for these) --

class AttributeDefEntry(BaseModel):
    key: str
    label: str
    description: str


class AttributesResponse(BaseModel):
    attributes: list[AttributeDefEntry]


class BuildingTypeEntry(BaseModel):
    building_type: str
    name: str
    description: str


class BuildingsResponse(BaseModel):
    building_types: list[BuildingTypeEntry]


# -- /resources --

class ResourceTypeEntry(BaseModel):
    resource_type: str
    name: str
    terrain: str
    yields_item: str
    max_harvests: int
    respawn_cooldown: int
    harvest_ticks: int


class ResourcesResponse(BaseModel):
    resource_types: list[ResourceTypeEntry]


# -- /recipes --

class RecipeEntry(BaseModel):
    recipe_id: str
    output_item: str
    output_name: str
    gold_cost: int
    materials: dict[str, int]


class RecipesResponse(BaseModel):
    recipes: list[RecipeEntry]


# ---------------------------------------------------------------------------
# TypeAdapters for core models — serialize pydantic dataclasses to dicts
# ---------------------------------------------------------------------------

_item_ta = TypeAdapter(ItemTemplate)
_skill_ta = TypeAdapter(SkillDef)
_classdef_ta = TypeAdapter(ClassDef)
_breakthroughdef_ta = TypeAdapter(BreakthroughDef)
_traitdef_ta = TypeAdapter(TraitDef)


# ---------------------------------------------------------------------------
# Helper data (enums, attribute defs, building defs — no core model for these)
# ---------------------------------------------------------------------------

_NON_WALKABLE = {Material.WALL, Material.WATER, Material.LAVA}

_AI_STATE_DESCRIPTIONS: dict[str, str] = {
    "IDLE": "Idle — waiting for the AI evaluator to pick a new goal.",
    "WANDER": "Exploring and moving toward unexplored tiles to map the world.",
    "HUNT": "Seeking and chasing enemies to engage in combat.",
    "COMBAT": "Engaged in melee combat with an adjacent enemy.",
    "FLEE": "Retreating from danger toward safety.",
    "RETURN_TO_TOWN": "Navigating back to town for rest and resupply.",
    "RESTING_IN_TOWN": "Healing at town. Will visit buildings when fully healed.",
    "RETURN_TO_CAMP": "Enemy returning to its home camp.",
    "GUARD_CAMP": "Patrolling camp territory and watching for intruders.",
    "LOOTING": "Picking up items from the ground.",
    "ALERT": "Responding to a territory intrusion — seeking the intruder.",
    "VISIT_SHOP": "At the General Store — buying or selling items.",
    "VISIT_BLACKSMITH": "At the Blacksmith — learning recipes or crafting equipment.",
    "VISIT_GUILD": "At the Adventurer's Guild — gathering intel and accepting quests.",
    "HARVESTING": "Channeling a harvest action on a nearby resource node.",
    "VISIT_CLASS_HALL": "At the Class Hall — learning skills or attempting a class breakthrough.",
    "VISIT_INN": "Resting at the Inn for rapid HP and stamina recovery.",
    "VISIT_HOME": "At home — storing items or upgrading home storage.",
}

_ATTR_DEFS = [
    ("str", "STR", "Physical ATK scaling (+2%/pt), carry weight."),
    ("agi", "AGI", "SPD +0.4/pt, Crit +0.4%/pt, Evasion +0.3%/pt."),
    ("vit", "VIT", "Max HP +2/pt, physical DEF +0.3/pt."),
    ("int", "INT", "XP gain +1%/pt, MATK +0.2/pt, cooldown reduction."),
    ("spi", "SPI", "MATK +0.6/pt, MDEF +0.15/pt — primary magic offense."),
    ("wis", "WIS", "MDEF +0.4/pt, Luck +0.3/pt, XP gain +0.5%/pt."),
    ("end", "END", "Max stamina +2/pt, Max HP +0.5/pt, HP regen."),
    ("per", "PER", "Vision range +0.3/pt, loot quality, detection."),
    ("cha", "CHA", "Trade prices +1%/pt, interaction speed, social influence."),
]

_BUILDING_TYPES = [
    ("store", "General Store", "Buy and sell items. Heroes sell loot and purchase potions, equipment, and crafting materials."),
    ("blacksmith", "Blacksmith", "Learn recipes and craft equipment. Heroes bring materials and gold to forge upgrades."),
    ("guild", "Adventurer's Guild", "Gather intel on camps and resources. Accept quests and receive material hints."),
    ("class_hall", "Class Hall", "Learn class skills and attempt breakthroughs. The hall of heroes."),
    ("inn", "Traveler's Inn", "Rapid HP and stamina recovery. A safe haven within town walls."),
    ("hero_house", "Hero's House", "Personal dwelling. Store and retrieve items safely between adventures."),
]

_MATERIAL_NAMES = {
    Material.FLOOR: "Floor",
    Material.WALL: "Wall",
    Material.WATER: "Water",
    Material.TOWN: "Town",
    Material.CAMP: "Camp",
    Material.SANCTUARY: "Sanctuary",
    Material.FOREST: "Forest",
    Material.DESERT: "Desert",
    Material.SWAMP: "Swamp",
    Material.MOUNTAIN: "Mountain",
    Material.ROAD: "Road",
    Material.BRIDGE: "Bridge",
    Material.RUINS: "Ruins",
    Material.DUNGEON_ENTRANCE: "Dungeon Entrance",
    Material.LAVA: "Lava",
}

_SKILL_TARGET_NAMES = {
    SkillTarget.SELF: "self",
    SkillTarget.SINGLE_ENEMY: "single_enemy",
    SkillTarget.AREA_ENEMIES: "area_enemies",
    SkillTarget.SINGLE_ALLY: "single_ally",
    SkillTarget.AREA_ALLIES: "area_allies",
}


# ---------------------------------------------------------------------------
# Class view helpers — restructure flat ClassDef/BreakthroughDef into grouped views
# ---------------------------------------------------------------------------

def _attr_bonuses(obj) -> AttrBonuses:
    return AttrBonuses(**{
        "str": obj.str_bonus, "agi": obj.agi_bonus, "vit": obj.vit_bonus,
        "int": obj.int_bonus, "spi": obj.spi_bonus, "wis": obj.wis_bonus,
        "end": obj.end_bonus, "per": obj.per_bonus, "cha": obj.cha_bonus,
    })


def _cap_bonuses(obj) -> AttrBonuses:
    return AttrBonuses(**{
        "str": obj.str_cap_bonus, "agi": obj.agi_cap_bonus, "vit": obj.vit_cap_bonus,
        "int": obj.int_cap_bonus, "spi": obj.spi_cap_bonus, "wis": obj.wis_cap_bonus,
        "end": obj.end_cap_bonus, "per": obj.per_cap_bonus, "cha": obj.cha_cap_bonus,
    })


def _scaling(cd: ClassDef) -> AttrScaling:
    return AttrScaling(**{
        "str": cd.str_scaling, "agi": cd.agi_scaling, "vit": cd.vit_scaling,
        "int": cd.int_scaling, "spi": cd.spi_scaling, "wis": cd.wis_scaling,
        "end": cd.end_scaling, "per": cd.per_scaling, "cha": cd.cha_scaling,
    })


def _class_key(hc: HeroClass) -> str:
    return hc.name.lower()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/enums", response_model=EnumsResponse)
def get_enums() -> EnumsResponse:
    """All enum-like definitions: materials, AI states, tiers, rarities, factions, entity kinds."""

    materials = [
        MaterialEntry(
            id=m.value,
            name=_MATERIAL_NAMES.get(m, m.name.replace("_", " ").title()),
            walkable=m not in _NON_WALKABLE,
        )
        for m in Material
    ]

    ai_states = [
        EnumEntry(id=s.value, name=s.name, description=_AI_STATE_DESCRIPTIONS.get(s.name, ""))
        for s in AIState
    ]

    tiers = [EnumEntry(id=t.value, name=t.name.title()) for t in EnemyTier]
    rarities = [EnumEntry(id=r.value, name=r.name.lower()) for r in Rarity]
    item_types = [EnumEntry(id=it.value, name=it.name.lower()) for it in ItemType]
    damage_types = [EnumEntry(id=dt.value, name=dt.name.lower()) for dt in DamageType]
    elements = [EnumEntry(id=e.value, name=e.name.lower()) for e in Element]
    entity_roles = [EnumEntry(id=er.value, name=er.name.lower()) for er in EntityRole]
    factions = [FactionEntry(id=f.value, name=f.name.replace("_", " ").title()) for f in Faction]

    reg = FactionRegistry.default()
    faction_relations: list[FactionRelationEntry] = []
    for fa in Faction:
        for fb in Faction:
            if fa.value < fb.value:
                rel = reg.relation(fa, fb)
                faction_relations.append(FactionRelationEntry(
                    faction_a=fa.value, faction_b=fb.value,
                    relation=FactionRelation(rel).name.lower(),
                ))

    entity_kinds: list[EntityKindEntry] = []
    for kind_str, faction_val in reg._kind_map.items():
        entity_kinds.append(EntityKindEntry(
            kind=kind_str,
            faction=Faction(faction_val).name.replace("_", " ").title(),
        ))

    return EnumsResponse(
        materials=materials, ai_states=ai_states, tiers=tiers, rarities=rarities,
        item_types=item_types, damage_types=damage_types, elements=elements,
        entity_roles=entity_roles, factions=factions,
        faction_relations=faction_relations, entity_kinds=entity_kinds,
    )


@router.get("/items")
def get_items() -> dict:
    """Full item registry — returns core ItemTemplate models directly."""
    items = [_item_ta.dump_python(t, mode="json") for t in ITEM_REGISTRY.values()]
    return {"items": items}


@router.get("/classes", response_model=ClassesResponse)
def get_classes() -> ClassesResponse:
    """Class definitions, skills, breakthroughs, scaling grades, and mastery tiers."""

    classes: list[ClassView] = []
    for hc, cd in CLASS_DEFS.items():
        bt_view: BreakthroughView | None = None
        bt = BREAKTHROUGHS.get(hc)
        if bt:
            bt_view = BreakthroughView(
                from_class=_class_key(bt.from_class),
                to_class=_class_key(bt.to_class),
                level_req=bt.level_req,
                attr_req=bt.attr_req,
                attr_threshold=bt.attr_threshold,
                talent=bt.talent,
                bonuses=_attr_bonuses(bt),
                cap_bonuses=_cap_bonuses(bt),
            )

        classes.append(ClassView(
            id=_class_key(hc),
            name=cd.name,
            description=cd.description,
            tier=cd.tier,
            role=cd.role,
            lore=cd.lore,
            playstyle=cd.playstyle,
            attr_bonuses=_attr_bonuses(cd),
            cap_bonuses=_cap_bonuses(cd),
            scaling=_scaling(cd),
            skill_ids=CLASS_SKILLS.get(hc, []),
            breakthrough=bt_view,
        ))

    # Serialize core SkillDef models directly
    skills = [_skill_ta.dump_python(sdef, mode="json") for sdef in SKILL_DEFS.values()]

    scaling_grades = [
        ScalingGradeEntry(grade=g, multiplier=SCALING_MULTIPLIER[g])
        for g in SCALING_GRADES
    ]

    mastery_tiers = [
        MasteryTierEntry(name="Novice",      min_mastery=0,   power_bonus="—",    stamina_reduction="—",    cooldown_reduction="—"),
        MasteryTierEntry(name="Apprentice",   min_mastery=25,  power_bonus="—",    stamina_reduction="−10%", cooldown_reduction="—"),
        MasteryTierEntry(name="Adept",        min_mastery=50,  power_bonus="+20%", stamina_reduction="−10%", cooldown_reduction="—"),
        MasteryTierEntry(name="Expert",       min_mastery=75,  power_bonus="+20%", stamina_reduction="−20%", cooldown_reduction="−1 tick"),
        MasteryTierEntry(name="Master",       min_mastery=100, power_bonus="+35%", stamina_reduction="−25%", cooldown_reduction="−1 tick"),
    ]

    skill_targets = [
        EnumEntry(id=st.value, name=_SKILL_TARGET_NAMES.get(st, st.name.lower()))
        for st in SkillTarget
    ]

    return ClassesResponse(
        classes=classes, skills=skills, race_skills=RACE_SKILLS,
        scaling_grades=scaling_grades, mastery_tiers=mastery_tiers,
        skill_targets=skill_targets,
    )


@router.get("/traits")
def get_traits() -> dict:
    """All personality trait definitions — returns core TraitDef models directly."""
    traits = [_traitdef_ta.dump_python(tdef, mode="json") for tdef in TRAIT_DEFS.values()]
    return {"traits": traits}


@router.get("/attributes", response_model=AttributesResponse)
def get_attributes() -> AttributesResponse:
    """The 9 primary attribute definitions with effect descriptions."""
    return AttributesResponse(
        attributes=[AttributeDefEntry(key=k, label=l, description=d) for k, l, d in _ATTR_DEFS]
    )


@router.get("/buildings", response_model=BuildingsResponse)
def get_buildings() -> BuildingsResponse:
    """All building type definitions."""
    return BuildingsResponse(
        building_types=[BuildingTypeEntry(building_type=bt, name=n, description=d) for bt, n, d in _BUILDING_TYPES]
    )


@router.get("/resources", response_model=ResourcesResponse)
def get_resources() -> ResourcesResponse:
    """All resource node type definitions."""
    entries: list[ResourceTypeEntry] = []
    for terrain_mat, res_list in TERRAIN_RESOURCES.items():
        terrain_name = _MATERIAL_NAMES.get(Material(terrain_mat), str(terrain_mat))
        for res_type, res_name, yields, max_h, respawn, h_ticks in res_list:
            entries.append(ResourceTypeEntry(
                resource_type=res_type, name=res_name, terrain=terrain_name,
                yields_item=yields, max_harvests=max_h,
                respawn_cooldown=respawn, harvest_ticks=h_ticks,
            ))
    return ResourcesResponse(resource_types=entries)


@router.get("/recipes", response_model=RecipesResponse)
def get_recipes() -> RecipesResponse:
    """All crafting recipe definitions."""
    entries: list[RecipeEntry] = []
    for recipe in RECIPES:
        item = ITEM_REGISTRY.get(recipe.output_item)
        entries.append(RecipeEntry(
            recipe_id=recipe.recipe_id,
            output_item=recipe.output_item,
            output_name=item.name if item else recipe.output_item,
            gold_cost=recipe.gold_cost,
            materials=dict(recipe.materials),
        ))
    return RecipesResponse(recipes=entries)
