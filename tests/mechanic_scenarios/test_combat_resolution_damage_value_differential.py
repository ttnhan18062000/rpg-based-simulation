"""Runtime-evidence program, value-differential axis, combat batch 1
(TCK-20260921-MECHANISM-COMBAT-VALUE-DIFFERENTIAL-INSTRUMENT): applies the instrument to
`combat_resolution`'s own `CombatResolutionSystem.calculate_damage()` (src/engine/combat.py:31-46)
-- the answer to the question motivating this program's choice of `combat` as its next target: do
an entity's attributes have any real purchase on how a fight resolves?

`damage = (atk * atk_mult) * ((atk * atk_mult) / ((atk * atk_mult) + (def * def_mult) * 2.0 +
1.0))`. Pure function of `attacker.combat.atk`/`defender.combat.def_stat` only, no RNG call
anywhere in the function body (re-confirmed by direct code read, same conclusion already reached
during the progression program's own `evolution`/`xp_leveling` determinism-trap investigation).

The value under test here is `combat.atk`/`combat.def_stat` DIRECTLY, not `attributes.strength`
upstream of them -- `attributes.strength -> combat.atk` is `derived_stats`'s own mechanism, already
value-differential-tested in the progression program (+10 strength moves atk by exactly +5).
Staging `combat.atk` directly tests `combat_resolution`'s own real, direct input, not a re-test of
`derived_stats` under a different name.

World: reused `data/worlds/mechanic_scenario_combat_judgement_withdrawal/` (goblin vs orc, already
proven a legal forced-attack pairing by an existing test). Orc's `combat.hp` staged HIGH (well
above any single hit) so the attack never kills -- the value under test is the DAMAGE dealt, not
whether a kill happens, unlike this program's own earlier XP-reward test.
"""
import os
from dataclasses import replace

from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository
from src.engine.kernel import Kernel
from src.config.profiles import PROD_SMALL
from src.platform.rng import DeterministicRNG
from src.core.state import TaskComponent

WORLD_ID = "mechanic_scenario_combat_judgement_withdrawal"
GOBLIN_ID = 1
ORC_ID = 2
SEED = 42
ORC_STARTING_HP = 200.0


def _compile_world():
    repo = WorldRepository(os.path.join("data", "worlds"))
    spec, context = repo.load_world_with_context(WORLD_ID)
    state, _report = WorldCompiler.compile(spec, SEED, context=context)
    return state


def _run_arm(*, attacker_atk: float, attacker_evolution_level: int = 1):
    state = _compile_world()
    goblin = state.entities[GOBLIN_ID]
    orc = state.entities[ORC_ID]

    goblin = replace(
        goblin,
        navigation=replace(goblin.navigation, position=(0.0, 0.0)),
        combat=replace(goblin.combat, atk=attacker_atk),
        identity=replace(goblin.identity, evolution_level=attacker_evolution_level),
        task=TaskComponent(work_kind="ENTITY_ACT", payload={"action": "ATTACK", "target_id": ORC_ID}),
    )
    orc = replace(
        orc,
        navigation=replace(orc.navigation, position=(1.0, 0.0)),
        combat=replace(orc.combat, hp=ORC_STARTING_HP, max_hp=ORC_STARTING_HP),
    )

    new_entities = dict(state.entities)
    new_entities[GOBLIN_ID] = goblin
    new_entities[ORC_ID] = orc
    object.__setattr__(state, "entities", new_entities)

    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(SEED), flags={"no_frame_pacing": True})
    try:
        kernel.tick_once()
        final_state = kernel._state
    finally:
        kernel.shutdown()
    orc_after = final_state.entities[ORC_ID]
    damage_dealt = ORC_STARTING_HP - orc_after.combat.hp
    return damage_dealt, orc_after


def test_attacker_atk_scales_damage_by_the_documented_formula():
    """Positive control: varying ONLY attacker.combat.atk must move the resulting damage by
    exactly the documented formula, holding defender.combat.def_stat fixed at its real compiled
    value."""
    baseline_damage, orc_after = _run_arm(attacker_atk=8.0)
    varied_damage, _ = _run_arm(attacker_atk=20.0)

    def_stat = float(orc_after.combat.def_stat)
    expected_baseline = int(8.0 * (8.0 / (8.0 + def_stat * 2.0 + 1.0)))
    expected_varied = int(20.0 * (20.0 / (20.0 + def_stat * 2.0 + 1.0)))

    assert baseline_damage == expected_baseline, (
        f"combat_resolution mechanic: expected baseline damage {expected_baseline} "
        f"(atk=8.0, def_stat={def_stat}), got {baseline_damage}."
    )
    assert varied_damage == expected_varied, (
        f"combat_resolution mechanic: expected varied damage {expected_varied} "
        f"(atk=20.0, def_stat={def_stat}), got {varied_damage}."
    )
    assert varied_damage > baseline_damage, (
        f"combat_resolution mechanic: expected higher atk to deal more damage, but baseline="
        f"{baseline_damage}, varied={varied_damage}."
    )


def test_attacker_evolution_level_does_not_change_damage_dealt():
    """Negative control: identity.evolution_level is provably never read by calculate_damage() (or
    by anything feeding its inputs) -- already established directly in the progression program's
    own evolution/xp_leveling determinism-trap trace. Varying it here, holding combat.atk fixed,
    must produce identical damage."""
    baseline_damage, _ = _run_arm(attacker_atk=8.0, attacker_evolution_level=1)
    varied_damage, _ = _run_arm(attacker_atk=8.0, attacker_evolution_level=50)

    assert varied_damage == baseline_damage, (
        "combat_resolution mechanic negative control: attacker evolution_level must not change "
        f"damage dealt, but it did (baseline {baseline_damage}, varied {varied_damage})."
    )
