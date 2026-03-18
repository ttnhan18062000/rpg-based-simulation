"""Hero class system — classes, skills, breakthrough, and mastery.

Heroes choose a class which provides:
  - Attribute bonuses (base + cap)
  - Class-specific skills (learnable at class buildings for gold)
  - Breakthrough path (e.g. Warrior → Champion at Lv10+ with STR 30+)
  - Mastery progression (using skills increases mastery)

All entities also have race skills (innate, no cost to learn).

Skill types:
  - ACTIVE: Costs stamina, has cooldown, used in combat/exploration
  - PASSIVE: Always active, provides stat bonuses
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum, unique
from typing import Annotated

from pydantic import PlainSerializer
from pydantic.dataclasses import dataclass as pydantic_dataclass

from src.core.enums import DamageType


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

@unique
class HeroClass(IntEnum):
    """Class identities for heroes and mobs (shared enum)."""
    NONE = 0
    # --- Hero classes ---
    WARRIOR = 1
    RANGER = 2
    MAGE = 3
    ROGUE = 4
    # --- Hero breakthroughs ---
    CHAMPION = 5
    SHARPSHOOTER = 6
    ARCHMAGE = 7
    ASSASSIN = 8
    # --- Tier 3 Transcendence classes ---
    WARLORD = 9
    STORM_CALLER = 10
    GHOST_STALKER = 11
    NIGHTSHADE = 12
    # --- Mob archetypes ---
    BRUTE = 20       # Heavy melee (orcs, warrior goblins) — STR/VIT focus
    SCOUT = 21       # Fast flanker (wolves, scouts) — AGI/PER focus
    CASTER = 22      # Magic user (liches, goblin chiefs) — SPI/INT focus
    TANK = 23        # Durable defender (skeletons, orc warlords) — VIT/END focus
    BEAST = 24       # Wild creature (wolves, dire wolves) — STR/AGI focus


@unique
class SkillType(IntEnum):
    """Skill categories."""
    ACTIVE = 0
    PASSIVE = 1


@unique
class SkillTarget(IntEnum):
    """Who a skill targets."""
    SELF = 0
    SINGLE_ENEMY = 1
    AREA_ENEMIES = 2
    SINGLE_ALLY = 3
    AREA_ALLIES = 4


# ---------------------------------------------------------------------------
# Skill definition
# ---------------------------------------------------------------------------

from pydantic import PlainSerializer, BeforeValidator

def _parse_enum(cls):
    def _parse(v):
        if isinstance(v, cls): return v
        if isinstance(v, int):
            try: return cls(v)
            except ValueError: return v
        if isinstance(v, str):
            try: return cls[v.upper()]
            except KeyError: pass
        return v
    return _parse

# Serialization helpers — enums serialize as lowercase name strings for the API
_SkillTypeSer = Annotated[SkillType, BeforeValidator(_parse_enum(SkillType)), PlainSerializer(lambda v: SkillType(v).name.lower(), return_type=str)]
_SkillTargetSer = Annotated[SkillTarget, BeforeValidator(_parse_enum(SkillTarget)), PlainSerializer(lambda v: SkillTarget(v).name.lower(), return_type=str)]
_HeroClassSer = Annotated[HeroClass, BeforeValidator(_parse_enum(HeroClass)), PlainSerializer(lambda v: HeroClass(v).name.lower(), return_type=str)]
_DamageTypeSer = Annotated[int, BeforeValidator(_parse_enum(DamageType)), PlainSerializer(lambda v: DamageType(v).name.lower(), return_type=str)]


@pydantic_dataclass(frozen=True)
class SkillDef:
    """Immutable skill template/definition."""
    skill_id: str
    name: str
    description: str
    skill_type: _SkillTypeSer
    target: _SkillTargetSer
    class_req: _HeroClassSer       # NONE = race skill (no class required)
    level_req: int = 1
    gold_cost: int = 0         # Cost to learn at building
    cooldown: int = 5          # Ticks between uses
    stamina_cost: int = 10     # Stamina to activate
    # Effects
    power: float = 1.0         # Damage multiplier or heal amount multiplier
    duration: int = 0          # Buff/debuff duration in ticks
    range: int = 1             # Cast distance in tiles (how far you can use it)
    # AoE (epic-05 F1)
    radius: int = 0            # AoE spread from impact point (0 = single target)
    aoe_falloff: float = 0.15  # Damage reduction per tile from center (0.15 = -15%/tile)
    # Learning prerequisites
    mastery_req: str = ""       # Prerequisite skill_id that must have mastery >= mastery_threshold
    mastery_threshold: float = 25.0  # Min mastery on prerequisite skill
    # Stat modifiers (for passive skills)
    atk_mod: float = 0.0
    def_mod: float = 0.0
    spd_mod: float = 0.0
    crit_mod: float = 0.0
    evasion_mod: float = 0.0
    hp_mod: float = 0.0
    # Damage type: determines which stat pair (ATK/DEF vs MATK/MDEF) is used
    damage_type: _DamageTypeSer = DamageType.PHYSICAL


@dataclass(slots=True)
class SkillInstance:
    """A learned skill on an entity, tracking cooldown and mastery."""
    skill_id: str
    cooldown_remaining: int = 0
    mastery: float = 0.0       # 0.0 to 100.0
    times_used: int = 0

    def is_ready(self) -> bool:
        return self.cooldown_remaining <= 0

    def use(self, base_cooldown: int) -> None:
        self.cooldown_remaining = base_cooldown
        self.times_used += 1
        # Mastery gain: diminishing returns
        gain = max(0.1, 1.0 - self.mastery * 0.008)
        self.mastery = min(100.0, self.mastery + gain)

    def tick(self) -> None:
        if self.cooldown_remaining > 0:
            self.cooldown_remaining -= 1

    @property
    def mastery_tier(self) -> int:
        """0=novice, 1=apprentice(25), 2=adept(50), 3=expert(75), 4=master(100)"""
        if self.mastery >= 100.0:
            return 4
        if self.mastery >= 75.0:
            return 3
        if self.mastery >= 50.0:
            return 2
        if self.mastery >= 25.0:
            return 1
        return 0

    def effective_power(self, base_power: float) -> float:
        """Power modified by mastery. +20% at mastery tier 2+."""
        mult = 1.0
        if self.mastery >= 50.0:
            mult += 0.20
        if self.mastery >= 100.0:
            mult += 0.15  # Total +35% at master
        return base_power * mult

    def effective_stamina_cost(self, base_cost: int) -> int:
        """Stamina cost reduced by mastery. -10% at tier 1+, -20% at tier 3+."""
        mult = 1.0
        if self.mastery >= 25.0:
            mult -= 0.10
        if self.mastery >= 75.0:
            mult -= 0.10  # Total -20%
        return max(1, int(base_cost * mult))

    def effective_cooldown(self, base_cd: int) -> int:
        """Cooldown reduced at mastery tier 3+."""
        if self.mastery >= 75.0:
            return max(1, base_cd - 1)
        return base_cd

    def copy(self) -> SkillInstance:
        return SkillInstance(
            skill_id=self.skill_id,
            cooldown_remaining=self.cooldown_remaining,
            mastery=self.mastery,
            times_used=self.times_used,
        )


# ---------------------------------------------------------------------------
# Class definition
# ---------------------------------------------------------------------------

# Attribute scaling grades — determines how effectively a class
# benefits from investing in each attribute.  Higher grades yield
# larger derived-stat bonuses from that attribute.
SCALING_GRADES = ('E', 'D', 'C', 'B', 'A', 'S', 'SS', 'SSS')

SCALING_MULTIPLIER: dict[str, float] = {
    'E': 0.60, 'D': 0.75, 'C': 0.90, 'B': 1.00,
    'A': 1.15, 'S': 1.30, 'SS': 1.50, 'SSS': 1.80,
}


@pydantic_dataclass(frozen=True)
class ClassDef:
    """Immutable class template."""
    class_id: _HeroClassSer
    name: str
    description: str
    # Attribute bonuses applied when class is chosen
    str_bonus: int = 0
    agi_bonus: int = 0
    vit_bonus: int = 0
    int_bonus: int = 0
    spi_bonus: int = 0
    wis_bonus: int = 0
    end_bonus: int = 0
    per_bonus: int = 0
    cha_bonus: int = 0
    # Attribute cap bonuses
    str_cap_bonus: int = 0
    agi_cap_bonus: int = 0
    vit_cap_bonus: int = 0
    int_cap_bonus: int = 0
    spi_cap_bonus: int = 0
    wis_cap_bonus: int = 0
    end_cap_bonus: int = 0
    per_cap_bonus: int = 0
    cha_cap_bonus: int = 0
    # Breakthrough target
    breakthrough_class: _HeroClassSer = HeroClass.NONE
    breakthrough_level: int = 10
    breakthrough_attr: str = ""      # e.g. "str" — which attribute must be >= threshold
    breakthrough_threshold: int = 30
    # Attribute scaling grades (E–SSS)
    str_scaling: str = 'E'
    agi_scaling: str = 'E'
    vit_scaling: str = 'E'
    int_scaling: str = 'E'
    spi_scaling: str = 'E'
    wis_scaling: str = 'E'
    end_scaling: str = 'E'
    per_scaling: str = 'E'
    cha_scaling: str = 'E'
    # Lore & identity
    tier: int = 1                    # 1 = base, 2 = breakthrough, 3 = transcendence
    lore: str = ''
    playstyle: str = ''
    role: str = ''                   # e.g. "DPS", "Tank", "Support"


@pydantic_dataclass(frozen=True)
class BreakthroughDef:
    """Breakthrough (promotion) definition."""
    from_class: _HeroClassSer
    to_class: _HeroClassSer
    level_req: int
    attr_req: str              # e.g. "str"
    attr_threshold: int
    # Bonuses on breakthrough
    str_bonus: int = 0
    agi_bonus: int = 0
    vit_bonus: int = 0
    int_bonus: int = 0
    spi_bonus: int = 0
    wis_bonus: int = 0
    end_bonus: int = 0
    per_bonus: int = 0
    cha_bonus: int = 0
    str_cap_bonus: int = 0
    agi_cap_bonus: int = 0
    vit_cap_bonus: int = 0
    int_cap_bonus: int = 0
    spi_cap_bonus: int = 0
    wis_cap_bonus: int = 0
    end_cap_bonus: int = 0
    per_cap_bonus: int = 0
    cha_cap_bonus: int = 0
    talent: str = ""           # Special passive ability name


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

# -- Class Definitions --

CLASS_DEFS: dict[HeroClass, ClassDef] = {}

SKILL_DEFS: dict[str, SkillDef] = {}

SKILL_DEFS: dict[str, SkillDef] = {}

BREAKTHROUGHS: dict[HeroClass, BreakthroughDef] = {}

# --- Tier 2 Breakthroughs (Already existing in simulation logic) ---
BREAKTHROUGHS[HeroClass.WARRIOR] = BreakthroughDef(HeroClass.WARRIOR, HeroClass.CHAMPION, 10, "str", 30)
BREAKTHROUGHS[HeroClass.RANGER] = BreakthroughDef(HeroClass.RANGER, HeroClass.SHARPSHOOTER, 10, "agi", 30)
BREAKTHROUGHS[HeroClass.MAGE] = BreakthroughDef(HeroClass.MAGE, HeroClass.ARCHMAGE, 10, "int", 30)
BREAKTHROUGHS[HeroClass.ROGUE] = BreakthroughDef(HeroClass.ROGUE, HeroClass.ASSASSIN, 10, "agi", 30)

# --- Tier 3 Transcendence (New Calamity-locked classes) ---
BREAKTHROUGHS[HeroClass.CHAMPION] = BreakthroughDef(
    HeroClass.CHAMPION, HeroClass.WARLORD, 20, "str", 50, str_bonus=10, vit_bonus=10, talent="Indomitable"
)
BREAKTHROUGHS[HeroClass.ARCHMAGE] = BreakthroughDef(
    HeroClass.ARCHMAGE, HeroClass.STORM_CALLER, 20, "int", 50, int_bonus=10, spi_bonus=10, talent="Storm Soul"
)
BREAKTHROUGHS[HeroClass.SHARPSHOOTER] = BreakthroughDef(
    HeroClass.SHARPSHOOTER, HeroClass.GHOST_STALKER, 20, "agi", 50, agi_bonus=10, per_bonus=10, talent="Untraceable"
)
BREAKTHROUGHS[HeroClass.ASSASSIN] = BreakthroughDef(
    HeroClass.ASSASSIN, HeroClass.NIGHTSHADE, 20, "agi", 50, agi_bonus=10, cha_bonus=10, talent="Void Veil"
)

# Race → default race skills mapping
RACE_SKILLS: dict[str, list[str]] = {
    "hero":           ["rally", "second_wind"],
    "goblin":         ["ambush", "scavenge"],
    "goblin_scout":   ["ambush", "scavenge"],
    "goblin_warrior": ["ambush"],
    "goblin_chief":   ["ambush", "scavenge"],
    "wolf":           ["pack_hunt", "feral_bite"],
    "dire_wolf":      ["pack_hunt", "feral_bite"],
    "alpha_wolf":     ["pack_hunt", "feral_bite"],
    "bandit":         ["quickdraw"],
    "bandit_archer":  ["quickdraw"],
    "bandit_chief":   ["quickdraw"],
    "skeleton":       ["drain_life"],
    "zombie":         ["drain_life"],
    "lich":           ["drain_life"],
    "orc":            ["berserker_rage", "war_cry"],
    "orc_warrior":    ["berserker_rage", "war_cry"],
    "orc_warlord":    ["berserker_rage", "war_cry"],
}


# Class → available class skills mapping
CLASS_SKILLS: dict[HeroClass, list[str]] = {
    HeroClass.WARRIOR: ["power_strike", "shield_wall", "whirlwind"],
    HeroClass.RANGER:  ["quick_shot", "evasive_step", "rain_of_arrows"],
    HeroClass.MAGE:    ["arcane_bolt", "frost_shield", "fireball"],
    HeroClass.ROGUE:   ["backstab", "shadowstep", "poison_blade"],
    # Breakthroughs inherit parent class skills
    HeroClass.CHAMPION:    ["power_strike", "shield_wall", "whirlwind"],
    HeroClass.SHARPSHOOTER: ["quick_shot", "evasive_step", "rain_of_arrows"],
    HeroClass.ARCHMAGE:    ["arcane_bolt", "frost_shield", "fireball"],
    HeroClass.ASSASSIN:    ["backstab", "shadowstep", "poison_blade"],
}


# Class building type → class mapping
CLASS_BUILDING_MAP: dict[str, HeroClass] = {
    "warrior_hall":  HeroClass.WARRIOR,
    "ranger_lodge":  HeroClass.RANGER,
    "mage_tower":    HeroClass.MAGE,
    "rogue_den":     HeroClass.ROGUE,
}


# ---------------------------------------------------------------------------
# Hero Starting Gear — class-based starting equipment
# ---------------------------------------------------------------------------

HERO_STARTING_GEAR: dict[HeroClass, dict[str, str | None]] = {
    HeroClass.WARRIOR: {"weapon": "iron_sword",       "armor": "leather_vest", "accessory": None},
    HeroClass.RANGER:  {"weapon": "shortbow",         "armor": "leather_vest", "accessory": None},
    HeroClass.MAGE:    {"weapon": "apprentice_staff",  "armor": "cloth_robe",   "accessory": None},
    HeroClass.ROGUE:   {"weapon": "bandit_dagger",     "armor": "leather_vest", "accessory": None},
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def get_attr_value(attrs, attr_name: str) -> int:
    """Get attribute value by string name."""
    mapping = {"str": attrs.str_, "agi": attrs.agi, "vit": attrs.vit,
               "int": attrs.int_, "spi": attrs.spi, "wis": attrs.wis,
               "end": attrs.end, "per": attrs.per, "cha": attrs.cha}
    return mapping.get(attr_name, 0)


def can_breakthrough(hero_class: HeroClass, level: int, attrs) -> bool:
    """Check if an entity can breakthrough to the next class."""
    bt = BREAKTHROUGHS.get(hero_class)
    if bt is None:
        return False
    if level < bt.level_req:
        return False
    return get_attr_value(attrs, bt.attr_req) >= bt.attr_threshold


def available_class_skills(hero_class: HeroClass, level: int) -> list[str]:
    """Get skill IDs available for a class at a given level (ignores mastery)."""
    skill_ids = CLASS_SKILLS.get(hero_class, [])
    result = []
    for sid in skill_ids:
        sdef = SKILL_DEFS.get(sid)
        if sdef and level >= sdef.level_req:
            result.append(sid)
    return result


def can_learn_skill(
    sdef: SkillDef,
    level: int,
    known_skills: list[SkillInstance],
    class_mastery: float = 0.0,
) -> tuple[bool, str]:
    """Check whether a hero meets all requirements to learn a skill.

    Returns (can_learn, reason_if_not).
    """
    if level < sdef.level_req:
        return False, f"Requires level {sdef.level_req} (current: {level})"
    if sdef.mastery_req:
        prereq = None
        for si in known_skills:
            if si.skill_id == sdef.mastery_req:
                prereq = si
                break
        if prereq is None:
            prereq_def = SKILL_DEFS.get(sdef.mastery_req)
            prereq_name = prereq_def.name if prereq_def else sdef.mastery_req
            return False, f"Requires knowledge of {prereq_name}"
        if prereq.mastery < sdef.mastery_threshold:
            prereq_def = SKILL_DEFS.get(sdef.mastery_req)
            prereq_name = prereq_def.name if prereq_def else sdef.mastery_req
            return False, f"Requires {prereq_name} mastery {sdef.mastery_threshold:.0f}+ (current: {prereq.mastery:.0f})"
    return True, ""


# ---------------------------------------------------------------------------
# Race + Tier → Mob class mapping
# ---------------------------------------------------------------------------

# Maps (race, tier) → HeroClass archetype for mobs.
# Tier EnemyTier values: BASIC=0, SCOUT=1, WARRIOR=2, ELITE=3
RACE_CLASS_MAP: dict[tuple[str, int], HeroClass] = {
    # Goblins — small, cunning; scouts are fast, warriors are brutes, chiefs are casters
    ("goblin", 0): HeroClass.SCOUT,       # goblin (basic) — nimble raider
    ("goblin", 1): HeroClass.SCOUT,       # goblin_scout — fast flanker
    ("goblin", 2): HeroClass.BRUTE,       # goblin_warrior — stronger melee
    ("goblin", 3): HeroClass.CASTER,      # goblin_chief — shamanic magic
    # Wolves — natural predators; all BEAST except alpha (BRUTE)
    ("wolf", 0): HeroClass.BEAST,         # wolf — pack hunter
    ("wolf", 1): HeroClass.BEAST,         # dire_wolf — bigger, faster
    ("wolf", 2): HeroClass.BEAST,         # dire_wolf (warrior tier)
    ("wolf", 3): HeroClass.BRUTE,         # alpha_wolf — pack leader, raw power
    # Bandits — human rogues; scouts are fast, warriors are brutes, chiefs are tactical
    ("bandit", 0): HeroClass.SCOUT,       # bandit — agile raider
    ("bandit", 1): HeroClass.SCOUT,       # bandit_archer — ranged flanker
    ("bandit", 2): HeroClass.BRUTE,       # bandit (warrior) — heavy hitter
    ("bandit", 3): HeroClass.BRUTE,       # bandit_chief — brutal leader
    # Undead — shambling horrors; basic are tanks, higher tiers gain magic
    ("undead", 0): HeroClass.TANK,        # skeleton — durable, slow
    ("undead", 1): HeroClass.CASTER,      # skeleton_mage — ranged dark magic
    ("undead", 2): HeroClass.TANK,        # zombie (warrior) — armored dead
    ("undead", 3): HeroClass.CASTER,      # lich — powerful necromancer
    # Orcs — brutal warriors; everything is brute or tank
    ("orc", 0): HeroClass.BRUTE,          # orc — raw muscle
    ("orc", 1): HeroClass.SCOUT,          # orc (scout) — orc skirmisher
    ("orc", 2): HeroClass.BRUTE,          # orc_warrior — heavy fighter
    ("orc", 3): HeroClass.TANK,           # orc_warlord — armored commander
}


def mob_class_for(race: str, tier: int) -> HeroClass:
    """Look up the mob archetype class for a given race and tier."""
    return RACE_CLASS_MAP.get((race, tier), HeroClass.BRUTE)
