"""
Attribute contribution terms of the combat-stat derivation (Mechanics Bible 01 §2).

This is the single definition of how core attributes feed max_hp / atk / def / evasion. Both the
derivation (`LevelingService.recalculate_combat_stats`) and the spawn-time residual
(`residual_base_terms`) call it, so the two cannot drift apart.
"""
from __future__ import annotations

from typing import Tuple


def attribute_stat_terms(attributes) -> Tuple[int, int, int, float]:
    """Return the (max_hp, atk, def, evasion) contributions of `attributes`."""
    return (
        attributes.vitality * 2 + int(attributes.endurance * 0.5),
        int(attributes.strength * 0.5),
        int(attributes.vitality * 0.3),
        attributes.agility * 0.001,
    )


def residual_base_terms(combat, attributes) -> Tuple[int, int, int, float]:
    """
    Return the (base_hp, base_atk, base_def, base_evasion) such that
    ``base + attribute_stat_terms(attributes) == the spawned stat`` for this entity.

    The residual is NOT a declared stat. Stat profiles declare FINAL spawned values, while the
    derivation treats its base as a term attributes are then added to; the residual reconciles the
    two. It is deliberately unclamped: a profile stat below its own attribute contribution (e.g. a
    `worker` with def 0 and vitality 5) yields a negative term, and clamping it would break the
    exact round trip that is the point of storing it.
    """
    hp_t, atk_t, def_t, eva_t = attribute_stat_terms(attributes)
    return (
        combat.max_hp - hp_t,
        combat.atk - atk_t,
        combat.def_stat - def_t,
        combat.evasion - eva_t,
    )
