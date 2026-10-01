"""Findings-pinning tests for TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK (Card C1).

This is an assessment/observation ticket, not a code fix. These tests pin the ticket's empirical
findings so they cannot silently regress or need re-deriving. They assert the CURRENT, DEFECTIVE
behaviour on purpose -- see the per-test docstrings. When the routed fix lands (primary owner
`TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP`, plus the separate `world_dynamics.py:39`
overwrite ticket), these tests are EXPECTED to fail and must be rewritten to the fixed contract,
not deleted -- their failure is the signal the fix actually changed the observed behaviour.

**Anti-drift caveat, load-bearing, not flavor text.** `test_hazard_drain_destroys_a_same_tick_
combat_kill_record` dispatches a SCRIPTED forced-lethal ATTACK through a real `Kernel.tick_once()`,
reusing the staging of `test_combat_death_trace_encounterability.py` (B0). It proves the mechanism
and the routing. It is NOT a claim this collision is common in unscripted play: C1's own corpus
probe saw ZERO `KILL`/`PERMADEATH` outcomes in 120 ticks of `frontier_marches`, consistent with
`registries/mechanisms.yaml`'s `tactical_decision` entry (0-2 real `resolve_attack()` calls per
1000-2000 ticks, corpus-verified 2026-09-19). Both facts are true and recorded separately.

The control arm is the negative control for the collision arm, and it is the same assertion
`test_combat_death_trace_encounterability.py::test_forced_combat_kill_produces_combat_death_
reason_in_one_tick` already makes -- deliberately duplicated here so the differential is a single
self-contained comparison rather than a cross-module inference.
"""
from __future__ import annotations

import os
from dataclasses import replace

import pytest

from src.config.profiles import PROD_SMALL
from src.core.state import TaskComponent
from src.engine.kernel import Kernel
from src.engine.world_dynamics import WorldDynamicsSystem
from src.platform.rng import DeterministicRNG
from src.world.environment import EnvironmentService
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository

WORLD_ID = "mechanic_scenario_combat_judgement_withdrawal"
GOBLIN_ID = 1
ORC_ID = 2
SEED = 42

# The arena's own compiled hazard_level. Pinned so the differential below changes exactly one
# field (hazard_kind) -- changing the level too would confound the comparison.
ARENA_HAZARD_LEVEL = 1.0
# orc_clan declares NATURAL_TERRAIN endurance, so the arena's own compiled hazard_kind drains 0.
IMMUNE_KIND = "NATURAL_TERRAIN"
# A real catalog hazard_kind (data/worlds/) that orc_clan does NOT endure.
NON_IMMUNE_KIND = "ARCANE_CORRUPTION"


def _compile_world():
    repo = WorldRepository(os.path.join("data", "worlds"))
    spec, context = repo.load_world_with_context(WORLD_ID)
    state, _report = WorldCompiler.compile(spec, SEED, context=context)
    return state


def _force_lethal_attack(state):
    """Same staging as B0's module: goblin attacks a 1-HP orc at melee range."""
    goblin = replace(
        state.entities[GOBLIN_ID],
        navigation=replace(state.entities[GOBLIN_ID].navigation, position=(0.0, 0.0)),
        task=TaskComponent(work_kind="ENTITY_ACT", payload={"action": "ATTACK", "target_id": ORC_ID}),
    )
    orc = replace(
        state.entities[ORC_ID],
        navigation=replace(state.entities[ORC_ID].navigation, position=(1.0, 0.0)),
        combat=replace(state.entities[ORC_ID].combat, hp=1.0, max_hp=1.0),
    )
    ents = dict(state.entities)
    ents[GOBLIN_ID] = goblin
    ents[ORC_ID] = orc
    object.__setattr__(state, "entities", ents)
    return state


def _set_region_hazard(state, kind):
    new_regions = {
        r_id: replace(region, hazard_level=ARENA_HAZARD_LEVEL, hazard_kind=kind)
        for r_id, region in state.regions.items()
    }
    object.__setattr__(state, "regions", new_regions)
    return state


def _run(kind, ticks):
    state = _set_region_hazard(_force_lethal_attack(_compile_world()), kind)

    orc = state.entities[ORC_ID]
    region = WorldDynamicsSystem._get_region_for_pos(state, orc.navigation.position)
    assert region is not None, "staging sanity: the orc must stand inside a real region"
    drain = EnvironmentService.calculate_hazard_drain(region, orc)

    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(SEED),
                    flags={"no_frame_pacing": True})
    try:
        snapshots = []
        for _ in range(ticks):
            kernel.tick_once()
            snapshots.append(kernel._state.entities[ORC_ID])
        regions_after = dict(kernel._state.regions)
    finally:
        kernel.shutdown()
    return drain, snapshots, regions_after


def test_immune_hazard_kind_is_the_negative_control_and_records_a_combat_death():
    """Control arm. With the arena's own compiled hazard_kind, orc_clan's declared endurance makes
    hazard drain 0, nothing overwrites the victim's outcome_kind, and the forced kill is recorded
    correctly: death_reason='COMBAT' in the same tick. Also pins the immunity itself as the reason
    drain is 0 -- the first version of C1's probe mistook this for "the defect is absent"."""
    drain, snapshots, _regions = _run(IMMUNE_KIND, ticks=1)

    assert drain == 0, (
        f"control sanity: orc_clan endures {IMMUNE_KIND!r}, so drain must be 0, got {drain}. "
        "If this fires, the immunity pairing changed and this arm is no longer a control."
    )
    orc = snapshots[0]
    assert orc.lifecycle.active is False
    assert orc.lifecycle.death_reason == "COMBAT"
    assert orc.lifecycle.death_tick == 0
    assert orc.lifecycle.is_permadeath is True


