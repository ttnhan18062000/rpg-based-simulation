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

    # Flat modifiers (applied after multipliers)
    hp_per_tick: int = 0        # Positive = regen, negative = DoT

    @property
    def expired(self) -> bool:
        return self.remaining_ticks == 0

    def tick(self) -> None:
        """Decrement remaining duration.  Does nothing if permanent (-1)."""
        if self.remaining_ticks > 0:
            self.remaining_ticks -= 1

    def copy(self) -> StatusEffect:
        return StatusEffect(
            effect_type=self.effect_type,
            remaining_ticks=self.remaining_ticks,
            source=self.source,
            atk_mult=self.atk_mult,
            def_mult=self.def_mult,
            spd_mult=self.spd_mult,
            crit_mult=self.crit_mult,
            evasion_mult=self.evasion_mult,
            hp_per_tick=self.hp_per_tick,
        )


# ---------------------------------------------------------------------------
# Factory helpers for common effects
# ---------------------------------------------------------------------------

def territory_debuff(
    atk_mult: float = 0.7,
    def_mult: float = 0.7,
    spd_mult: float = 0.85,
    duration: int = 3,
    source: str = "enemy_territory",
) -> StatusEffect:
    """Create a territory intrusion debuff."""
    return StatusEffect(
        effect_type=EffectType.TERRITORY_DEBUFF,
        remaining_ticks=duration,
        source=source,
        atk_mult=atk_mult,
        def_mult=def_mult,
        spd_mult=spd_mult,
    )


def skill_effect(
    atk_mod: float = 0.0,
    def_mod: float = 0.0,
    spd_mod: float = 0.0,
    crit_mod: float = 0.0,
    evasion_mod: float = 0.0,
    hp_per_tick: int = 0,
    duration: int = 3,
    source: str = "skill",
    is_debuff: bool = False,
) -> StatusEffect:
    """Create a buff or debuff StatusEffect from skill modifiers.

    Modifiers are additive percentages (e.g. atk_mod=0.2 → +20% ATK → mult 1.2).
    Negative modifiers become debuffs (e.g. atk_mod=-0.15 → -15% ATK → mult 0.85).
    """
    etype = EffectType.SKILL_DEBUFF if is_debuff else EffectType.SKILL_BUFF
    return StatusEffect(
        effect_type=etype,
        remaining_ticks=duration,
        source=source,
        atk_mult=1.0 + atk_mod,
        def_mult=1.0 + def_mod,
        spd_mult=1.0 + spd_mod,
        crit_mult=1.0 + crit_mod,
        evasion_mult=1.0 + evasion_mod,
        hp_per_tick=hp_per_tick,
    )


def territory_buff(
    atk_mult: float = 1.1,
    def_mult: float = 1.1,
    duration: int = 3,
    source: str = "home_territory",
) -> StatusEffect:
    """Create a home territory buff."""
    return StatusEffect(
        effect_type=EffectType.TERRITORY_BUFF,
        remaining_ticks=duration,
        source=source,
        atk_mult=atk_mult,
        def_mult=def_mult,
    )
