"""Runtime-evidence program, batch 2 (TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION,
Bucket C, one of the 3 independent questions). Does `emotion`
(`src/domains/emotion/emotion_service.py::EmotionUpdateService`) actually fire through the real,
unconditional `near_death_hardening` phase (`src/engine/pipeline.py:410`, no feature-flag argument),
not just that the call site exists in code?

World: `data/worlds/mechanic_scenario_combat_judgement_withdrawal/` -- reused as-is. Real forced
attack (orc -> goblin), same staging technique as `test_combat_judgement_withdrawal.py`'s own
precedent, calibrated empirically (not guessed): a real attack in this world/seed does 19 real
damage (confirmed directly, not assumed).

Differential design, per proposal doc §3.3/§5 item 3: same forced attack dispatch, only the
goblin's own pre-attack `combat.hp` differs --
- "mechanism present": `hp=21` before the attack. Post-attack `hp=2`, `2 <= near_death_threshold`
  (10% of `max_hp`, real formula in `NearDeathHardeningPhase.apply()`) and `> 0` -- survives at
  critically low HP. `EmotionUpdateService.update_on_event(..., "near_death")` must fire:
  `fear += 0.4`, `panic += 0.5`, `confidence -= 0.3` from their real compiled defaults.
- "mechanism absent": `hp=35` (the compiled default) before the same attack. Post-attack `hp=16`,
  well above the near-death threshold -- the emotional model must stay at its compiled defaults.

Per §5 item 5 (added after `goal_hierarchy`'s own scenario surfaced a vacuous-negative-arm risk):
the negative arm's "nothing changed" is confirmed to mean reached-and-declined, not unevaluated --
`NearDeathHardeningPhase.apply()` only skips an entity that has NO staged `combat.CombatUpdate` at
all for the tick; both conditions here stage a real attack that DOES produce one (confirmed directly
via instrumentation, not assumed from the HP delta alone), so the goblin enters the per-entity loop
and is genuinely evaluated against the `survived`/`near_death_threshold` checks in both conditions --
unlike `goal_hierarchy`'s own first, buggy attempt, there is no per-entity cadence gate on this phase
at all to trip over.
"""
import os
from dataclasses import replace

from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository
from src.engine.kernel import Kernel
from src.config.profiles import PROD_SMALL
from src.platform.rng import DeterministicRNG
from src.core.state import TaskComponent
from src.engine.pipeline_phases.hardening import NearDeathHardeningPhase

WORLD_ID = "mechanic_scenario_combat_judgement_withdrawal"
GOBLIN_ID = 1
ORC_ID = 2
SEED = 42


def _compile_world():
    repo = WorldRepository(os.path.join("data", "worlds"))
    spec, context = repo.load_world_with_context(WORLD_ID)
    state, _report = WorldCompiler.compile(spec, SEED, context=context)
    return state


def _stage_forced_attack(state, *, goblin_pre_attack_hp: int):
    """Forces a real orc -> goblin ATTACK dispatch (orc is the aggressor so the goblin, not the
    orc, is the one whose survival-emotion path this scenario tests) -- same forced-dispatch
    technique as `test_combat_judgement_withdrawal.py`'s own precedent, with the goblin's
    pre-attack HP as the only varied precondition."""
    goblin = state.entities[GOBLIN_ID]
    orc = state.entities[ORC_ID]

    orc = replace(
        orc,
        navigation=replace(orc.navigation, position=(0.0, 0.0)),
        task=TaskComponent(work_kind="ENTITY_ACT", payload={"action": "ATTACK", "target_id": GOBLIN_ID}),
    )
    goblin = replace(
        goblin,
        navigation=replace(goblin.navigation, position=(1.0, 0.0)),
        combat=replace(goblin.combat, hp=goblin_pre_attack_hp),
    )

    new_entities = dict(state.entities)
    new_entities[ORC_ID] = orc
    new_entities[GOBLIN_ID] = goblin
    object.__setattr__(state, "entities", new_entities)
    return state


def _run_one_tick_confirming_reach_and_return_goblin(state):
    """Runs a real Kernel tick, confirming (per §5 item 5, not just inferring from the outcome)
    that the goblin genuinely had a real CombatUpdate staged before NearDeathHardeningPhase.apply()
    ran -- i.e. it entered the per-entity loop and was evaluated, not skipped before ever being
    considered."""
    orig_apply = NearDeathHardeningPhase.apply
    reach = {"had_combat_update": None}

    def wrapped(state_arg, update_arg):
        goblin_upd = update_arg.entity_updates.get(GOBLIN_ID)
        reach["had_combat_update"] = goblin_upd is not None and goblin_upd.combat is not None
        return orig_apply(state_arg, update_arg)

    NearDeathHardeningPhase.apply = staticmethod(wrapped)
    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(SEED), flags={"no_frame_pacing": True})
    try:
        kernel.tick_once()
        final_state = kernel._state
    finally:
        kernel.shutdown()
        NearDeathHardeningPhase.apply = staticmethod(orig_apply)

    assert reach["had_combat_update"], (
        "scenario staging defect: the goblin never received a real CombatUpdate this tick, so "
        "NearDeathHardeningPhase would have skipped it before ever evaluating survival -- the "
        "forced attack itself did not land, unrelated to the emotion mechanism being tested."
    )
    return final_state.entities[GOBLIN_ID]


def test_emotion_updates_when_entity_survives_a_near_death_hit():
    """Mechanism present: goblin survives the real attack at 2/107 HP (well within the real 10%
    near-death threshold). EmotionUpdateService.update_on_event(..., "near_death") must fire
    through the real, unconditional near_death_hardening phase."""
    state = _compile_world()
    state = _stage_forced_attack(state, goblin_pre_attack_hp=21)

    goblin = _run_one_tick_confirming_reach_and_return_goblin(state)
    emotion = goblin.cognition.subjective.emotion

    assert goblin.combat.hp > 0, "scenario staging defect: goblin died instead of surviving near-death"
    assert emotion.fear == 0.4, f"emotion mechanic: expected fear=0.4 (0.0 + 0.4) after near_death, got {emotion.fear!r}"
    assert emotion.panic == 0.5, f"emotion mechanic: expected panic=0.5 (0.0 + 0.5) after near_death, got {emotion.panic!r}"
    assert emotion.confidence == 0.2, f"emotion mechanic: expected confidence=0.2 (0.5 - 0.3) after near_death, got {emotion.confidence!r}"


def test_emotion_stays_at_default_when_entity_survives_a_non_critical_hit():
    """Mechanism absent: goblin survives the same real attack at 16/35 HP -- well above the 10%
    near-death threshold. The differential half: without this passing too, the first test could
    pass for a reason unrelated to the near-death check (e.g. every survived hit updating emotion
    regardless of severity)."""
    state = _compile_world()
    state = _stage_forced_attack(state, goblin_pre_attack_hp=35)

    goblin = _run_one_tick_confirming_reach_and_return_goblin(state)
    emotion = goblin.cognition.subjective.emotion

    assert goblin.combat.hp > 0, "scenario staging defect: goblin died instead of surviving the hit"
    assert emotion.fear == 0.0, f"emotion mechanic: expected fear to stay at compiled default 0.0, got {emotion.fear!r}"
    assert emotion.panic == 0.0, f"emotion mechanic: expected panic to stay at compiled default 0.0, got {emotion.panic!r}"
    assert emotion.confidence == 0.5, f"emotion mechanic: expected confidence to stay at compiled default 0.5, got {emotion.confidence!r}"
