"""Status effect system — temporary buffs and debuffs on entities.

Design:
  - Effects are lightweight dataclasses attached to an entity.
  - Each effect has a type, stat multipliers, and a remaining duration (ticks).
  - The WorldLoop ticks down durations and removes expired effects.
  - Entity.effective_*() methods query active effects for multipliers.
  - New effect types can be added by extending EffectType and creating
    factory functions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, unique


@unique
class EffectType(IntEnum):
    """Categories of status effects.  Extend to add new buff/debuff families."""

    TERRITORY_DEBUFF = 0      # Stat penalty for being on hostile territory
    TERRITORY_BUFF = 1        # Stat bonus for being on home territory
    POISON = 2                # DoT
    BERSERK = 3               # ATK up, DEF down
    SHIELD = 4                # Temporary DEF boost
    HASTE = 5                 # SPD boost
    SLOW = 6                  # SPD penalty
    SKILL_BUFF = 7            # Buff from a skill (self / ally)
    SKILL_DEBUFF = 8          # Debuff from a skill (applied to enemy)
    
    # Elemental States
    FROZEN = 10
    WET = 11
    SHOCKED = 12
    BURNED = 13
    SUPPRESSION = 14          # Regional fear effect
    CONQUERED_DEBUFF = 15     # Heavy penalty in conquered regions
    RESTED = 16               # Milestone 9: Well-Rested buff from Town Inn


@dataclass(slots=True)
class StatusEffect:
    """A temporary modifier applied to an entity.

    Multipliers are applied multiplicatively to base stats.
    A value of 1.0 means no change; < 1.0 is a debuff; > 1.0 is a buff.
    """

    effect_type: EffectType
    remaining_ticks: int        # -1 = permanent until explicitly removed, >0 = timed
    source: str = ""            # Human-readable origin, e.g. "goblin_camp_territory"

    # Stat multipliers (1.0 = neutral)
    atk_mult: float = 1.0
    def_mult: float = 1.0
    spd_mult: float = 1.0
    crit_mult: float = 1.0
    evasion_mult: float = 1.0
    max_hp_mult: float = 1.0
    xp_mult: float = 1.0 # Milestone 9 extension

    # Direct stat mods per tick
    hp_per_tick: int = 0
    stamina_per_tick: int = 0

    def tick(self) -> None:
        """Called each world tick if duration > 0."""
        if self.remaining_ticks > 0:
            self.remaining_ticks -= 1

    @property
    def expired(self) -> bool:
        """Expired if duration reached 0."""
        return self.remaining_ticks == 0

    def copy(self) -> StatusEffect:
        """Create a full copy (used when applying templates)."""
        return StatusEffect(
            effect_type=self.effect_type,
            remaining_ticks=self.remaining_ticks,
            source=self.source,
            atk_mult=self.atk_mult,
            def_mult=self.def_mult,
            spd_mult=self.spd_mult,
            crit_mult=self.crit_mult,
            evasion_mult=self.evasion_mult,
            max_hp_mult=self.max_hp_mult,
            xp_mult=self.xp_mult,
            hp_per_tick=self.hp_per_tick,
            stamina_per_tick=self.stamina_per_tick,
        )


# =====================================================================
# Factory functions for common effects
# =====================================================================

def territory_debuff(source: str, duration: int = -1, atk_mult: float = 0.8, def_mult: float = 0.8) -> StatusEffect:
    """Create a stat penalty for hostile territory."""
    return StatusEffect(
        effect_type=EffectType.TERRITORY_DEBUFF,
        remaining_ticks=duration,
        source=source,
        atk_mult=atk_mult,
        def_mult=def_mult,
    )


def territory_buff(source: str, duration: int = -1, atk_mult: float = 1.2, def_mult: float = 1.2) -> StatusEffect:
    """Create a stat bonus for home territory."""
    return StatusEffect(
        effect_type=EffectType.TERRITORY_BUFF,
        remaining_ticks=duration,
        source=source,
        atk_mult=atk_mult,
        def_mult=def_mult,
    )


def skill_buff(source: str, duration: int, atk_mod: float = 0.0, def_mod: float = 0.0, crit_mod: float = 0.0) -> StatusEffect:
    """Generic buff from a skill (e.g. atk_mod=0.15 → +15% ATK)."""
    return StatusEffect(
        effect_type=EffectType.SKILL_BUFF,
        remaining_ticks=duration,
        source=source,
        atk_mult=1.0 + atk_mod,
        def_mult=1.0 + def_mod,
        crit_mult=1.0 + crit_mod,
    )


def skill_debuff(source: str, duration: int, atk_mod: float = 0.0, def_mod: float = 0.0) -> StatusEffect:
    """Generic debuff from a skill (e.g. atk_mod=-0.15 → -15% ATK)."""
    return StatusEffect(
        effect_type=EffectType.SKILL_DEBUFF,
        remaining_ticks=duration,
        source=source,
        atk_mult=1.0 + atk_mod,
        def_mult=1.0 + def_mod,
    )


def skill_effect(source: str = "", duration: int = 1, atk_mod: float = 0.0, def_mod: float = 0.0, spd_mod: float = 0.0, crit_mod: float = 0.0, hp_per_tick: int = 0, is_debuff: bool = False) -> StatusEffect:
    """Legacy factory for skill-based effects (M6 compatibility)."""
    etype = EffectType.SKILL_DEBUFF if is_debuff else EffectType.SKILL_BUFF
    return StatusEffect(
        effect_type=etype,
        remaining_ticks=duration,
        source=source,
        atk_mult=1.0 + atk_mod,
        def_mult=1.0 + def_mod,
        spd_mult=1.0 + spd_mod,
        crit_mult=1.0 + crit_mod,
        hp_per_tick=hp_per_tick,
    )


def poison_effect(duration: int = 10, damage: int = 2, source: str = "poison") -> StatusEffect:
    """Poison DoT."""
    return StatusEffect(
        effect_type=EffectType.POISON,
        remaining_ticks=duration,
        source=source,
        hp_per_tick=-damage,
    )


def haste_effect(duration: int = 20, speed_mult: float = 1.5) -> StatusEffect:
    """SPD boost."""
    return StatusEffect(
        effect_type=EffectType.HASTE,
        remaining_ticks=duration,
        source="haste",
        spd_mult=speed_mult,
    )


def slow_effect(duration: int = 15, speed_mult: float = 0.5) -> StatusEffect:
    """SPD penalty."""
    return StatusEffect(
        effect_type=EffectType.SLOW,
        remaining_ticks=duration,
        source="slow",
        spd_mult=speed_mult,
    )


def frozen_effect(duration: int = 5) -> StatusEffect:
    """Freeze target (SPD down drastically)."""
    return StatusEffect(
        effect_type=EffectType.FROZEN,
        remaining_ticks=duration,
        source="frozen",
        spd_mult=0.0,  # Immobilized
    )


def wet_effect(duration: int = 8) -> StatusEffect:
    """Wet target (Lightning vulnerability)."""
    return StatusEffect(
        effect_type=EffectType.WET,
        remaining_ticks=duration,
        source="wet",
        def_mult=0.9,
    )


def burned_effect(duration: int = 5, damage: int = 3) -> StatusEffect:
    """Burn target (DoT)."""
    return StatusEffect(
        effect_type=EffectType.BURNED,
        remaining_ticks=duration,
        source="burned",
        hp_per_tick=-damage,
    )


def suppression_effect(duration: int = 100) -> StatusEffect:
    """Create a suppression debuff (regional fear after many deaths)."""
    return StatusEffect(
        effect_type=EffectType.SUPPRESSION,
        remaining_ticks=duration,
        source="regional_suppression",
        atk_mult=0.8,
        spd_mult=0.8,
    )


def conquered_debuff(duration: int = 2) -> StatusEffect:
    """Create a conquered region debuff (stronghold presence)."""
    return StatusEffect(
        effect_type=EffectType.CONQUERED_DEBUFF,
        remaining_ticks=duration,
        source="conquered_stronghold",
        atk_mult=0.8,
        def_mult=0.8,
        spd_mult=0.9, # Slight slowdown
    )


def well_rested_effect(duration: int = 100) -> StatusEffect:
    """Create a Well-Rested buff (+10% Max HP, +20% XP Gain)."""
    return StatusEffect(
        effect_type=EffectType.RESTED,
        remaining_ticks=duration,
        source="well_rested",
        max_hp_mult=1.1,
        xp_mult=1.2,
    )
