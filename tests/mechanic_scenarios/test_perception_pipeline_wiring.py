"""Runtime-evidence program, batch 1 (TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION).
`perception`'s own `verified` block (registries/mechanisms.yaml, code_trace, `verdict: observed`)
claims `PerceptionFilterService.filter()` is "called from src/domains/perception/phase.py:43, a
real, non-test integration into the per-tick pipeline." Direct investigation for this ticket found
that claim is only half true: line 43 IS a real call site -- but it lives *inside*
`PerceptionUpdatePhase.run()`, and nothing in `src/` outside `phase.py` itself ever constructs a
`PerceptionUpdatePhase` or calls `.run()` (confirmed by a full-tree grep, not just a `pipeline.py`
read). `mechanism_state_caller_check.py`'s own one-level caller check cannot see this: it confirms
`PerceptionFilterService` has a real caller (`phase.py`) without checking whether that caller's own
caller is itself reachable from the real per-tick pipeline (`src/engine/pipeline.py::refine()`).

This scenario tests the claim the only way that actually settles it: run the real, unmodified
per-tick pipeline against a world with a genuinely perceivable candidate, and see whether perception
ever materializes.

World: `data/worlds/mechanic_scenario_combat_judgement_withdrawal/` -- reused as-is. goblin_scout
and orc_warchief compile within melee range of each other (confirmed by the pre-existing
`test_combat_judgement_withdrawal.py`/`test_action_pacing_readiness_gate.py` scenarios, which stage
attacks between them at this same range) -- about as strong a "perceivable candidate" as a
production-like scenario can offer without hand-authoring a new world: if perception were wired at
all, an adjacent, hostile, alive entity is exactly the kind of signal it would need to surface.

Two independent signals are checked, not just one, per the proposal's own §5.2 caution that a
passing-looking absence can be a scenario-design gap rather than a real finding:
1. `entity.cognition.subjective.perception.perceived_entities` -- the claimed observable effect.
2. A call-counter wrap on `PerceptionFilterService.filter` itself -- whether the mechanism's own
   entry point is invoked at all, independent of what it would have produced.
Both must show "never happened" for this to be a real contradiction rather than a mechanism that
runs and legitimately perceives nothing.

Per this program's explicit governing constraint: if this instrument contradicts the claim, the
contradiction is recorded in the registry -- `PerceptionUpdatePhase` is NOT wired into
`pipeline.py` here to make the existing `observed` verdict true.
"""
import os

from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository
from src.engine.kernel import Kernel
from src.config.profiles import PROD_SMALL
from src.platform.rng import DeterministicRNG
from src.domains.perception.filter import PerceptionFilterService

WORLD_ID = "mechanic_scenario_combat_judgement_withdrawal"
GOBLIN_ID = 1
ORC_ID = 2
SEED = 42
TICKS_TO_RUN = 5


def _compile_world():
    repo = WorldRepository(os.path.join("data", "worlds"))
    spec, context = repo.load_world_with_context(WORLD_ID)
    state, _report = WorldCompiler.compile(spec, SEED, context=context)
    return state


def _run_n_ticks_and_count_filter_calls(state, n: int):
    orig_filter = PerceptionFilterService.filter
    calls = []

    def wrapped(*args, **kwargs):
        calls.append(1)
        return orig_filter(*args, **kwargs)

    PerceptionFilterService.filter = staticmethod(wrapped)
    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(SEED), flags={"no_frame_pacing": True})
    try:
        for _ in range(n):
            kernel.tick_once()
        final_state = kernel._state
    finally:
        kernel.shutdown()
        PerceptionFilterService.filter = staticmethod(orig_filter)

    return final_state, len(calls)


def test_perception_never_materializes_for_an_adjacent_perceivable_entity_through_the_real_pipeline():
    """A real, adjacent, alive, hostile entity is present -- exactly the signal `perception`'s own
    registry note claims it surfaces. Across 5 real ticks, `perceived_entities` must stay empty if
    the mechanism is genuinely unwired, confirming the state claim is contradicted rather than
    proving the mechanism produces nothing under these specific conditions."""
    state = _compile_world()

    final_state, filter_calls = _run_n_ticks_and_count_filter_calls(state, TICKS_TO_RUN)

    goblin_perception = final_state.entities[GOBLIN_ID].cognition.subjective.perception
    orc_perception = final_state.entities[ORC_ID].cognition.subjective.perception

    assert filter_calls == 0, (
        "perception mechanic: expected PerceptionFilterService.filter to never be called through "
        f"the real per-tick pipeline across {TICKS_TO_RUN} ticks (nothing in src/ outside "
        "phase.py instantiates PerceptionUpdatePhase), but it was called "
        f"{filter_calls} time(s) -- if this happens, the registry's `orphan`-shaped finding for "
        "this mechanism is WRONG and must not be recorded as a contradiction."
    )
    assert goblin_perception.perceived_entities == {}, (
        "perception mechanic: expected the goblin's perceived_entities to stay empty (no "
        f"perception phase ever runs), but found {goblin_perception.perceived_entities!r} after "
        f"{TICKS_TO_RUN} ticks with an adjacent, alive orc present."
    )
    assert orc_perception.perceived_entities == {}, (
        "perception mechanic: expected the orc's perceived_entities to stay empty, but found "
        f"{orc_perception.perceived_entities!r}."
    )


def test_perception_filter_service_itself_still_works_when_called_directly():
    """Positive control: PerceptionFilterService.filter() is not itself broken -- calling it
    directly (bypassing the pipeline entirely, the way PerceptionUpdatePhase.run() would if
    anything ever constructed one) against a real candidate signal DOES produce a perceived entry.
    This is what rules out "the salience/budget logic silently rejects everything" as the
    explanation for the zero-call result above -- the mechanism's own code works; it is simply
    never reached from the real per-tick pipeline."""
    from src.domains.perception.salience import WorldSignal
    from src.domains.perception.filter import PerceptionBudget

    state = _compile_world()
    goblin = state.entities[GOBLIN_ID]
    orc = state.entities[ORC_ID]

    signal = WorldSignal(
        signal_id=str(ORC_ID),
        kind="entity",
        position=orc.navigation.position,
        base_relevance=1.0,
        danger_level=0.8,
    )

    update = PerceptionFilterService.filter(
        entity=goblin,
        candidate_signals=[signal],
        budget=PerceptionBudget(),
        tick=0,
    )

    assert len(update.perceived_entities) > 0, (
        "perception mechanic: PerceptionFilterService.filter() called DIRECTLY against a real "
        "candidate signal produced zero perceived entities -- this would mean the mechanism's own "
        "code is broken, not merely unwired, and the finding above needs re-investigating before "
        "recording a verdict."
    )
