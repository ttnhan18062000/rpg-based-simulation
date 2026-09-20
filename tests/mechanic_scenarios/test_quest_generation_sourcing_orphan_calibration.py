"""Runtime-evidence program, batch 1 (TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION).
Calibration case, per the peer's explicit instruction: `quest_generation_sourcing` is already
`state: orphan`, `verdict: contradicted` (code_trace) -- `QuestGenerationSystem`
(`src/systems/world_systems/quests.py`) has zero real callers for any of its 3 methods anywhere in
`src/` (re-confirmed by a fresh grep for this ticket, no output). If a runtime scenario reports this
mechanism as running, the harness itself is broken -- this is what tells us the instrument
discriminates at all, not just that it can produce a favorable answer.

Stages the real trigger condition `generate_from_scar()` itself checks (`region.trauma_score >
0.3`) on a real compiled world's own region, runs several real ticks through the unmodified
pipeline, and confirms zero real calls to any of the 3 `QuestGenerationSystem` methods -- with a
positive control (direct call, bypassing the pipeline) proving the code itself is not broken, only
unreached, so a zero-call result is attributable to "never invoked," not to the trauma precondition
being staged wrong.
"""
import os
from dataclasses import replace

from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository
from src.engine.kernel import Kernel
from src.config.profiles import PROD_SMALL
from src.platform.rng import DeterministicRNG
from src.systems.world_systems.quests import QuestGenerationSystem

WORLD_ID = "mechanic_scenario_combat_judgement_withdrawal"
SEED = 42
TICKS_TO_RUN = 5


def _compile_world():
    repo = WorldRepository(os.path.join("data", "worlds"))
    spec, context = repo.load_world_with_context(WORLD_ID)
    state, _report = WorldCompiler.compile(spec, SEED, context=context)
    return state


def _stage_high_trauma_region(state):
    """Clears the real trigger condition generate_from_scar() itself checks (trauma_score > 0.3) on
    whichever real region this compiled world has -- not a synthetic region, the actual one the
    catalog placed."""
    region_id = next(iter(state.regions))
    region = state.regions[region_id]
    staged_region = replace(region, trauma_score=0.9, hazard_level=0.7)

    new_regions = dict(state.regions)
    new_regions[region_id] = staged_region
    object.__setattr__(state, "regions", new_regions)
    return state, staged_region


def _run_n_ticks_with_call_counters(state, n: int):
    orig_scar = QuestGenerationSystem.generate_from_scar
    orig_blockers = QuestGenerationSystem.generate_from_blockers
    orig_to_project = QuestGenerationSystem.quest_to_project
    calls = {"scar": 0, "blockers": 0, "to_project": 0}

    def wrap_scar(*a, **kw):
        calls["scar"] += 1
        return orig_scar(*a, **kw)

    def wrap_blockers(*a, **kw):
        calls["blockers"] += 1
        return orig_blockers(*a, **kw)

    def wrap_to_project(*a, **kw):
        calls["to_project"] += 1
        return orig_to_project(*a, **kw)

    QuestGenerationSystem.generate_from_scar = staticmethod(wrap_scar)
    QuestGenerationSystem.generate_from_blockers = staticmethod(wrap_blockers)
    QuestGenerationSystem.quest_to_project = staticmethod(wrap_to_project)

    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(SEED), flags={"no_frame_pacing": True})
    try:
        for _ in range(n):
            kernel.tick_once()
    finally:
        kernel.shutdown()
        QuestGenerationSystem.generate_from_scar = staticmethod(orig_scar)
        QuestGenerationSystem.generate_from_blockers = staticmethod(orig_blockers)
        QuestGenerationSystem.quest_to_project = staticmethod(orig_to_project)

    return calls


def test_quest_generation_system_is_never_called_through_the_real_pipeline_despite_the_trigger_condition_being_met():
    """Calibration: a real region clears generate_from_scar()'s own trauma_score > 0.3 threshold
    for 5 real ticks through the unmodified per-tick pipeline. If the harness reports any call
    here, it is broken -- QuestGenerationSystem has zero real callers by direct grep, independently
    of this scenario."""
    state = _compile_world()
    state, staged_region = _stage_high_trauma_region(state)
    assert staged_region.trauma_score > 0.3, "scenario staging defect: trigger condition not met"

    calls = _run_n_ticks_with_call_counters(state, TICKS_TO_RUN)

    assert calls == {"scar": 0, "blockers": 0, "to_project": 0}, (
        "quest_generation_sourcing calibration: expected zero real calls to any "
        "QuestGenerationSystem method across "
        f"{TICKS_TO_RUN} ticks with trauma_score=0.9 (clears the 0.3 threshold), but got "
        f"{calls!r} -- either the harness has a false-positive bug, or this mechanism is no longer "
        "orphaned and the registry's own `orphan`/`contradicted` state needs re-investigating "
        "before this test's own assumption can stand."
    )


def test_generate_from_scar_itself_produces_a_real_quest_when_called_directly():
    """Positive control: the code itself is not broken, only unreached. Calling
    generate_from_scar() DIRECTLY (bypassing the pipeline, since nothing else ever reaches it)
    against the same staged region returns a real QuestTemplate -- proving the zero-call result
    above means "never invoked," not "the trauma precondition doesn't actually trigger anything.\""""
    state = _compile_world()
    state, staged_region = _stage_high_trauma_region(state)

    quest = QuestGenerationSystem.generate_from_scar(staged_region, current_tick=0)

    assert quest is not None, (
        "quest_generation_sourcing calibration: generate_from_scar() called DIRECTLY against a "
        "region with trauma_score=0.9 returned None -- the code itself would be broken, not "
        "merely unreached, and the calibration test above needs re-investigating."
    )
    assert quest.kind == "scar_investigation"
