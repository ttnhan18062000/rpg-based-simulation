"""Regression coverage for TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE.

Every existing natural-aging/death test in this repo (`test_heir_inventory_transfer_corpus.py`,
`test_lineage_dispatch_deterministic_kernel_tick.py`, `test_force_full_scan_phase_compliance.py`,
`test_aging_death_value_differential.py`, `test_succession_heir_selection_value_differential.py`)
stages `age_ticks` past `max_age_ticks` directly, so `resolve_lifecycle`'s own OLD_AGE check
(`src/systems/lifecycle_systems/lifecycle.py:193-195`) is already true on the very first tick it
runs. That staging pattern never exercises the real bug: on the tick where an entity's `age_ticks`
*first* reaches `max_age_ticks` through ordinary per-tick advancement,
`ApplyPath._compute_entity_changes`'s passive branch (`src/engine/apply.py:94-110`) independently
computes `lifecycle.active=False` a tick *before* `resolve_lifecycle` ever gets to see the
persisted age (resolution runs against the pre-tick snapshot, before this tick's age increment is
committed) -- and once `active` is `False`, `resolve_lifecycle`'s own loop guard
(`lifecycle.py:147-148`) skips the entity forever. No `death_reason` is ever recorded and no
lineage consequence ever dispatches. This module reproduces that exact ordinary-per-tick path
through a real `Kernel.tick_once()` loop.

Fix: `src/engine/apply.py`'s passive branch's `active=` formula changed from
`(new_hp > 0 and new_age < life.max_age_ticks)` to
`(new_hp > 0 and (life.active or new_age < life.max_age_ticks))` -- `resolve_lifecycle`'s OLD_AGE
branch is now the sole authority for old-age deactivation; the passive branch keeps only its
immediate HP-death gate. See `docs/simulation/lifecycle_systems_contract.md` for the declared
authority and `docs/guidelines/intentional_divergences.md` §2.59 for the resulting one-tick death
shift this file's `test_old_age_death_tick_is_pinned_one_tick_after_age_first_reaches_max` pins.
"""
from __future__ import annotations

from src.config.profiles import PROD_SMALL
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, ItemStack
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG

MAX_AGE_TICKS = 3
NUM_TICKS_TO_RUN = 6


def _build_aging_world():
    subject = (
        V2EntityBuilder(1)
        .kind("HERO")
        .location(0.0, 0.0)
        .lifecycle(active=True, age_ticks=0, max_age_ticks=MAX_AGE_TICKS, heir_entity_id=2)
        .inventory(items=[ItemStack(item_id="iron_sword", quantity=1), ItemStack(item_id="healing_potion", quantity=3)])
        .build()
    )
    heir = (
        V2EntityBuilder(2)
        .kind("HERO")
        .location(0.0, 0.0)
        .lifecycle(active=True)
        .inventory(items=[])
        .build()
    )
    return AuthoritativeState(tick=0, seed=42, entities={1: subject, 2: heir})


def _run_and_trace(num_ticks: int):
    state = _build_aging_world()
    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(42), flags={"no_frame_pacing": True})
    trace = []
    try:
        for _ in range(num_ticks):
            kernel.tick_once()
            life = kernel.state.entities[1].lifecycle
            trace.append((kernel.state.tick, life.active, life.death_reason, life.age_ticks))
        final_state = kernel.state
    finally:
        kernel.shutdown()
    return trace, final_state


def test_natural_aging_death_is_recorded_as_old_age_and_dispatches_succession():
    """AC1/AC2: an entity aged to max_age_ticks through ordinary per-tick Kernel.tick_once()
    progression -- not staged past max -- must end up dead with death_reason='OLD_AGE' and must
    dispatch its heir inventory transfer, identically to the already-working staged-age case."""
    _trace, final_state = _run_and_trace(NUM_TICKS_TO_RUN)

    final_subject = final_state.entities[1]
    assert final_subject.lifecycle.active is False, (
        "subject must be deactivated once age_ticks has passed max_age_ticks through ordinary "
        f"progression, got active={final_subject.lifecycle.active}"
    )
    assert final_subject.lifecycle.death_reason == "OLD_AGE", (
        "an ordinary-progression old-age death must record death_reason='OLD_AGE', got "
        f"{final_subject.lifecycle.death_reason!r} -- this is the dual-writer race's own symptom "
        "(passive branch silently deactivates one tick before resolve_lifecycle ever runs against "
        "the persisted age) if it reproduces as None"
    )

    final_heir = final_state.entities[2]
    heir_item_ids = {stack.item_id for stack in final_heir.inventory.items}
    assert "iron_sword" in heir_item_ids, "heir must inherit the deceased's iron_sword"
    assert "healing_potion" in heir_item_ids, "heir must inherit the deceased's healing_potion"


