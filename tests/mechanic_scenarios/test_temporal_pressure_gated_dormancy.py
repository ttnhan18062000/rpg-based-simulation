"""Runtime-evidence program, batch 2 (TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION,
remaining 17 `cognition` mechanisms). `temporal_pressure`'s own prior `code_trace` note (batch 3 of
the earlier unbound-claims program) cited `TemporalPressureService.calculate_urgencies()` called
from `src/domains/memory/phase.py:90` as its real production caller -- true, but one level shallow:
that call site lives inside `MemoryUpdatePhase.run()`, itself only reached via
`MemoryUpdatePhase.apply()`, which `src/engine/pipeline.py` gates behind `ENABLE_MEMORY_UPDATE`
(`FeatureMode.OFF` by default, `src/domains/optimization/feature_flags.py`). The prior note never
checked whether the containing phase was itself reachable by default -- the same one-level-deep gap
`perception`'s own note had (this program's own §5 item 4 backing rule exists specifically for this
shape). `causal_spatial_memory` (the same phase's own registered mechanism) already carries `state:
gated` for exactly this reason; `temporal_pressure` carries `state: skeleton` and never mentions the
gate at all.

Differential design: same staged entity (a real `DeadlineEntry` about to expire, the precondition
`calculate_urgencies()` itself reads), same real `Kernel.tick_once()` dispatch, only
`state.feature_flags["ENABLE_MEMORY_UPDATE"]` differs --
- "mechanism present" (flag ON): the deadline's own near-expiry urgency must be computed and
  written to `entity.cognition.subjective.time.urgency`.
- "mechanism absent" (flag OFF, the real default): `urgency` must stay at its compiled default
  (empty) -- the phase never runs, so nothing computes it.
Backing (per proposal doc §5 item 4): **(a) static** -- `ENABLE_MEMORY_UPDATE` defaults OFF in
`src/domains/optimization/feature_flags.py`, a fact independent of which scenario world is used;
the scenario corroborates it at runtime.

World: `data/worlds/mechanic_scenario_combat_judgement_withdrawal/` -- reused as-is.
"""
import os
from dataclasses import replace

from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository
from src.engine.kernel import Kernel
from src.config.profiles import PROD_SMALL
from src.platform.rng import DeterministicRNG
from src.core.cognition import DeadlineEntry
from src.domains.optimization.feature_flags import FeatureMode

WORLD_ID = "mechanic_scenario_combat_judgement_withdrawal"
GOBLIN_ID = 1
DEADLINE_KEY = "quest_deadline_scenario"
SEED = 42


def _compile_world():
    repo = WorldRepository(os.path.join("data", "worlds"))
    spec, context = repo.load_world_with_context(WORLD_ID)
    state, _report = WorldCompiler.compile(spec, SEED, context=context)
    return state


def _stage_near_expiry_deadline(state, *, memory_update_flag):
    goblin = state.entities[GOBLIN_ID]
    deadline = DeadlineEntry(target_id="scenario_target", expiry_tick=1)
    new_time = replace(goblin.cognition.subjective.time, deadlines={DEADLINE_KEY: deadline})
    new_subjective = replace(goblin.cognition.subjective, time=new_time)
    new_cognition = replace(goblin.cognition, subjective=new_subjective)
    goblin = replace(goblin, cognition=new_cognition)

    new_entities = dict(state.entities)
    new_entities[GOBLIN_ID] = goblin
    object.__setattr__(state, "entities", new_entities)
    object.__setattr__(state, "tick", 0)
    if memory_update_flag is not None:
        object.__setattr__(state, "feature_flags", {"ENABLE_MEMORY_UPDATE": memory_update_flag})
    return state


def _run_one_tick_and_get_urgency(state):
    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(SEED), flags={"no_frame_pacing": True})
    try:
        kernel.tick_once()
        final_state = kernel._state
    finally:
        kernel.shutdown()
    return final_state.entities[GOBLIN_ID].cognition.subjective.time.urgency


def test_urgency_is_computed_when_memory_update_is_enabled():
    """Mechanism present: ENABLE_MEMORY_UPDATE=ON. The near-expiry deadline (expiry_tick=1,
    current_tick=0, ticks_left=1) must produce a real, near-maximum urgency value through the real
    Kernel dispatch."""
    state = _compile_world()
    state = _stage_near_expiry_deadline(state, memory_update_flag=FeatureMode.ON)

    urgency = _run_one_tick_and_get_urgency(state)

    assert DEADLINE_KEY in urgency, (
        "temporal_pressure mechanic: expected the near-expiry deadline's urgency to be computed "
        f"when ENABLE_MEMORY_UPDATE=ON, but urgency map was {urgency!r} -- the phase did not run "
        "despite the flag being on."
    )
    assert urgency[DEADLINE_KEY] > 0.9, (
        f"temporal_pressure mechanic: expected near-maximum urgency for a 1-tick-from-expiry "
        f"deadline, got {urgency[DEADLINE_KEY]!r}."
    )


def test_urgency_stays_uncomputed_when_memory_update_is_off_the_real_default():
    """Mechanism absent: no feature_flags override at all -- the real, shipped default
    (ENABLE_MEMORY_UPDATE=OFF). The same near-expiry deadline is staged, but MemoryUpdatePhase
    never runs, so `urgency` must stay at its compiled default (empty) -- proving `temporal_pressure`
    is dormant by default in production, the same shape `causal_spatial_memory`'s own `gated` state
    already documents for the same phase."""
    state = _compile_world()
    state = _stage_near_expiry_deadline(state, memory_update_flag=None)

    urgency = _run_one_tick_and_get_urgency(state)

    assert urgency == {}, (
        "temporal_pressure mechanic: expected urgency to stay uncomputed with ENABLE_MEMORY_UPDATE "
        f"at its real default (OFF), but got {urgency!r} -- either the flag default changed, or "
        "something else computes urgency outside MemoryUpdatePhase."
    )


def test_calculate_urgencies_itself_works_when_called_directly():
    """Positive control: the service's own logic is not broken -- calling it directly against the
    same staged deadline produces the same near-maximum urgency value the gated-ON scenario above
    observes through the real pipeline."""
    from src.domains.time.service import TemporalPressureService

    state = _compile_world()
    state = _stage_near_expiry_deadline(state, memory_update_flag=None)
    goblin = state.entities[GOBLIN_ID]

    urgency = TemporalPressureService.calculate_urgencies(goblin, current_tick=0)

    assert urgency[DEADLINE_KEY] > 0.9
