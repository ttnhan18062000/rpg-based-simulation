"""Natural healing (owner decision 42, memo row 65): every living body heals a little all the time, faster asleep or resting.

A body of ``max_hp`` regains 1 HP every ``round(AWAKE_TICKS / max_hp)`` ticks awake and every ``round(RESTING_TICKS / max_hp)`` ticks in a
held SLEEP or REST (a collapse included), so a body of any size is whole again in about 4 days awake or 2 days resting. The rates are named
placeholders (D33); per-kind rates come with the body properties in M1.

Healing follows the same need stages as starvation (D36) and sleep debt (D41): none at or past the starving line, half speed while weakened by
hunger or by sleep debt (the worse of the two decides). Everything is derived from fields that already exist (hunger, sleep debt, hp, max_hp,
the task, the tick and the entity id): no new state field. The shape mirrors ``starvation.hp_loss``: staggered by entity id and indexed by the
life-due ordinal, so a governor that raises the lifecycle cadence does not skip the multiples.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.core.state import BiologicalComponent, CombatComponent
from src.engine.sleep_debt import recovery_scale as sleep_scale
from src.engine.starvation import STARVING_LINE
from src.engine.starvation import recovery_scale as hunger_scale


@dataclass(frozen=True, slots=True)
class HealingTable:
    """The healing periods, tuned in this one place."""
    awake_ticks: int = 9600    # ticks for a body to regain full health awake (4 days at 1 tick = 36 s)
    resting_ticks: int = 4800  # the same asleep or resting (2 days)


HEALING = HealingTable()


def heal_period(max_hp: int, resting: bool, scale: float) -> int:
    """Ticks between the 1 HP gains of a body of ``max_hp``: its table period, stretched by ``1 / scale`` while weakened."""
    whole = HEALING.resting_ticks if resting else HEALING.awake_ticks
    return max(1, round(whole / max(1, max_hp) / max(scale, 1e-9)))


def hp_gain(combat: CombatComponent, bio: BiologicalComponent, resting: bool, life_ordinal: int, entity_id: int) -> int:
    """HP regained on this life-due tick: 1 once every ``heal_period`` ticks, else 0. Never past ``max_hp``.

    ``life_ordinal`` is ``tick // lifecycle_cadence`` (the life-due ordinal, as in ``starvation.hp_loss``). At or past the starving line nothing
    heals; the period doubles while weakened by hunger or sleep debt (the worse of the two decides)."""
    if combat.hp <= 0 or combat.hp >= combat.max_hp or bio.hunger >= STARVING_LINE:
        return 0
    period = heal_period(combat.max_hp, resting, min(hunger_scale(bio.hunger), sleep_scale(bio.sleep_debt)))
    return 1 if (life_ordinal + entity_id) % period == 0 else 0
