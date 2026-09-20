"""Runtime-evidence program, batch 2 (TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION,
Bucket B). One shared question, not two independent ones, per the same discipline
`goal_hierarchy`/`strategic_intelligence_core` already established for the `strategic_intelligence`
phase: `self_model` and `knowledge_model` share one real dispatch point --
`SelfModelUpdatePhase.apply()` (`src/engine/pipeline.py:192`), gated behind
`ENABLE_SELF_MODEL_COGNITION` (`FeatureMode.OFF` by default). `knowledge_model`
(`KnowledgeModelService`) is one of the 4 sub-services `SelfModelUpdatePhase.run()` orchestrates
(see `self_model`'s own registry note) -- a single real scenario against the shared gate genuinely
exercises both, unlike `strategic_learning_bias`/`concern_intake`'s own separate branches, which the
shared `strategic_intelligence` scenario explicitly did NOT cover.

World: `data/worlds/unit_selfmodel_pilot/` -- a real, purpose-built, already-compiled world
(`TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT`) that composes `frontier_village_core` +
`hero_adventurers` and stages one real `pending_self_model_information_events` entry resolving to
a real compiled entity (actor_id 15) with a genuine unknown fact about `material.wood.source` --
reused as-is, not authored for this scenario, since it already exists specifically for self-model
testing. `state.feature_flags` is confirmed empty by default even for this world (the world's own
"ENABLE_SELF_MODEL_COGNITION is ON via this world's own profile YAML" description refers to a
SimQ-corpus-runner-level override, not something `WorldCompiler.compile()` itself applies) --
confirmed directly, not assumed, before staging.

Differential design: same compiled world/entity/pending event, same real `Kernel.tick_once()`
dispatch at `state.tick=1` (not 0 -- `last_self_check_tick=0` is indistinguishable from "never
updated" at tick 0, a real ambiguity caught empirically before it became a vacuous assertion), only
`state.feature_flags["ENABLE_SELF_MODEL_COGNITION"]` differs --
- "mechanism present" (flag ON): the entity's real pending unknown-fact event is assimilated --
  `self_model.knowledge.unknowns["material.wood.source"]` becomes a real `UnknownFact`
  (`knowledge_model`), and `self_model.self_awareness.last_self_check_tick` updates to the real
  tick (`self_model`).
- "mechanism absent" (flag OFF, the real default): `self_model` stays at its fully compiled default
  (`SelfModelBundle.empty()`-equivalent) -- the phase never runs.
Backing (per proposal doc §5 item 4, same reachability-claim shape as `temporal_pressure`'s own
already-audited entry): (a) static -- `ENABLE_SELF_MODEL_COGNITION` defaults OFF in
`src/domains/optimization/feature_flags.py`, independent of world choice; §5 item 5's reach-proof
requirement does not apply to this negative arm for the same reason it doesn't apply to
`temporal_pressure`'s.
"""
import os

from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository
from src.engine.kernel import Kernel
from src.config.profiles import PROD_SMALL
from src.platform.rng import DeterministicRNG
from src.domains.optimization.feature_flags import FeatureMode

WORLD_ID = "unit_selfmodel_pilot"
GENERATION_SEED = 503
ACTOR_ID = 15
SEED = 503


def _compile_world():
    repo = WorldRepository(os.path.join("data", "worlds"))
    spec, context = repo.load_world_with_context(WORLD_ID)
    state, _report = WorldCompiler.compile(spec, GENERATION_SEED, context=context)
    return state


def _stage_flag_and_tick(state, *, self_model_flag):
    object.__setattr__(state, "tick", 1)
    if self_model_flag is not None:
        object.__setattr__(state, "feature_flags", {"ENABLE_SELF_MODEL_COGNITION": self_model_flag})
    return state


def _run_one_tick_and_get_self_model(state):
    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(SEED), flags={"no_frame_pacing": True})
    try:
        kernel.tick_once()
        final_state = kernel._state
    finally:
        kernel.shutdown()
    return final_state.entities[ACTOR_ID].self_model


def test_self_model_and_knowledge_model_update_when_self_model_cognition_is_enabled():
    """Mechanism present: ENABLE_SELF_MODEL_COGNITION=ON. The entity's own real pending unknown-fact
    event must be assimilated (knowledge_model) and self-awareness re-checked (self_model), through
    a real Kernel dispatch of the actual pending_self_model_information_events this world compiles."""
    state = _compile_world()
    state = _stage_flag_and_tick(state, self_model_flag=FeatureMode.ON)

    self_model = _run_one_tick_and_get_self_model(state)

    assert "material.wood.source" in self_model.knowledge.unknowns, (
        "knowledge_model mechanic: expected the entity's own real pending unknown-fact event to be "
        f"assimilated when ENABLE_SELF_MODEL_COGNITION=ON, but unknowns was "
        f"{self_model.knowledge.unknowns!r}."
    )
    assert self_model.self_awareness.last_self_check_tick == 1, (
        "self_model mechanic: expected self_awareness to be re-checked (last_self_check_tick=1) "
        f"when ENABLE_SELF_MODEL_COGNITION=ON, but got "
        f"{self_model.self_awareness.last_self_check_tick!r}."
    )


def test_self_model_and_knowledge_model_stay_default_when_self_model_cognition_is_off_the_real_default():
    """Mechanism absent: no feature_flags override -- the real, shipped default
    (ENABLE_SELF_MODEL_COGNITION=OFF). SelfModelUpdatePhase never runs, so self_model must stay at
    its fully compiled default for both the self-awareness and the knowledge halves."""
    state = _compile_world()
    state = _stage_flag_and_tick(state, self_model_flag=None)

    self_model = _run_one_tick_and_get_self_model(state)

    assert self_model.knowledge.unknowns == {}, (
        "knowledge_model mechanic: expected unknowns to stay empty with ENABLE_SELF_MODEL_COGNITION "
        f"at its real default (OFF), but got {self_model.knowledge.unknowns!r}."
    )
    assert self_model.self_awareness.last_self_check_tick == 0, (
        "self_model mechanic: expected last_self_check_tick to stay at its compiled default (0) "
        f"with the flag off, but got {self_model.self_awareness.last_self_check_tick!r}."
    )


def test_knowledge_model_service_itself_works_when_called_directly():
    """Positive control: the service's own logic is not broken -- calling
    KnowledgeModelService.assimilate() directly against the same real pending event produces the
    same real unknown-fact record the gated-ON scenario above observes through the real pipeline."""
    from src.cognition.knowledge_model import KnowledgeModelService
    from src.core.self_model import SelfModelBundle

    state = _compile_world()
    entity = state.entities[ACTOR_ID]
    event = state.pending_self_model_information_events[0]["event"]

    new_knowledge = KnowledgeModelService.assimilate(entity, event, tick=1)

    assert "material.wood.source" in new_knowledge.unknowns