def test_no_tick_leaves_the_subject_inactive_without_a_death_reason():
    """AC3: across the full natural-aging trace, no tick may leave the subject
    active=False/death_reason=None as a terminal (i.e. never-recovered) state -- the exact silent
    -death signature this ticket exists to eliminate. Checked on every tick of the trace, not just
    the final one, since the bug's own symptom is a state that never recovers once reached."""
    trace, _final_state = _run_and_trace(NUM_TICKS_TO_RUN)

    silent_death_ticks = [
        world_tick for (world_tick, active, death_reason, _age) in trace
        if active is False and death_reason is None
    ]
    assert silent_death_ticks == [], (
        "found tick(s) where the subject was deactivated with no death_reason recorded: "
        f"{silent_death_ticks} -- full trace: {trace}"
    )


def test_old_age_death_tick_is_pinned_one_tick_after_age_first_reaches_max():
    """AC4: pins the exact tick the death is recorded on. age_ticks first reaches MAX_AGE_TICKS
    (3) at the end of the 3rd Kernel.tick_once() call (Writer 1's own passive-branch age
    increment, which now -- post-fix -- no longer independently deactivates the entity for age).
    resolve_lifecycle only observes that persisted age on the *following* tick (resolution runs
    against the pre-tick snapshot), so the death is recorded on the 4th call, one tick after
    age_ticks first reached max_age_ticks -- not on the 3rd call itself, and not silently on
    neither. This is the ticket's own declared, documented one-tick shift (intentional_divergences
    .md §2.59), not an accidental side effect."""
    trace, _final_state = _run_and_trace(NUM_TICKS_TO_RUN)

    age_reaches_max_tick = next(
        world_tick for (world_tick, _active, _death_reason, age_ticks) in trace
        if age_ticks >= MAX_AGE_TICKS
    )
    death_recorded_tick = next(
        world_tick for (world_tick, _active, death_reason, _age_ticks) in trace
        if death_reason is not None
    )

    assert age_reaches_max_tick == 3, (
        f"expected age_ticks to first reach {MAX_AGE_TICKS} on world tick 3, trace={trace}"
    )
    assert death_recorded_tick == age_reaches_max_tick + 1, (
        "expected the OLD_AGE death to be recorded exactly one tick after age_ticks first reached "
        f"max_age_ticks (world tick {age_reaches_max_tick + 1}), got {death_recorded_tick}. "
        f"full trace={trace}"
    )

    # The subject must still be active on the tick age_ticks reaches max itself (the tick the
    # pre-fix dual-writer race silently deactivated it on with no death_reason).
    active_when_age_reaches_max = next(
        active for (world_tick, active, _death_reason, _age_ticks) in trace
        if world_tick == age_reaches_max_tick
    )
    assert active_when_age_reaches_max is True, (
        "the subject must remain active on the tick age_ticks first reaches max_age_ticks -- "
        "deactivation-for-age is now resolve_lifecycle's sole responsibility, one tick later"
    )


def test_starvation_sleep_debt_driven_hp_loss_is_recorded_post_fix():
    """Updated by TCK-20261001-PASSIVE-BIOLOGICAL-DEATH-CAUSE-RECORDED-AT-WRITER (this test was
    `..._is_still_silent_post_fix`, pinning the gap TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-
    GAP named). An entity driven to hp=0 by the passive path writes combat.hp=0/alive=False and a
    typed passive cause on tick N; `lifecycle.active` is left alone (resolve_lifecycle is the sole
    authority, as PROG-030 declares for age), and resolve_lifecycle records the death on the
    following tick with its succession dispatch."""
    starving = (
        V2EntityBuilder(3)
        .kind("HERO")
        .location(0.0, 0.0)
        .biological(hunger=95.0, sleep_debt=98.0)
        .combat(hp=1)
        .lifecycle(active=True, age_ticks=0, max_age_ticks=100_000)
        .build()
    )
    state = AuthoritativeState(tick=0, seed=42, entities={3: starving})
    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(42), flags={"no_frame_pacing": True})
    try:
        kernel.tick_once()
        zeroing = kernel.state.entities[3]
        kernel.tick_once()
        final = kernel.state.entities[3]
    finally:
        kernel.shutdown()

    assert zeroing.combat.hp == 0 and zeroing.combat.alive is False
    assert zeroing.lifecycle.active is True and zeroing.lifecycle.death_reason is None
    assert zeroing.lifecycle.passive_death_cause is not None
    assert final.lifecycle.active is False
    assert final.lifecycle.death_reason == "STARVATION"
