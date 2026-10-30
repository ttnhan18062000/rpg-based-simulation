"""Staged sleep debt (SURV-02, owner decision 41): weakened first, then collapse where it stands; health is never lost to lack of sleep.

Past a high sleep debt a subject weakens (it recovers more slowly and fights worse); at the collapse line it falls asleep on the tile it
occupies, takes no action, and wakes once enough of the debt is slept off. The old rule (1 HP per tick at debt 98 or more) killed a standing
subject about 100 ticks after the line, still walking (LB-S19).

Every stage is derived from ``BiologicalComponent.sleep_debt`` alone: no new state field. The collapse itself is a held ``SLEEP`` task
(``collapse_update``) that the actions phase keeps until ``is_rested_enough``. ``SLEEP_DEBT`` is the one place these values are tuned.

Values (owner decision 33: they follow the fiction, never fitted to an outcome; ruled by the designer, D41 / LB-S19, applying SURV-07):
  - ``weakened_line`` 80: the pre-existing EXHAUSTION line in ``combat.py``; recovery at ``recovery_scale`` 0.5 (decision 36's scale), confirmed.
  - ``collapse_line`` 98: the pre-existing drain line in ``apply.py`` that decision 41 turns into a collapse.
  - ``wake_line``: no new number, SURV-07's escalation onset (``need_pull.ESCALATION_ONSET`` x ``SLEEP_LINE``, about 59): the debt below which a
    sleeper wakes and then DECIDES (decision 32): keep sleeping if safe and tired, or get up.
  - ``rest_factor`` 2: while asleep the debt falls at twice the kind's own accrual rate (people 0.1 a tick against 0.05; animals by their own
    profile, decision 42), for a collapse and for a voluntary sleep alike. A collapse from 98 then lasts about 390 ticks (about 4 hours).
    A bed still improves quality; it has no separate rate.
  - ``bed_reach`` 30 tiles: how far a tired subject walks for a bed (about half an hour at 36 s a tick).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.core.movement_modes import MovementMode
from src.core.strategic import GoalKind, ProjectStatus
from src.core.updates import EntityUpdate, NavigationUpdate, TaskUpdate
from src.engine.need_pull import ESCALATION_ONSET, SLEEP_LINE


@dataclass(frozen=True, slots=True)
class SleepDebtTable:
    """The stage lines and effects, tuned in this one place."""
    weakened_line: float = 80.0   # debt above which the body weakens: recovery and attack are scaled
    collapse_line: float = 98.0   # debt at which the subject falls asleep where it stands
    wake_line: float = ESCALATION_ONSET * SLEEP_LINE  # debt below which a sleeper wakes (about 59), then decides
    rest_factor: float = 2.0      # while asleep the debt falls at this multiple of the kind's own accrual rate
    recovery_scale: float = 0.5   # stamina and readiness regeneration while weakened
    bed_reach: float = 30.0       # tiles a tired subject will walk for a bed (ruled: about half an hour's walk at 36 s a tick)


SLEEP_DEBT = SleepDebtTable()
COLLAPSE_LINE = SLEEP_DEBT.collapse_line
COLLAPSE_FLAG = "collapse"  # marks a SLEEP task that began as a collapse (a key other than `reason`, which the outcome annotation drops)
# The sleep debt below which a CHOSEN rest or sleep is met and ends, and a fatigue project completes (divergence 2.153, STRAT-293). Moved here from
# ``tactical_rest`` (the one tuning place for sleep values); ``tactical_rest`` re-exports it. No new number: the value is unchanged.
REST_MIN_SLEEP_DEBT = 20.0
SLEEP_ACTIONS = frozenset({"SLEEP", "REST"})  # the actions that put a subject to sleep; each is held until the debt is below the wake line


def is_weakened(sleep_debt: float) -> bool:
    """True above the weakened line (debt 80)."""
    return sleep_debt > SLEEP_DEBT.weakened_line


def must_collapse(sleep_debt: float) -> bool:
    """True from the collapse line (debt 98) upward."""
    return sleep_debt >= SLEEP_DEBT.collapse_line


def is_rested_enough(sleep_debt: float) -> bool:
    """True once the debt is below the wake line (debt 60)."""
    return sleep_debt < SLEEP_DEBT.wake_line


def chosen_rest_is_met(sleep_debt: float) -> bool:
    """True once a CHOSEN rest or sleep (not a collapse) has met the sleep need: debt below ``REST_MIN_SLEEP_DEBT`` (2.153 / STRAT-293). Strictly below, because the fatigue project completes
    (``intelligence.py`` ``< 20.0``) and the goal exits (``scorers.py`` ``< 20.0``) only strictly below the floor: ending at exactly 20.0 would leave both open.

    The wake line (``is_rested_enough``) stays the scheduler's wake trigger, the goal's "tired" read and a collapse's end; a chosen rest ran only
    to it before, so a REST begun at the line ended after one tick and the fatigue project (which completes at the floor) never did."""
    return sleep_debt < REST_MIN_SLEEP_DEBT


def rest_ended_at_the_floor(entity: Any) -> bool:
    """2.153 / STRAT-293: True for a subject whose chosen rest has just ended at the sleep floor, so its brain closes the need before debt accrues again.

    An idle subject (no held task) whose current project is a live, ACTIVE fatigue project and whose sleep debt is strictly below ``REST_MIN_SLEEP_DEBT``:
    exactly the state a chosen SLEEP/REST leaves when it ends (``chosen_rest_is_met``). The scheduler wakes its brain and the strategic pass runs for it on that
    tick (off its cadence), so ``intelligence.py`` sees the debt under the floor and completes the project; without it the next cadence tick, up to ten ticks
    later, sees the debt back at the floor and rests in place again. Woken: nothing else. No new constant. A pure read."""
    if entity.task.payload or entity.biological.sleep_debt >= REST_MIN_SLEEP_DEBT:
        return False
    strat = entity.strategic
    project = strat.projects.get(strat.current_project_id) if strat.current_project_id else None
    return project is not None and project.kind == GoalKind.FATIGUE and project.status == ProjectStatus.ACTIVE


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


def is_asleep(entity: Any) -> bool:
    """True when the subject's task is a sleep (a collapse, a rest in place or a rest at a bed): the debt then falls instead of accruing."""
    return entity.task.work_kind == "ENTITY_ACT" and entity.task.payload.get("action") in SLEEP_ACTIONS


def debt_change_per_tick(accrual_rate: float, asleep: bool) -> float:
    """The change in sleep debt per tick: +the kind's accrual rate awake, -rest_factor x that rate asleep."""
    return -SLEEP_DEBT.rest_factor * accrual_rate if asleep else accrual_rate
