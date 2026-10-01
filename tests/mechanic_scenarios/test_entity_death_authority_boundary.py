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


def test_hazard_drain_destroys_a_same_tick_combat_kill_record():
    """Collision arm, and C1's Q2/Q3 finding. Changing ONLY the region's hazard_kind to one
    orc_clan does not endure makes `WorldDynamicsSystem.resolve_dynamics`
    (src/engine/world_dynamics.py:39) unconditionally overwrite the victim's own
    outcome_kind="KILL" with "HAZARD" -- it runs at pipeline.py:348, between the phase that writes
    KILL (:297/:320) and the phase that reads it (:414). `resolve_lifecycle` only deactivates on
    outcome_kind in ("KILL","PERMADEATH") (src/systems/lifecycle_systems/lifecycle.py:202), so the
    death is never recorded: no death_reason, no death_tick, no is_permadeath, and therefore no
    succession/heirloom/lineage dispatch. The entity is deactivated a tick LATE by apply.py:109's
    passive HP gate, still with no recorded cause.

    Asserts the defective behaviour deliberately. See module docstring."""
    drain, snapshots, regions_after = _run(NON_IMMUNE_KIND, ticks=2)

    assert drain > 0, (
        f"staging sanity: {NON_IMMUNE_KIND!r} must actually drain, got {drain}"
    )
    first, second = snapshots[0], snapshots[1]

    # The combat half really did land: HP is gone and combat considers the entity dead.
    assert first.combat.hp == 0
    assert first.combat.alive is False

    # ...but lifecycle books no death at all, and still does not a tick later.
    assert first.lifecycle.active is True, (
        "C1 finding: the victim of a same-tick combat kill + hazard drain is NOT deactivated on "
        f"the kill tick, got active={first.lifecycle.active}"
    )
    assert first.lifecycle.death_reason is None
    assert second.lifecycle.active is False, (
        "the late deactivation comes from apply.py:109's passive HP gate on the following tick"
    )
    assert second.lifecycle.death_reason is None, (
        "C1 finding: the combat death record is destroyed outright -- death_reason stays None "
        f"even after deactivation, got {second.lifecycle.death_reason!r}"
    )
    assert second.lifecycle.death_tick is None
    assert second.lifecycle.is_permadeath is False

    # The world, meanwhile, books the death: +1.0 regional trauma fires off alive_set=False
    # (world_dynamics.py:47-60), identically to the control arm. That asymmetry -- the region
    # scarred, the entity never recorded as dead -- is the observable inconsistency.
    #
    # Asserted as a differential against the control arm rather than against an absolute
    # threshold: the booked +1.0 is subject to per-tick trauma decay (it reads 0.9995 after two
    # ticks, not 1.0), so a hardcoded bound would be pinning the decay rate by accident. The
    # claim under test is "the world books this death the same either way", which is exactly an
    # equality between the arms.
    _control_drain, _control_snaps, control_regions = _run(IMMUNE_KIND, ticks=2)
    collision_trauma = {r: reg.trauma_score for r, reg in regions_after.items()}
    control_trauma = {r: reg.trauma_score for r, reg in control_regions.items()}
    assert collision_trauma == pytest.approx(control_trauma), (
        "regional trauma must be booked for this death identically to the recorded-death control "
        "arm -- that is what makes lifecycle's silence an inconsistency rather than a consistent "
        f"'no death happened'. collision={collision_trauma} control={control_trauma}"
    )
    assert all(v > 0.0 for v in collision_trauma.values()), (
        f"sanity: the death must leave a nonzero regional scar, got {collision_trauma}"
    )


@pytest.mark.slow
def test_unrecorded_deaths_occur_in_unscripted_corpus_play():
    """C1's Q1/Q2 production finding, unscripted: the committed signature
    `combat.alive=False` AND `lifecycle.active=True` AND `death_reason=None` is reached in an
    unmodified corpus world within 120 ticks, by routes that need no combat KILL at all --
    hazard-only drain deaths, and `DEFEAT` outcomes (src/engine/combat.py:136 forces
    is_lethal=False for EntityRole.HERO defenders, so a lethal blow on a HERO yields DEFEAT with
    alive_set=False, which resolve_lifecycle ignores).

    This is the evidence that the defect's consequence is routine even though the specific
    combat+hazard collision is rare. Asserts the defective behaviour deliberately."""
    repo = WorldRepository(os.path.join("data", "worlds"))
    spec, context = repo.load_world_with_context("frontier_marches")
    state, _report = WorldCompiler.compile(spec, SEED, context=context)

    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(SEED),
                    flags={"no_frame_pacing": True})
    unrecorded = []
    try:
        for i in range(120):
            kernel.tick_once()
            for e_id, e in kernel._state.entities.items():
                if (e.combat and not e.combat.alive
                        and e.lifecycle and e.lifecycle.active
                        and e.lifecycle.death_reason is None):
                    unrecorded.append((i, e_id))
    finally:
        kernel.shutdown()

    assert unrecorded, (
        "C1 finding: expected at least one entity committed as combat-dead but lifecycle-alive "
        "with no death_reason in 120 unscripted ticks of frontier_marches. If this stops "
        "reproducing, the routed fix may have landed -- rewrite this test to the fixed contract "
        "rather than deleting it."
    )
