"""Runtime-evidence program, batch 2 (TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION,
Bucket B). `causal_spatial_memory` (`src/domains/memory/phase.py::MemoryUpdatePhase`) already
carries `state: gated` correctly (unlike `temporal_pressure`'s own prior mis-classification, the
same phase's sibling mechanism) -- this scenario upgrades its `code_trace` verdict to a real
runtime-confirmed `scenario` one, reusing the flag-toggle scaffolding `temporal_pressure`'s own
scenario already built and validated for this same phase/gate.

Targets step 3 of `MemoryUpdatePhase.run()` ("Regular Spatial Visited region updating based on
current position") rather than the trigger-event-driven causal-attribution half (step 2, which needs
a real `combat_loss`/`near_death` world event threaded through `state.recent_world_events` --
more staging than this scenario needs for a clean differential): every processed entity with a real
`navigation.region_id` gets `SpatialMemoryUpdateService.update_region_visit()` called
unconditionally, no trigger needed -- the simplest, most reliable real observable effect this phase
produces.

Differential design: same compiled entity (already has `navigation.region_id="judgement_arena"` and
an empty `memory.spatial.visited_regions` by default), same real `Kernel.tick_once()` dispatch, only
`state.feature_flags["ENABLE_MEMORY_UPDATE"]` differs --
- "mechanism present" (flag ON): the region gets recorded as visited (`visit_count=1,
  familiarity=0.2`).
- "mechanism absent" (flag OFF, the real default): `visited_regions` stays empty -- the phase never
  runs.
Backing (per proposal doc §5 item 4, same shape as `temporal_pressure`'s own already-audited entry):
**(a) static** -- `ENABLE_MEMORY_UPDATE` defaults OFF in
`src/domains/optimization/feature_flags.py`, independent of which world is used; this is a
reachability claim (is the phase reachable when the flag is off), not an internal-decision-logic
claim, so §5 item 5's reach-proof requirement does not apply to the negative arm here -- same
distinction already recorded on `temporal_pressure`'s own entry.
"""
import os
from dataclasses import replace

from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository
from src.engine.kernel import Kernel
from src.config.profiles import PROD_SMALL
from src.platform.rng import DeterministicRNG
from src.domains.optimization.feature_flags import FeatureMode

WORLD_ID = "mechanic_scenario_combat_judgement_withdrawal"
GOBLIN_ID = 1
SEED = 42


def _compile_world():
    repo = WorldRepository(os.path.join("data", "worlds"))
    spec, context = repo.load_world_with_context(WORLD_ID)
    state, _report = WorldCompiler.compile(spec, SEED, context=context)
    return state


def _stage_flag(state, *, memory_update_flag):
    object.__setattr__(state, "tick", 0)
    if memory_update_flag is not None:
        object.__setattr__(state, "feature_flags", {"ENABLE_MEMORY_UPDATE": memory_update_flag})
    return state


def _run_one_tick_and_get_visited_regions(state):
    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(SEED), flags={"no_frame_pacing": True})
    try:
        kernel.tick_once()
        final_state = kernel._state
    finally:
        kernel.shutdown()
    return final_state.entities[GOBLIN_ID].cognition.memory.spatial.visited_regions


def test_region_visit_is_recorded_when_memory_update_is_enabled():
    """Mechanism present: ENABLE_MEMORY_UPDATE=ON. The goblin's own real, compiled
    navigation.region_id ("judgement_arena") must be recorded as a real visit through a real
    Kernel dispatch."""
    state = _compile_world()
    state = _stage_flag(state, memory_update_flag=FeatureMode.ON)

    visited = _run_one_tick_and_get_visited_regions(state)

    assert "judgement_arena" in visited, (
        "causal_spatial_memory mechanic: expected the goblin's own compiled region to be recorded "
        f"as visited when ENABLE_MEMORY_UPDATE=ON, but visited_regions was {visited!r}."
    )
    assert visited["judgement_arena"].visit_count == 1
    assert visited["judgement_arena"].familiarity == 0.2


def test_region_visit_stays_unrecorded_when_memory_update_is_off_the_real_default():
    """Mechanism absent: no feature_flags override -- the real, shipped default
    (ENABLE_MEMORY_UPDATE=OFF). MemoryUpdatePhase never runs, so visited_regions must stay at its
    compiled default (empty) -- the same reachability claim `temporal_pressure`'s own scenario
    already established and audited for this identical phase/gate."""
    state = _compile_world()
    state = _stage_flag(state, memory_update_flag=None)

    visited = _run_one_tick_and_get_visited_regions(state)

    assert visited == {}, (
        "causal_spatial_memory mechanic: expected visited_regions to stay empty with "
        f"ENABLE_MEMORY_UPDATE at its real default (OFF), but got {visited!r}."
    )


def test_update_region_visit_itself_works_when_called_directly():
    """Positive control: the service's own logic is not broken -- calling it directly against the
    same compiled region_id produces the same real visit record the gated-ON scenario above
    observes through the real pipeline."""
    from src.domains.memory.spatial_update import SpatialMemoryUpdateService
    from src.core.cognition import SpatialMemory

    updated = SpatialMemoryUpdateService.update_region_visit(SpatialMemory(), "judgement_arena")

    assert updated.visited_regions["judgement_arena"].visit_count == 1
    assert updated.visited_regions["judgement_arena"].familiarity == 0.2
