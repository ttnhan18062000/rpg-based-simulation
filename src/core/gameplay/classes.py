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

from src.core.models.enums import (
    DamageType, HeroClass, SkillType, SkillTarget, Element,
    SkillTypeSer, SkillTargetSer, HeroClassSer, DamageTypeSer, ElementSer
)

# ---------------------------------------------------------------------------
# Skill definition
# ---------------------------------------------------------------------------


@pydantic_dataclass(frozen=True)
class SkillDef:
    """Immutable skill template/definition."""
    skill_id: str
    name: str
    description: str
    skill_type: SkillTypeSer
    target: SkillTargetSer
    class_req: HeroClassSer       # NONE = race skill (no class required)
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
    damage_type: DamageTypeSer = DamageType.PHYSICAL
    element: ElementSer = Element.NONE


# ---------------------------------------------------------------------------
# Skill Metadata (Legacy mapping to be replaced by JSON data)
# ---------------------------------------------------------------------------

# Skills that deal magical damage (use MATK instead of ATK)
_MAGICAL_SKILLS = frozenset({
    "arcane_bolt", "frost_shield", "mana_surge", "drain_life",
})

# Skill → element mapping (skills not listed default to NONE)
_SKILL_ELEMENTS: dict[str, Element] = {
    "frost_shield": Element.ICE,
    "arcane_bolt": Element.NONE,
    "drain_life": Element.DARK,
    "poison_blade": Element.DARK,
}


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
        """Cooldown reduced by mastery. -10% at tier 2, -20% at tier 4."""
        mult = 1.0
        if self.mastery >= 50.0:
            mult -= 0.10
        if self.mastery >= 100.0:
            mult -= 0.10  # Total -20%
        return max(1, int(base_cd * mult))

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
    class_id: HeroClassSer
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
    breakthrough_class: HeroClassSer = HeroClass.NONE
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
    # Starting gear & Skills
    starting_gear: dict[str, str | None] = field(default_factory=dict)
    class_skills: list[str] = field(default_factory=list)


@pydantic_dataclass(frozen=True)
class BreakthroughDef:
    """Breakthrough (promotion) definition."""
    from_class: HeroClassSer
    to_class: HeroClassSer
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
BREAKTHROUGHS: dict[HeroClass, BreakthroughDef] = {}

# ---------------------------------------------------------------------------
# Backward-compatible computed shims
# ---------------------------------------------------------------------------
# These properties let old consumer code (entity_builder, __main__, etc.)
# continue to reference RACE_SKILLS / CLASS_SKILLS / HERO_STARTING_GEAR
# while the actual data lives in RACE_PROFILES and CLASS_DEFS.

class _DictShim(dict):
    """Dict-like wrapper that lazily computes values from a registry."""
    def __init__(self, compute_fn, keys_fn=None):
        super().__init__()
        self._compute_fn = compute_fn
        self._keys_fn = keys_fn
    def __getitem__(self, key):
        return self._compute_fn(key)
    def get(self, key, default=None):
        val = self._compute_fn(key)
        return val if val is not None else default
    def __contains__(self, key):
        val = self._compute_fn(key)
        return val is not None and val != []
    def __iter__(self):
        if self._keys_fn:
            return iter(self._keys_fn())
        return super().__iter__()
    def __len__(self):
        if self._keys_fn:
            return len(self._keys_fn())
        return super().__len__()
    def items(self):
        if self._keys_fn:
            return [(k, self._compute_fn(k)) for k in self._keys_fn()]
        return super().items()

def _race_skills_lookup(race: str) -> list[str]:
    from src.core.models.enums import RACE_PROFILES
    profile = RACE_PROFILES.get(race)
    return list(profile.starting_skills) if profile else []

def _class_skills_lookup(hero_class) -> list[str]:
    cdef = CLASS_DEFS.get(hero_class)
    return list(cdef.class_skills) if cdef else []

def _hero_starting_gear_lookup(hero_class) -> dict[str, str | None]:
    cdef = CLASS_DEFS.get(hero_class)
    return dict(cdef.starting_gear) if cdef else {}

def _race_class_lookup(key) -> HeroClass:
    # key is (race, tier)
    if not isinstance(key, tuple): return HeroClass.NONE
    race, tier = key
    from src.core.world.spawn_config import SPAWN_CONFIGS
    cfg = SPAWN_CONFIGS.get((race, tier))
    if cfg:
        # Archetype is a HeroClass enum or int
        return HeroClass(cfg.archetype) if cfg.archetype else HeroClass.NONE
    return HeroClass.NONE

RACE_SKILLS = _DictShim(_race_skills_lookup)
CLASS_SKILLS = _DictShim(_class_skills_lookup)
HERO_STARTING_GEAR = _DictShim(_hero_starting_gear_lookup)
RACE_CLASS_MAP = _DictShim(_race_class_lookup)

# --- Building mapping remains as it's static meta ---
CLASS_BUILDING_MAP: dict[str, HeroClass] = {
    "warrior_hall":  HeroClass.WARRIOR,
    "ranger_lodge":  HeroClass.RANGER,
    "mage_tower":    HeroClass.MAGE,
    "rogue_den":     HeroClass.ROGUE,
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
    cdef = CLASS_DEFS.get(hero_class)
    if not cdef:
        return []
    
    skill_ids = cdef.class_skills
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

def mob_class_for(race: str, tier: int) -> HeroClass:
    """Look up the mob archetype class for a given race and tier."""
    from src.core.world.spawn_config import SPAWN_CONFIGS
    from src.core.models.enums import EnemyTier
    
    cfg = SPAWN_CONFIGS.get((race, EnemyTier(tier)))
    return cfg.archetype if cfg else HeroClass.BRUTE
