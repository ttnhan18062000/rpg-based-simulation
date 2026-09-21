"""Runtime-evidence program, value-differential axis, combat -- narrow re-scope
(TCK-20260921-MECHANISM-COMBAT-VALUE-DIFFERENTIAL-INSTRUMENT, re-scoped by peer from an 8-mechanism
sweep to one direct question): within a real fight, does an entity's own combat attributes have
measurable purchase on the outcome, or not?

Chains the two real, already-confirmed-RNG-free formulas this program's own investigation
established:
1. `LevelingService.recalculate_combat_stats()` (src/progression/leveling.py:76-105) --
   `attributes.strength` -> `atk`, `attributes.vitality` -> `def_stat`. Called directly here with
   two real attribute presets, the SAME function the real pipeline uses (not a shortcut or
   synthetic replacement) -- legitimate because the real apply-path sequencing recalculates
   derived stats only at the END of the tick that changed attributes, meaning a same-tick
   attribute-change-then-attack test would use the OLD atk anyway; calling the real derivation
   function directly to get the value a real recalculation WOULD produce, then staging that
   result, tests the same real formula without a misleading same-tick race.
2. `CombatResolutionSystem.calculate_damage()` (src/engine/combat.py:31-46) -- dispatched through
   a real `Kernel.tick_once()` forced attack, reusing `mechanic_scenario_combat_judgement_
   withdrawal` (goblin vs orc, already proven a legal forced-attack pairing).

Determinism trap, resolved by code trace before staging anything (both functions re-read in full
for this test, same conclusion as this program's own prior investigation): neither function
contains an RNG call. `calculate_damage()` reads only `combat.atk`/`combat.def_stat`; varying the
attacker's attributes changes only the DERIVED `atk` value fed into it, never the fight's own RNG
surface (there is none). Confirmed empirically too: both arms below resolve the same real one-hit
outcome shape (a single real dispatched attack, no retries, no branching).

Positive control: attacker attributes with real strength=20 (vs a real strength=5 baseline,
`AttributeComponent`'s own documented default) produce a higher real `atk` via the real formula,
and the resulting real fight deals more damage to a fixed, undamaged defender -- the ONE, direct
answer to "do combat attributes have real purchase on a real fight's outcome."

Negative control: attacker attributes varied only on `charisma` (confirmed, by re-reading
`recalculate_combat_stats()` in full, to feed none of its outputs -- the function reads only
strength/vitality/endurance/agility) leave the derived atk, and therefore the real fight's outcome,
unchanged -- proving this observation is not an artifact of perturbing anything on the entity.

Recorded against `combat_resolution` only (the mechanism this scenario actually dispatches and
observes) -- not stretched across `derived_stats` (already independently value-tested in the
progression program) or any other entry this scenario does not itself exercise.
"""
import os
from dataclasses import replace

from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository
from src.engine.kernel import Kernel
from src.config.profiles import PROD_SMALL
from src.platform.rng import DeterministicRNG
from src.core.state import TaskComponent, AttributeComponent
from src.progression.leveling import LevelingService

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


def _derived_atk_for(attributes: AttributeComponent) -> float:
    """Real derivation, same function the authoritative apply path calls -- not a shortcut."""
    derived = LevelingService.recalculate_combat_stats(attributes)
    return float(derived["atk"])


def _run_arm(*, attacker_attributes: AttributeComponent):
    state = _compile_world()
    goblin = state.entities[GOBLIN_ID]
    orc = state.entities[ORC_ID]

    real_derived_atk = _derived_atk_for(attacker_attributes)

    goblin = replace(
        goblin,
        navigation=replace(goblin.navigation, position=(0.0, 0.0)),
        attributes=attacker_attributes,
        combat=replace(goblin.combat, atk=real_derived_atk),
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
    return damage_dealt


def test_attacker_strength_has_real_purchase_on_a_real_fights_outcome():
    """Positive control, the one-sentence deliverable: a real strength difference, run through the
    real derivation formula and a real dispatched fight, produces a real, larger damage output."""
    baseline_attrs = AttributeComponent()  # real documented default: strength=5
    strong_attrs = replace(baseline_attrs, strength=20)

    baseline_damage = _run_arm(attacker_attributes=baseline_attrs)
    strong_damage = _run_arm(attacker_attributes=strong_attrs)

    assert strong_damage > baseline_damage, (
        f"combat_resolution mechanic: expected a real strength increase (5 -> 20) to deal more "
        f"real damage in a real dispatched fight, but baseline={baseline_damage}, "
        f"strong={strong_damage}. Within a real fight, this entity's own combat attributes did "
        f"NOT have measurable purchase on the outcome."
    )


def test_attacker_charisma_does_not_move_the_fights_outcome():
    """Negative control: charisma is provably never read by recalculate_combat_stats() (re-read in
    full -- only strength/vitality/endurance/agility feed any output). Varying it must leave the
    real derived atk, and therefore the real fight's outcome, unchanged."""
    baseline_attrs = AttributeComponent()
    high_charisma_attrs = replace(baseline_attrs, charisma=50)

    assert _derived_atk_for(baseline_attrs) == _derived_atk_for(high_charisma_attrs), (
        "sanity check: charisma must not move the real derived atk at all before even dispatching "
        "a fight."
    )

    baseline_damage = _run_arm(attacker_attributes=baseline_attrs)
    high_charisma_damage = _run_arm(attacker_attributes=high_charisma_attrs)

    assert high_charisma_damage == baseline_damage, (
        "combat_resolution mechanic negative control: charisma must not move a real fight's "
        f"outcome, but baseline={baseline_damage}, high-charisma={high_charisma_damage}."
    )
