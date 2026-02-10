"""Trait system — Rimworld-style discrete personality traits.

Each entity gets 2-4 traits at spawn.  Traits modify utility scores
in the AI goal-evaluation layer and can provide passive stat bonuses.

Incompatible trait pairs (e.g. AGGRESSIVE + CAUTIOUS) are enforced
during assignment so an entity never has contradictory personality.

Key types:
  TraitDef          — immutable blueprint for one trait
  UtilityBonus      — typed additive modifiers for goal scoring
  TraitStatModifiers— typed passive stat modifiers
  TraitRegistry     — central registry for definitions, compatibility, race bias
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import TYPE_CHECKING

from pydantic.dataclasses import dataclass as pydantic_dataclass

from src.core.enums import TraitType

if TYPE_CHECKING:
    from src.systems.rng import DeterministicRNG


# ---------------------------------------------------------------------------
# Trait definition
# ---------------------------------------------------------------------------

@pydantic_dataclass(frozen=True)
class TraitDef:
    """Immutable blueprint describing one trait's effects."""

    trait_type: int          # TraitType enum value
    name: str
    description: str
    # Utility score modifiers (additive bonuses to goal utility)
    combat_utility: float = 0.0     # Hunt/attack goal
    flee_utility: float = 0.0       # Flee/retreat goal
    explore_utility: float = 0.0    # Explore/wander goal
    loot_utility: float = 0.0       # Loot/gather goal
    trade_utility: float = 0.0      # Shop/trade goal
    rest_utility: float = 0.0       # Rest/heal goal
    craft_utility: float = 0.0      # Craft/harvest goal
    social_utility: float = 0.0     # Guild/interact goal
    # Passive stat multipliers (1.0 = no change)
    atk_mult: float = 1.0
    def_mult: float = 1.0
    matk_mult: float = 1.0
    mdef_mult: float = 1.0
    crit_bonus: float = 0.0
    evasion_bonus: float = 0.0
    vision_bonus: int = 0
    hp_regen_mult: float = 1.0
    interaction_speed_mult: float = 1.0
    # Elemental damage bonus multipliers (1.0 = no change, >1 = bonus dmg)
    fire_dmg_mult: float = 1.0
    ice_dmg_mult: float = 1.0
    lightning_dmg_mult: float = 1.0
    dark_dmg_mult: float = 1.0
    # Flee HP threshold modifier (additive; positive = flee sooner)
    flee_threshold_mod: float = 0.0


# ---------------------------------------------------------------------------
# Trait registry
# ---------------------------------------------------------------------------

TRAIT_DEFS: dict[int, TraitDef] = {}


def _reg(t: TraitDef) -> None:
    TRAIT_DEFS[t.trait_type] = t


# -- Combat disposition --
_reg(TraitDef(
    TraitType.AGGRESSIVE, "Aggressive",
    "Seeks combat eagerly, lower flee threshold.",
    combat_utility=0.3, flee_utility=-0.2, flee_threshold_mod=-0.1,
    atk_mult=1.05,
))
_reg(TraitDef(
    TraitType.CAUTIOUS, "Cautious",
    "Prefers safety, flees sooner, avoids risky fights.",
    combat_utility=-0.2, flee_utility=0.3, rest_utility=0.1,
    flee_threshold_mod=0.1, def_mult=1.05,
))
_reg(TraitDef(
    TraitType.BRAVE, "Brave",
    "Resists fleeing even at low HP.",
    combat_utility=0.15, flee_utility=-0.3, flee_threshold_mod=-0.15,
))
_reg(TraitDef(
    TraitType.COWARDLY, "Cowardly",
    "Flees at the first sign of danger.",
    combat_utility=-0.3, flee_utility=0.4, explore_utility=-0.1,
    flee_threshold_mod=0.2,
))
_reg(TraitDef(
    TraitType.BLOODTHIRSTY, "Bloodthirsty",
    "Craves violence, bonus crit in combat.",
    combat_utility=0.4, flee_utility=-0.3, rest_utility=-0.1,
    crit_bonus=0.05, flee_threshold_mod=-0.1,
))

# -- Social / economic --
_reg(TraitDef(
    TraitType.GREEDY, "Greedy",
    "Prioritises loot and gold above all else.",
    loot_utility=0.4, trade_utility=0.2, combat_utility=-0.1,
))
_reg(TraitDef(
    TraitType.GENEROUS, "Generous",
    "Willing to share, less focused on hoarding.",
    loot_utility=-0.1, social_utility=0.2, trade_utility=-0.1,
))
_reg(TraitDef(
    TraitType.CHARISMATIC, "Charismatic",
    "Better trade prices and social interactions.",
    trade_utility=0.3, social_utility=0.3,
))
_reg(TraitDef(
    TraitType.LONER, "Loner",
    "Prefers solitude, avoids social activities.",
    social_utility=-0.3, explore_utility=0.2,
))