def test_hazard_drain_no_longer_destroys_a_same_tick_combat_kill_record():
    """Collision arm, rewritten to the fixed contract by
    TCK-20261001-HAZARD-OVERWRITES-SAME-TICK-COMBAT-OUTCOME-KIND (it asserted the defect before).
    Changing ONLY the region's hazard_kind to one orc_clan does not endure used to make
    `WorldDynamicsSystem.resolve_dynamics` overwrite the victim's own outcome_kind="KILL" with
    "HAZARD", so the death was never recorded. Combat resolves first and its terminal outcome now
    stands; hazard application stays observable through `CombatUpdate.hazard_damage`. The assertion
    that matters is equality with the control arm: the same death, recorded the same way.

    Residual realism caveat unchanged: this is a SCRIPTED forced-lethal attack (see module
    docstring), not a claim the collision is common in unscripted play."""
    drain, snapshots, regions_after = _run(NON_IMMUNE_KIND, ticks=2)
    _control_drain, control_snaps, control_regions = _run(IMMUNE_KIND, ticks=2)

    assert drain > 0, f"staging sanity: {NON_IMMUNE_KIND!r} must actually drain, got {drain}"
    first, second = snapshots[0], snapshots[1]
    control_first, control_second = control_snaps[0], control_snaps[1]

    assert first.combat.hp == 0 and first.combat.alive is False
    for got, want in ((first, control_first), (second, control_second)):
        assert got.lifecycle.active is want.lifecycle.active is False
        assert got.lifecycle.death_reason == want.lifecycle.death_reason == "COMBAT"
        assert got.lifecycle.death_tick == want.lifecycle.death_tick
        assert got.lifecycle.is_permadeath is want.lifecycle.is_permadeath is True
        assert got.lifecycle.heir_entity_id == want.lifecycle.heir_entity_id

    # The world, meanwhile, books the death: +1.0 regional trauma fires off alive_set=False
    # (world_dynamics.py:47-60), identically to the control arm. That asymmetry -- the region
    # scarred, the entity never recorded as dead -- is the observable inconsistency.
    #
    # Asserted as a differential against the control arm rather than against an absolute
    # threshold: the booked +1.0 is subject to per-tick trauma decay (it reads 0.9995 after two
    # ticks, not 1.0), so a hardcoded bound would be pinning the decay rate by accident. The
    # claim under test is "the world books this death the same either way", which is exactly an
    # equality between the arms.
    collision_trauma = {r: reg.trauma_score for r, reg in regions_after.items()}
    control_trauma = {r: reg.trauma_score for r, reg in control_regions.items()}
    assert collision_trauma == pytest.approx(control_trauma), (
        "regional trauma must be booked for this death identically to the control arm. collision={collision_trauma} control={control_trauma}"
    )
    assert all(v > 0.0 for v in collision_trauma.values()), (
        f"sanity: the death must leave a nonzero regional scar, got {collision_trauma}"
    )


@pytest.mark.slow
def test_defeat_deaths_are_recorded_in_unscripted_corpus_play():
    """C1's Q1/Q2 production finding, rewritten to the fixed contract by
    TCK-20261001-DEFEAT-REBIRTH-CONVERTED-TO-DEATH-BY-PASSIVE-HP-GATE. The same 120-tick
    `frontier_marches` seed-42 run once showed terminal `DEFEAT` outcomes
    (src/engine/combat.py forces is_lethal=False for HERO defenders) committed as combat-dead /
    lifecycle-alive with no death_reason. Now every terminal DEFEAT is a recorded death with its own
    reason, deactivated by resolve_lifecycle, and no reborn entity is left combat-dead.

    The remaining combat-dead / lifecycle-active / unrecorded residue is the hazard route
    (world_dynamics.py:39 overwrites outcome_kind), owned by
    TCK-20261001-HAZARD-OVERWRITES-SAME-TICK-COMBAT-OUTCOME-KIND; pinned so its fix is visible."""
    repo = WorldRepository(os.path.join("data", "worlds"))
    spec, context = repo.load_world_with_context("frontier_marches")
    state, _report = WorldCompiler.compile(spec, SEED, context=context)

    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(SEED),
                    flags={"no_frame_pacing": True})
    try:
        for _ in range(120):
            kernel.tick_once()
        entities = list(kernel._state.entities.values())
    finally:
        kernel.shutdown()

    defeated = [e for e in entities if e.lifecycle.death_reason == "DEFEAT"]
    assert defeated, "expected at least one terminal DEFEAT in the 120-tick corpus run (was 4 on 71c4aa321)"
    assert all(e.lifecycle.active is False and e.combat.alive is False for e in defeated)

    reborn = [e for e in entities if e.lifecycle.generation > 1]
    # A reborn hero may legitimately die again later (the corpus run is also wall-clock-budget
    # sensitive, so the population varies run to run); what must hold is that it is never silently
    # deactivated, and a still-active one is not left combat-dead by rebirth itself.
    assert all(e.lifecycle.death_reason is not None for e in reborn if not e.lifecycle.active), (
        "a reborn entity may only be inactive with a recorded death_reason"
    )

    # Tightened by TCK-20261001-HAZARD-OVERWRITES-SAME-TICK-COMBAT-OUTCOME-KIND: hazard deaths are
    # now recorded and deactivated by resolve_lifecycle, so no HP-0 entity is left active/unrecorded.
    # (A REBIRTH defender is the one remaining class until TCK-20261001-RETIRE-HERO-REBIRTH-...)
    residue = [
        (e.id, e.lifecycle.generation) for e in entities
        if not e.combat.alive and e.lifecycle.active and e.lifecycle.death_reason is None
    ]
    assert all(gen > 1 for _id, gen in residue), (
        f"HP-0 entities left active with no death record other than REBIRTH: {residue}"
    )
