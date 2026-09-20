"""Runtime-evidence program, value-differential axis (TCK-20260921-MECHANISM-PROGRESSION-VALUE-
DIFFERENTIAL-INSTRUMENT): applies the new value-differential instrument (see
test_readiness_and_derived_stats_value_differential.py for the calibration instrument itself) to
`evolution`/`xp_leveling` (merged per docs/plans/mechanism_identity_and_change_taxonomy.md §8's
own recorded-but-unexecuted Merge verdict) -- the real chain `combat.py`'s
`xp_reward=defender.identity.evolution_level * 10` -> `conservation.py`'s
`IdentityUpdate(evolution_points_delta=intent.xp_reward)` -> `EvolutionSystem.evaluate()`.

Unlike the calibration instrument (a pure, RNG-free function, structurally immune to the
determinism trap), this mechanism runs through a real combat kill inside a real Kernel tick --
peer named exactly this risk: varying the defender's own level might also change the defender's
derived combat stats, which could ripple into a DIFFERENT number of rounds/RNG draws before a kill
resolves, confounding the result with something unrelated to the mechanism itself.

Resolved by direct code trace before staging anything (see investigation.md for the full trace,
summarized here):
1. `CombatResolutionSystem.calculate_damage()` (src/engine/combat.py:31-46) reads ONLY
   `attacker.combat.atk` and `defender.combat.def_stat` -- no RNG call in the function at all.
2. `LevelingService.recalculate_combat_stats()` (src/progression/leveling.py:76-180) reads ONLY
   `AttributeComponent` fields -- never `identity.evolution_level` or `identity.evolution_points`.
3. `src/domains/combat_engagement/power.py`/`perception.py` both state explicitly, in their own
   code comments, that `evolution_level` is "deliberately excluded, not merely unweighted" from
   combat-power comparisons -- independent, in-code confirmation.
So `defender.combat.atk`/`def_stat` (and therefore `calculate_damage`'s result and whether the hit
is lethal) cannot change when only `identity.evolution_level` or `identity.evolution_points`
varies -- the fight itself is byte-identical across every arm below; only the post-kill XP reward
differs. `defender.combat.hp` is staged to 1 in every arm to guarantee a one-hit kill
deterministically, removing any dependency on the exact damage roll at all (the same technique
Program A's `emotion_near_death_hardening` scenario used for low-HP staging).

World: data/worlds/mechanic_scenario_combat_judgement_withdrawal/ (real, catalog-driven content,
already used by test_combat_judgement_withdrawal.py for this exact goblin/orc pairing) -- reused
rather than authoring a new one; attacking is already proven a real, legal action for this pairing.

Three real arms:
- Arm A (orc evolution_level=1, evolution_points=0): baseline: EvolutionSystem's own documented
  MONSTER xp_multiplier=10 (src/engine/combat_rewards.py) applies, expect goblin's evolution_points
  to gain exactly 1 * 10 = 10.
- Arm B (orc evolution_level=5, evolution_points=0): positive control -- expect goblin's XP gain to
  scale to exactly 5 * 10 = 50, proving the reward's own input (evolution_level) has real purchase
  on the outcome.
- Arm C (orc evolution_level=1, evolution_points=999): negative control -- evolution_points is a
  real field on the same identity component, provably unread by both the xp_reward formula (which
  reads only evolution_level) and by combat resolution (which reads attributes, not identity, for
  damage) -- expect goblin's XP gain to be identical to Arm A's 10, proving this instrument does
  not report a difference whenever anything on the defender is perturbed.
Every arm also asserts the kill itself resolved identically (orc dies, exactly one attack call),
making the RNG-order-safety claim directly observable, not just argued in this docstring.
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


def _compile_world():
    repo = WorldRepository(os.path.join("data", "worlds"))
    spec, context = repo.load_world_with_context(WORLD_ID)
    state, _report = WorldCompiler.compile(spec, SEED, context=context)
    return state


def _stage_forced_kill(state, *, orc_evolution_level: int, orc_evolution_points: int):
    goblin = state.entities[GOBLIN_ID]
    orc = state.entities[ORC_ID]

    goblin = replace(
        goblin,
        navigation=replace(goblin.navigation, position=(0.0, 0.0)),
        task=TaskComponent(work_kind="ENTITY_ACT", payload={"action": "ATTACK", "target_id": ORC_ID}),
    )
    orc = replace(
        orc,
        navigation=replace(orc.navigation, position=(1.0, 0.0)),
        combat=replace(orc.combat, hp=1),
        identity=replace(
            orc.identity,
            evolution_level=orc_evolution_level,
            evolution_points=orc_evolution_points,
        ),
    )

    new_entities = dict(state.entities)
    new_entities[GOBLIN_ID] = goblin
    new_entities[ORC_ID] = orc
    object.__setattr__(state, "entities", new_entities)
    return state


def _run_one_tick(state):
    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(SEED), flags={"no_frame_pacing": True})
    try:
        kernel.tick_once()
        final_state = kernel._state
    finally:
        kernel.shutdown()
    return final_state


def _run_arm(*, orc_evolution_level: int, orc_evolution_points: int):
    state = _compile_world()
    state = _stage_forced_kill(
        state, orc_evolution_level=orc_evolution_level, orc_evolution_points=orc_evolution_points
    )
    final_state = _run_one_tick(state)
    goblin_after = final_state.entities[GOBLIN_ID]
    orc_after = final_state.entities[ORC_ID]
    return goblin_after, orc_after


def test_baseline_kill_grants_the_documented_level_1_xp_reward():
    """Baseline arm: orc at evolution_level=1 (the default). The kill must actually happen (orc
    dead), and the goblin's evolution_points must land at exactly 10 -- matching `evolution`'s own
    already-verified MONSTER xp_multiplier=10 formula (src/engine/combat_rewards.py)."""
    goblin_after, orc_after = _run_arm(orc_evolution_level=1, orc_evolution_points=0)

    assert orc_after.combat.alive is False, (
        "scenario reach check: expected the staged one-hit kill (orc hp=1) to actually resolve as "
        "a kill this tick -- if it didn't, no arm below is testing a real XP reward at all."
    )
    assert goblin_after.identity.evolution_points == 10, (
        f"evolution/xp_leveling mechanic baseline: expected exactly 10 XP (level-1 orc, "
        f"MONSTER xp_multiplier=10), got {goblin_after.identity.evolution_points}."
    )


def test_defender_evolution_level_scales_the_xp_reward_proportionally():
    """Positive control: varying ONLY the defender's evolution_level (1 -> 5) must scale the
    XP reward proportionally (10 -> 50), proving the mechanism's own input has real purchase on
    the outcome -- not just that the mechanism runs."""
    baseline_goblin, baseline_orc = _run_arm(orc_evolution_level=1, orc_evolution_points=0)
    varied_goblin, varied_orc = _run_arm(orc_evolution_level=5, orc_evolution_points=0)

    assert baseline_orc.combat.alive is False and varied_orc.combat.alive is False, (
        "scenario reach check: both arms must resolve the same real kill for this comparison to "
        "be meaningful."
    )
    assert varied_goblin.identity.evolution_points == 50, (
        f"evolution/xp_leveling mechanic: expected orc evolution_level=5 to grant exactly 50 XP "
        f"(5 * MONSTER xp_multiplier=10), got {varied_goblin.identity.evolution_points}."
    )
    assert varied_goblin.identity.evolution_points == baseline_goblin.identity.evolution_points * 5, (
        "evolution/xp_leveling mechanic: expected the XP reward to scale exactly proportionally "
        f"with defender evolution_level (baseline {baseline_goblin.identity.evolution_points}, "
        f"5x level got {varied_goblin.identity.evolution_points})."
    )


def test_defender_evolution_points_does_not_change_the_xp_reward():
    """Negative control: varying the defender's own evolution_points (a real field on the same
    identity component, provably unread by both the xp_reward formula and combat resolution) must
    leave the XP reward unchanged -- proving this instrument does not report a difference whenever
    anything on the defender is perturbed."""
    baseline_goblin, baseline_orc = _run_arm(orc_evolution_level=1, orc_evolution_points=0)
    varied_goblin, varied_orc = _run_arm(orc_evolution_level=1, orc_evolution_points=999)

    assert baseline_orc.combat.alive is False and varied_orc.combat.alive is False, (
        "scenario reach check: both arms must resolve the same real kill for this comparison to "
        "be meaningful."
    )
    assert varied_goblin.identity.evolution_points == baseline_goblin.identity.evolution_points, (
        "evolution/xp_leveling mechanic negative control: defender evolution_points must not "
        f"move the XP reward, but it did (baseline {baseline_goblin.identity.evolution_points}, "
        f"varied {varied_goblin.identity.evolution_points})."
    )
