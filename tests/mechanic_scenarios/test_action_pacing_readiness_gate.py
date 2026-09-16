"""First real use of docs/plans/mechanic_verification_scenarios_proposal.md's component to verify
a mechanism named by docs/brainstorm/mechanisms.yaml -- `action_pacing_readiness`
(`TCK-20260916-ACTION-PACING-READINESS-SCENARIO-VERIFICATION`). Does the readiness gate
(`src/engine/legality.py::LegalityServiceV2.verify_readiness`, dispatched from
`src/engine/domain/action_router.py`'s "0. Readiness Check") actually withhold a real action when
an entity's own `combat.readiness` is below 100.0, in a real compiled world, through the real
Kernel tick loop -- not just a code trace confirming the check exists and is called?

World: data/worlds/mechanic_scenario_combat_judgement_withdrawal/ -- reused as-is (real, compiled,
catalog-driven goblin_scout vs orc_warchief), not a new world authored for this scenario. This
world's entities compile with `combat.readiness == 100.0` by default (confirmed directly, not
assumed) and carry no `last_combat_posture` for this pairing unless a test stages one -- so reusing
it lets this scenario isolate the readiness gate specifically, without needing to also stage or
neutralize the separate posture gate `test_combat_judgement_withdrawal.py` already verifies. Posture
is left untouched (absent) in both conditions here.

Differential design, per the proposal's own §3.3 mandatory requirement (the combat-judgement
scenario's own first, naive attempt is the in-house cautionary example this test is built not to
repeat): the scenario runs twice, same forced ATTACK dispatch through the same
`ActionRouter.execute_action` checkpoint, only `combat.readiness` differs --
- "mechanism present" (the gate's own blocking condition is met): `readiness = 50.0` (< 100.0) --
  the gate must withhold the attack.
- "mechanism absent" (the gate's blocking condition is not met): `readiness = 100.0` (the
  compiled default, unmodified) -- the attack must proceed.
A scenario showing the same outcome in both conditions would not have tested the gate, whatever its
name claims.

Scope note, per the ticket's own explicit instruction: this verifies the readiness GATE only --
the registry's own `state: partial` on this mechanism separately (and already, via code_trace)
captures that `readiness_speed` is flat 10.0 for every entity rather than scaling with agility
(TCK-20260831-READINESS-SPEED-FORMULA, filed, not fixed here). That is a distinct claim about a
different code path (the derived-stats recalculation that would set `readiness_speed`, not the
gate that reads `readiness` against the 100.0 threshold) and is out of scope for this scenario --
verification here is about whether the gate itself works, which is what the mechanism's 23
transitive dependents actually depend on being true.
"""
import os
from dataclasses import replace

from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository
from src.engine.kernel import Kernel
from src.config.profiles import PROD_SMALL
from src.platform.rng import DeterministicRNG
from src.engine.domain.combat_actions import CombatActions
from src.core.state import TaskComponent

WORLD_ID = "mechanic_scenario_combat_judgement_withdrawal"
GOBLIN_ID = 1
ORC_ID = 2
SEED = 42


def _compile_world():
    repo = WorldRepository(os.path.join("data", "worlds"))
    spec, context = repo.load_world_with_context(WORLD_ID)
    state, _report = WorldCompiler.compile(spec, SEED, context=context)
    return state


def _stage_forced_attack(state, *, readiness: float):
    """Forces the goblin's task to a pending ATTACK against the orc, at melee range, isolating the
    action_router.py dispatch checkpoint -- same staging shape as
    test_combat_judgement_withdrawal.py, with `readiness` as the only varied precondition and
    posture left entirely unset (absent, per that scenario's own confirmed non-blocking case) in
    both conditions here."""
    goblin = state.entities[GOBLIN_ID]
    orc = state.entities[ORC_ID]

    goblin = replace(
        goblin,
        navigation=replace(goblin.navigation, position=(0.0, 0.0)),
        combat=replace(goblin.combat, readiness=readiness),
        task=TaskComponent(work_kind="ENTITY_ACT", payload={"action": "ATTACK", "target_id": ORC_ID}),
    )
    orc = replace(orc, navigation=replace(orc.navigation, position=(1.0, 0.0)))

    new_entities = dict(state.entities)
    new_entities[GOBLIN_ID] = goblin
    new_entities[ORC_ID] = orc
    object.__setattr__(state, "entities", new_entities)
    return state


def _run_one_tick_and_count_goblin_attacks(state) -> int:
    orig_attack = CombatActions.execute_attack
    calls = []

    def wrapped(entity, payload, current_tick, neighbor_view, context_arg):
        calls.append(entity.id)
        return orig_attack(entity, payload, current_tick, neighbor_view, context_arg)

    CombatActions.execute_attack = staticmethod(wrapped)
    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(SEED), flags={"no_frame_pacing": True})
    try:
        kernel.tick_once()
    finally:
        kernel.shutdown()
        CombatActions.execute_attack = staticmethod(orig_attack)

    return sum(1 for eid in calls if eid == GOBLIN_ID)


def test_readiness_gate_withholds_a_real_action_when_readiness_is_below_threshold():
    """Mechanism present: the goblin's own combat.readiness is 50.0 (< 100.0). The gate must
    withhold the real attack -- CombatActions.execute_attack must NOT be called for the goblin
    this tick, even though a pending ATTACK task was staged."""
    state = _compile_world()
    state = _stage_forced_attack(state, readiness=50.0)

    goblin_attacks = _run_one_tick_and_count_goblin_attacks(state)

    assert goblin_attacks == 0, (
        "action_pacing_readiness mechanic: expected the readiness gate "
        "(src/engine/legality.py::verify_readiness) to withhold the goblin's attack given "
        "combat.readiness=50.0 (< 100.0), but CombatActions.execute_attack was called "
        f"{goblin_attacks} time(s) for the goblin -- the gate did not block an under-threshold action."
    )


def test_readiness_gate_does_not_withhold_when_readiness_meets_the_threshold():
    """Mechanism absent: the goblin's own combat.readiness is 100.0 (the compiled default,
    unmodified -- meets the threshold exactly). The gate must NOT withhold the attack. This is the
    differential half: without this passing too, the first test could pass for a reason unrelated
    to the readiness gate (e.g. the attack being blocked by legality, range, or some other check
    entirely), and the scenario would not actually be testing the readiness gate specifically."""
    state = _compile_world()
    state = _stage_forced_attack(state, readiness=100.0)

    goblin_attacks = _run_one_tick_and_count_goblin_attacks(state)

    assert goblin_attacks > 0, (
        "action_pacing_readiness mechanic: expected the staged attack to proceed when "
        "combat.readiness=100.0 (meets the 100.0 threshold), but CombatActions.execute_attack "
        f"was called {goblin_attacks} time(s) for the goblin -- either the attack was blocked by "
        "something other than the readiness gate (a real defect in scenario staging, not the gate "
        "itself), or the gate is over-blocking when it should not."
    )
