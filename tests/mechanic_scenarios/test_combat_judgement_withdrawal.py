"""First scenario for TCK-20260915-MECHANIC-VERIFICATION-SCENARIOS: does the combat-judgement
posture gate (src/engine/domain/action_router.py, TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-
WIRED-TO-EXECUTION) actually withhold a real attack when the attacker's own combat_engagement
assessment has rejected that exact fight?

World: data/worlds/mechanic_scenario_combat_judgement_withdrawal/ -- real, compiled, catalog-
driven content (goblin_scout vs orc_warchief, a real authored mismatch via
faction_relationships.yaml's "weaker_rival_fear"), not a synthetic V2EntityBuilder fixture.

Differential design, not a single pass/fail (peer review's explicit correction after this
scenario's first, naive attempt showed an identical outcome regardless of the gate -- because the
scenario staged the wrong precondition, not because the gate doesn't work): the scenario runs
twice, same forced ATTACK dispatch, only the precondition the gate itself reads differs --
- "mechanism present": the attacker has a real recorded posture toward this exact target, and
  it's risk-rejected ("avoid").
- "mechanism absent": no posture is recorded for this pairing at all (the documented, real
  "absence does not withhold" case -- not a monkeypatch of the gate's own code, an actual
  supported precondition).
A scenario that shows the same outcome in both conditions has not tested the mechanism, whatever
its name claims -- see the general principle this test exists to enforce, not just to pass once.
"""
import os
from dataclasses import replace

import pytest

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


def _stage_forced_attack(state, *, posture: str | None):
    """Forces the goblin's task to a pending ATTACK against the orc, at melee range, bypassing
    tactical.py's own decision entirely -- isolating the action_router.py dispatch checkpoint,
    which is the actual per-attack gate (see TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-
    TO-EXECUTION's own Implementation Notes for why a decision-point gate is not equivalent to
    this). `posture=None` stages the "mechanism absent" condition; any risk-rejected posture
    string stages the "mechanism present, rejects" condition.
    """
    goblin = state.entities[GOBLIN_ID]
    orc = state.entities[ORC_ID]

    new_props = dict(goblin.identity.properties)
    if posture is not None:
        new_props["last_combat_posture"] = posture
        new_props["last_combat_posture_target"] = ORC_ID
    else:
        new_props.pop("last_combat_posture", None)
        new_props.pop("last_combat_posture_target", None)

    goblin = replace(
        goblin,
        navigation=replace(goblin.navigation, position=(0.0, 0.0)),
        identity=replace(goblin.identity, properties=new_props),
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


def test_combat_judgement_gate_withholds_a_real_attack_when_posture_rejects_it():
    """Mechanism present: the goblin's own posture toward the orc is "avoid" (risk-rejected).
    The gate must withhold the real attack -- CombatActions.execute_attack must NOT be called
    for the goblin this tick, even though a pending ATTACK task was staged.
    """
    state = _compile_world()
    state = _stage_forced_attack(state, posture="avoid")

    goblin_attacks = _run_one_tick_and_count_goblin_attacks(state)

    assert goblin_attacks == 0, (
        "combat_judgement mechanic: expected the posture gate "
        "(src/engine/domain/action_router.py) to withhold the goblin's attack given a "
        "recorded 'avoid' posture toward the orc, but CombatActions.execute_attack was called "
        f"{goblin_attacks} time(s) for the goblin -- the gate did not block a risk-rejected attack."
    )


def test_combat_judgement_gate_does_not_withhold_when_no_posture_is_recorded():
    """Mechanism absent: no posture is recorded for this pairing at all (as if combat_engagement
    never assessed it -- flag off, or a cold-start tick). The gate must NOT withhold the attack;
    absence of a verdict is not itself a verdict (see the gate's own comment in
    action_router.py). This is the differential half: without this passing too, the first test
    could pass for a reason unrelated to the gate (e.g. the attack being blocked by something
    else entirely, like legality or readiness) and the scenario would not actually be testing
    the posture gate specifically.
    """
    state = _compile_world()
    state = _stage_forced_attack(state, posture=None)

    goblin_attacks = _run_one_tick_and_count_goblin_attacks(state)

    assert goblin_attacks > 0, (
        "combat_judgement mechanic: expected the staged attack to proceed when no posture is "
        "recorded for this pairing (absence of a verdict must not withhold an attack), but "
        f"CombatActions.execute_attack was called {goblin_attacks} time(s) for the goblin -- "
        "either the attack was blocked by something other than the posture gate (a real defect "
        "in scenario staging, not the gate itself), or the gate is over-blocking when it should "
        "no-op."
    )
