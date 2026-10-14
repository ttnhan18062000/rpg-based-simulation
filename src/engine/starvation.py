"""Staged starvation (SURV-02 amendment, owner decision 36): weak first, then slow loss of health, death over days.

Past the hunger line a person first weakens (recovers more slowly and fights worse) and only then loses health, slowly: a
full-health body dies ``DEATH_TICKS`` after crossing the starving line (2.5 days at 1 tick = 36 s), a hurt one sooner. The old rule
(2 HP per tick at hunger >= 95) killed a person about 50 ticks (half an hour) after the line.

Every stage is derived from fields that already exist (``BiologicalComponent.hunger``, ``CombatComponent.hp`` / ``max_hp``, the tick and
the entity id): no new state field. ``STARVATION`` is the one place these values are tuned; moving them into content is a later step.
The "hungry" stage (hunger above 70) is the existing cognitive capacity degradation
(``strategy/cognition_capacity.py``) and is not changed here.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StarvationTable:
    """The stage lines and effects, tuned in this one place."""
    weakened_line: float = 85.0   # hunger at which the body weakens: recovery and attack are scaled
    starving_line: float = 95.0   # hunger at which health starts to go (the pre-existing line)
    recovery_scale: float = 0.5   # stamina and readiness regeneration while weakened
    attack_scale: float = 0.8     # attack multiplier while weakened (compounds with EXHAUSTION: 0.8 * 0.8 = 0.64)
    death_ticks: int = 6000       # ticks from the starving line to death for a full-health body (2.5 days)


STARVATION = StarvationTable()
WEAKENED_LINE = STARVATION.weakened_line
STARVING_LINE = STARVATION.starving_line


def is_weakened(hunger: float) -> bool:
    """True from the weakened line (hunger 85) upward."""
    return hunger >= STARVATION.weakened_line


def recovery_scale(hunger: float) -> float:
    """Multiplier on stamina and readiness regeneration: 1.0 unless weakened."""
    return STARVATION.recovery_scale if hunger >= STARVATION.weakened_line else 1.0


def attack_scale(hunger: float) -> float:
    """Multiplier on a weakened attacker's attack: 1.0 unless weakened."""
    return STARVATION.attack_scale if hunger >= STARVATION.weakened_line else 1.0


def hp_loss_period(max_hp: int) -> int:
    """Ticks between the 1 HP losses of a starving body of ``max_hp``: a full-health body then dies ``death_ticks`` after the line."""
    return max(1, round(STARVATION.death_ticks / max(1, max_hp)))


def hp_loss(hunger: float, max_hp: int, tick: int, entity_id: int, lifecycle_cadence: int = 1) -> int:
    """HP lost on this life-due tick: 1 once every ``hp_loss_period`` ticks at the starving line or above, else 0.

    The loss is staggered by entity id so a hungry population does not lose health on the same tick, and indexed by the life-due
    ordinal (``tick // lifecycle_cadence``) so a governor that raises the lifecycle cadence does not skip the multiples."""
    if hunger < STARVATION.starving_line:
        return 0
    return 1 if (tick // max(1, lifecycle_cadence) + entity_id) % hp_loss_period(max_hp) == 0 else 0