# -- Work ethic --
_reg(TraitDef(
    TraitType.DILIGENT, "Diligent",
    "Works faster, rests less.",
    craft_utility=0.2, rest_utility=-0.15,
    interaction_speed_mult=1.15,
))
_reg(TraitDef(
    TraitType.LAZY, "Lazy",
    "Slow worker, prefers resting.",
    craft_utility=-0.2, rest_utility=0.3, explore_utility=-0.1,
    interaction_speed_mult=0.85,
))
_reg(TraitDef(
    TraitType.CURIOUS, "Curious",
    "Drawn to unexplored areas and new discoveries.",
    explore_utility=0.4, loot_utility=0.1,
))

# -- Combat style --
_reg(TraitDef(
    TraitType.BERSERKER, "Berserker",
    "Gains power at low HP, ignores some defense.",
    combat_utility=0.2, flee_utility=-0.2,
    atk_mult=1.1, def_mult=0.9, flee_threshold_mod=-0.1,
))
_reg(TraitDef(
    TraitType.TACTICAL, "Tactical",
    "Prefers skills over basic attacks, better positioning.",
    combat_utility=0.1,
))
_reg(TraitDef(
    TraitType.RESILIENT, "Resilient",
    "Faster HP regen, tougher overall.",
    rest_utility=0.1,
    hp_regen_mult=1.2, def_mult=1.05,
))

# -- Magical affinity --
_reg(TraitDef(
    TraitType.ARCANE_GIFTED, "Arcane Gifted",
    "Natural talent for magic, bonus MATK.",
    matk_mult=1.1,
))
_reg(TraitDef(
    TraitType.SPIRIT_TOUCHED, "Spirit Touched",
    "Connected to the spirit realm, bonus MDEF.",
    mdef_mult=1.1,
))
_reg(TraitDef(
    TraitType.ELEMENTALIST, "Elementalist",
    "Affinity for elemental magic. Bonus damage with all elements.",
    matk_mult=1.05,
    fire_dmg_mult=1.15, ice_dmg_mult=1.15,
    lightning_dmg_mult=1.15, dark_dmg_mult=1.10,
))

# -- Perception / awareness --
_reg(TraitDef(
    TraitType.KEEN_EYED, "Keen-Eyed",
    "Superior vision and detection.",
    explore_utility=0.15, loot_utility=0.1,
    vision_bonus=2,
))
_reg(TraitDef(
    TraitType.OBLIVIOUS, "Oblivious",
    "Reduced awareness but higher focus on current task.",
    explore_utility=-0.15,
    vision_bonus=-1, interaction_speed_mult=1.1,
))


# ---------------------------------------------------------------------------
# Incompatible pairs — entities cannot have both traits
# ---------------------------------------------------------------------------

INCOMPATIBLE_PAIRS: list[tuple[int, int]] = [
    (TraitType.AGGRESSIVE, TraitType.CAUTIOUS),
    (TraitType.AGGRESSIVE, TraitType.COWARDLY),
    (TraitType.BRAVE, TraitType.COWARDLY),
    (TraitType.BLOODTHIRSTY, TraitType.CAUTIOUS),
    (TraitType.GREEDY, TraitType.GENEROUS),
    (TraitType.DILIGENT, TraitType.LAZY),
    (TraitType.BERSERKER, TraitType.CAUTIOUS),
    (TraitType.KEEN_EYED, TraitType.OBLIVIOUS),
    (TraitType.LONER, TraitType.CHARISMATIC),
]

# Build a fast lookup set for incompatibility checks
_INCOMPAT_SET: set[tuple[int, int]] = set()
for a, b in INCOMPATIBLE_PAIRS:
    _INCOMPAT_SET.add((a, b))
    _INCOMPAT_SET.add((b, a))


def are_compatible(trait_a: int, trait_b: int) -> bool:
    """Check if two traits can coexist on one entity."""
    return (trait_a, trait_b) not in _INCOMPAT_SET


# ---------------------------------------------------------------------------
# Race-biased trait pools — some races are more likely to get certain traits
# ---------------------------------------------------------------------------

# Maps race prefix -> list of (TraitType, weight) for biased selection
# Traits not in the list still have a base weight of 1.0
RACE_TRAIT_BIAS: dict[str, list[tuple[int, float]]] = {
    "hero": [
        (TraitType.BRAVE, 2.0),
        (TraitType.CURIOUS, 1.5),
        (TraitType.DILIGENT, 1.5),
        (TraitType.TACTICAL, 1.5),
    ],
    "goblin": [
        (TraitType.GREEDY, 2.5),
        (TraitType.COWARDLY, 2.0),
        (TraitType.CAUTIOUS, 1.5),
    ],
    "wolf": [
        (TraitType.AGGRESSIVE, 2.5),
        (TraitType.BLOODTHIRSTY, 2.0),
        (TraitType.KEEN_EYED, 1.5),
    ],
    "bandit": [
        (TraitType.GREEDY, 2.0),
        (TraitType.AGGRESSIVE, 1.5),
        (TraitType.LONER, 1.5),
    ],
    "undead": [
        (TraitType.RESILIENT, 2.0),
        (TraitType.OBLIVIOUS, 1.5),
        (TraitType.SPIRIT_TOUCHED, 2.0),
    ],
    "orc": [
        (TraitType.BERSERKER, 2.5),
        (TraitType.BRAVE, 2.0),
        (TraitType.AGGRESSIVE, 2.0),
    ],
}


