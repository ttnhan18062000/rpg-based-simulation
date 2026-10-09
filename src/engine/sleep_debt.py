"""Staged sleep debt (SURV-02, owner decision 41): weakened first, then collapse where it stands; health is never lost to lack of sleep.

Past a high sleep debt a subject weakens (it recovers more slowly and fights worse); at the collapse line it falls asleep on the tile it
occupies, takes no action, and wakes once enough of the debt is slept off. The old rule (1 HP per tick at debt 98 or more) killed a standing
subject about 100 ticks after the line, still walking (LB-S19).

Every stage is derived from ``BiologicalComponent.sleep_debt`` alone: no new state field. The collapse itself is a held ``SLEEP`` task
(``collapse_update``) that the actions phase keeps until ``is_rested_enough``. ``SLEEP_DEBT`` is the one place these values are tuned.

Where each value comes from (owner decision 33: values follow the fiction, never fitted to an outcome):
  - ``weakened_line`` 80: the pre-existing EXHAUSTION line in ``combat.py`` (attack x0.8 above 80), now read from here.
  - ``collapse_line`` 98: the pre-existing drain line in ``apply.py`` that decision 41 turns into a collapse.
  - ``wake_line`` 60 and ``recovery_scale`` 0.5: rpg-planner's suggested values (LB-S19), recorded, not yet ruled by the designer;
    the recovery scale is the one decision 36 uses for a body weakened by hunger.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from src.core.movement_modes import MovementMode
from src.core.updates import EntityUpdate, NavigationUpdate, TaskUpdate


@dataclass(frozen=True, slots=True)
class SleepDebtTable:
    """The stage lines and effects, tuned in this one place."""
    weakened_line: float = 80.0   # debt above which the body weakens: recovery and attack are scaled
    collapse_line: float = 98.0   # debt at which the subject falls asleep where it stands
    wake_line: float = 60.0       # debt below which a collapsed subject wakes
    recovery_scale: float = 0.5   # stamina and readiness regeneration while weakened


SLEEP_DEBT = SleepDebtTable()
COLLAPSE_LINE = SLEEP_DEBT.collapse_line
COLLAPSE_FLAG = "collapse"  # carried by the held SLEEP task's payload (a key other than `reason`, which the outcome annotation drops)


def is_weakened(sleep_debt: float) -> bool:
    """True above the weakened line (debt 80)."""
    return sleep_debt > SLEEP_DEBT.weakened_line


def must_collapse(sleep_debt: float) -> bool:
    """True from the collapse line (debt 98) upward."""
    return sleep_debt >= SLEEP_DEBT.collapse_line


def is_rested_enough(sleep_debt: float) -> bool:
    """True once the debt is below the wake line (debt 60)."""
    return sleep_debt < SLEEP_DEBT.wake_line


def recovery_scale(sleep_debt: float) -> float:
    """Multiplier on stamina and readiness regeneration: 1.0 unless weakened."""
    return SLEEP_DEBT.recovery_scale if is_weakened(sleep_debt) else 1.0


def collapse_update(entity: Any) -> EntityUpdate:
    """The decision of a subject whose debt has reached the collapse line: stop where it stands and sleep (a held SLEEP task, no navigation target)."""
    return EntityUpdate(
        entity_id=entity.id,
        navigation=NavigationUpdate(target_clear=True, movement_mode_set=MovementMode.HOLD),
        task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "SLEEP", COLLAPSE_FLAG: True}),
    )


def sleep_done(entity: Any, actor_update: Optional[EntityUpdate]) -> bool:
    """True when a held collapse sleep ends: the debt after this execution is below the wake line (or the action did nothing)."""
    delta = actor_update.biological.sleep_debt_delta if actor_update is not None and actor_update.biological is not None else 0.0
    return is_rested_enough(entity.biological.sleep_debt + delta)
