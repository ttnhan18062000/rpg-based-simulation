"""Runtime-evidence program, value-differential axis (TCK-20260921-MECHANISM-PROGRESSION-VALUE-
DIFFERENTIAL-INSTRUMENT), wave 2: applies the instrument to `aging_death`
(`LifecycleSystem.resolve_lifecycle`, `src/systems/lifecycle_systems/lifecycle.py:189-195`) --
the real old-age check `entity.lifecycle.age_ticks >= entity.lifecycle.max_age_ticks`.

This is the first mechanism in this program that risks the new §5.1 null-result rule (added after
peer review of batch 1): aging is naturally tick-based, and a scenario that ran only a handful of
ticks with age_ticks staged far below any threshold would show "no difference" for a reason that
has nothing to do with whether `max_age_ticks` matters -- the outcome would simply not have been
computed yet. Resolved by staging `age_ticks` directly (not relying on the real per-tick
increment, which is itself cadence-gated -- `apply.py`'s own `is_life_due = should_run(tick, None,
cadence.lifecycle)` -- and would risk the same cadence trap Program A hit on `goal_hierarchy`) at
a fixed value in both arms, and varying only `max_age_ticks` -- the real field the mechanism's own
check reads. `resolve_lifecycle()` reads `state.entities[e_id].lifecycle.age_ticks`/
`max_age_ticks` directly (not from any update proposed earlier that tick) and runs unconditionally
every tick (registry note: "called from pipeline.py:414 every tick") -- so the outcome IS fully
computed within a single real Kernel tick. This satisfies §5.1(a) directly: the difference, if it
exists, is observable in one tick, no horizon-weakening needed.

World: reused `data/worlds/mechanic_scenario_combat_judgement_withdrawal/` (only the goblin is
touched; no combat is staged, aging_death is orthogonal to the pairing this world was built for).

Two real arms, `age_ticks` fixed at 1000 in both:
- Arm A (`max_age_ticks=999`, below the fixed age): positive control -- the entity must die of old
  age this tick (`death_reason="OLD_AGE"`, `active=False`).
- Arm B (`max_age_ticks=5000`, comfortably above the fixed age): negative control -- the entity
  must remain alive and active.
"""
import os
from dataclasses import replace

from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository
from src.engine.kernel import Kernel
from src.config.profiles import PROD_SMALL
from src.platform.rng import DeterministicRNG

WORLD_ID = "mechanic_scenario_combat_judgement_withdrawal"
GOBLIN_ID = 1
SEED = 42
FIXED_AGE_TICKS = 1000


def _compile_world():
    repo = WorldRepository(os.path.join("data", "worlds"))
    spec, context = repo.load_world_with_context(WORLD_ID)
    state, _report = WorldCompiler.compile(spec, SEED, context=context)
    return state


def _run_arm(*, max_age_ticks: int):
    state = _compile_world()
    goblin = state.entities[GOBLIN_ID]
    goblin = replace(
        goblin,
        lifecycle=replace(goblin.lifecycle, age_ticks=FIXED_AGE_TICKS, max_age_ticks=max_age_ticks),
    )
    new_entities = dict(state.entities)
    new_entities[GOBLIN_ID] = goblin
    object.__setattr__(state, "entities", new_entities)

    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(SEED), flags={"no_frame_pacing": True})
    try:
        kernel.tick_once()
        final_state = kernel._state
    finally:
        kernel.shutdown()
    return final_state.entities[GOBLIN_ID]


def test_max_age_ticks_below_current_age_kills_the_entity_of_old_age():
    """Positive control: with age_ticks=1000 fixed, a max_age_ticks of 999 (below the fixed age)
    must produce a real old-age death this same tick -- the mechanism's own input has real
    purchase on the outcome, and the outcome is observed within a single-tick window (§5.1(a))."""
    goblin_after = _run_arm(max_age_ticks=999)

    assert goblin_after.lifecycle.active is False, (
        "aging_death mechanic: expected the entity to be deactivated by old age this tick "
        f"(age_ticks=1000 >= max_age_ticks=999), but lifecycle.active={goblin_after.lifecycle.active}."
    )
    assert goblin_after.lifecycle.death_reason == "OLD_AGE", (
        "aging_death mechanic: expected death_reason='OLD_AGE', got "
        f"{goblin_after.lifecycle.death_reason!r}."
    )


def test_max_age_ticks_above_current_age_leaves_the_entity_alive():
    """Negative control: with the same age_ticks=1000, a max_age_ticks of 5000 (comfortably above)
    must leave the entity alive and active -- proving this instrument does not report a difference
    regardless of the input's value, only when the real threshold condition is actually crossed."""
    goblin_after = _run_arm(max_age_ticks=5000)

    assert goblin_after.lifecycle.active is True, (
        "aging_death mechanic negative control: expected the entity to remain active "
        f"(age_ticks=1000 < max_age_ticks=5000), but lifecycle.active={goblin_after.lifecycle.active}."
    )
    assert goblin_after.lifecycle.death_reason is None, (
        "aging_death mechanic negative control: expected no death_reason, got "
        f"{goblin_after.lifecycle.death_reason!r}."
    )