# ---------------------------------------------------------------------------
# Assignment: pick 2-4 compatible traits for an entity
# ---------------------------------------------------------------------------

ALL_TRAIT_TYPES: list[int] = [t.value for t in TraitType]


def assign_traits(
    rng: DeterministicRNG,
    domain_id: int,
    entity_id: int,
    tick: int,
    race_prefix: str = "",
    count_min: int = 2,
    count_max: int = 4,
) -> list[int]:
    """Randomly assign traits to an entity, respecting incompatibility.

    Uses weighted selection biased by race.  Returns a list of TraitType
    int values.
    """
    from src.core.enums import Domain

    # Determine how many traits
    num_traits = rng.next_int(domain_id, entity_id, tick + 100, count_min, count_max)

    # Build weighted pool
    base_weight = 1.0
    weight_map: dict[int, float] = {t: base_weight for t in ALL_TRAIT_TYPES}
    # Apply race bias
    for prefix, biases in RACE_TRAIT_BIAS.items():
        if race_prefix.startswith(prefix):
            for trait_type, weight in biases:
                weight_map[trait_type] = weight
            break

    chosen: list[int] = []
    available = list(ALL_TRAIT_TYPES)

    for i in range(num_traits):
        if not available:
            break

        # Compute cumulative weights for available traits
        weights = [weight_map.get(t, base_weight) for t in available]
        total = sum(weights)
        if total <= 0:
            break

        # Weighted random selection using RNG
        roll = rng.next_float(domain_id, entity_id, tick + 200 + i) * total
        cumulative = 0.0
        selected_idx = 0
        for idx, w in enumerate(weights):
            cumulative += w
            if roll <= cumulative:
                selected_idx = idx
                break

        selected = available[selected_idx]
        chosen.append(selected)

        # Remove selected and all incompatible traits from pool
        available = [
            t for t in available
            if t != selected and are_compatible(t, selected)
        ]

    return chosen


# ---------------------------------------------------------------------------
# Typed aggregation dataclasses
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class UtilityBonus:
    """Typed additive modifiers for AI goal scoring."""
    combat: float = 0.0
    flee: float = 0.0
    explore: float = 0.0
    loot: float = 0.0
    trade: float = 0.0
    rest: float = 0.0
    craft: float = 0.0
    social: float = 0.0


@dataclass(slots=True)
class TraitStatModifiers:
    """Typed passive stat modifiers aggregated from traits.

    Multiplicative fields start at 1.0 (no change).
    Additive fields start at 0.0.
    """
    atk_mult: float = 1.0
    def_mult: float = 1.0
    matk_mult: float = 1.0
    mdef_mult: float = 1.0
    crit_bonus: float = 0.0
    evasion_bonus: float = 0.0
    vision_bonus: int = 0
    hp_regen_mult: float = 1.0
    interaction_speed_mult: float = 1.0
    fire_dmg_mult: float = 1.0
    ice_dmg_mult: float = 1.0
    lightning_dmg_mult: float = 1.0
    dark_dmg_mult: float = 1.0
    flee_threshold_mod: float = 0.0


# ---------------------------------------------------------------------------
# Aggregate trait effects for an entity
# ---------------------------------------------------------------------------

def aggregate_trait_utility(traits: list[int]) -> UtilityBonus:
    """Sum utility modifiers across all traits."""
    bonus = UtilityBonus()
    for t in traits:
        tdef = TRAIT_DEFS.get(t)
        if tdef is None:
            continue
        bonus.combat += tdef.combat_utility
        bonus.flee += tdef.flee_utility
        bonus.explore += tdef.explore_utility
        bonus.loot += tdef.loot_utility
        bonus.trade += tdef.trade_utility
        bonus.rest += tdef.rest_utility
        bonus.craft += tdef.craft_utility
        bonus.social += tdef.social_utility
    return bonus


def aggregate_trait_stats(traits: list[int]) -> TraitStatModifiers:
    """Aggregate passive stat modifiers from all traits."""
    mods = TraitStatModifiers()
    for t in traits:
        tdef = TRAIT_DEFS.get(t)
        if tdef is None:
            continue
        mods.atk_mult *= tdef.atk_mult
        mods.def_mult *= tdef.def_mult
        mods.matk_mult *= tdef.matk_mult
        mods.mdef_mult *= tdef.mdef_mult
        mods.crit_bonus += tdef.crit_bonus
        mods.evasion_bonus += tdef.evasion_bonus
        mods.vision_bonus += tdef.vision_bonus
        mods.hp_regen_mult *= tdef.hp_regen_mult
        mods.interaction_speed_mult *= tdef.interaction_speed_mult
        mods.fire_dmg_mult *= tdef.fire_dmg_mult
        mods.ice_dmg_mult *= tdef.ice_dmg_mult
        mods.lightning_dmg_mult *= tdef.lightning_dmg_mult
        mods.dark_dmg_mult *= tdef.dark_dmg_mult
        mods.flee_threshold_mod += tdef.flee_threshold_mod
    return mods
