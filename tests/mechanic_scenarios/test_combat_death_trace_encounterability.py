"""Regression-pinning tests for TCK-20260928-COMBAT-DEATH-TRACE-SITUATED-ENCOUNTERABILITY.

This is an assessment/observation ticket, not a code fix -- these two tests pin the ticket's own
empirical findings into the test suite so they cannot silently regress or need to be re-derived
from scratch later. Both reuse `mechanic_scenario_combat_judgement_withdrawal` (goblin id 1 vs orc
id 2), the same real, catalog-authored hostile pair `test_combat_attributes_real_fight_outcome_
value_differential.py` already uses for this exact "does a combat death actually happen" question.

**Anti-drift caveat, load-bearing, not flavor text**: both tests below dispatch a SCRIPTED,
forced-lethal ATTACK through a real `Kernel.tick_once()` -- proof the dispatch-routing mechanism
works, not a claim that combat deaths are common in unscripted corpus play.
`registries/mechanisms.yaml`'s own `tactical_decision` entry (`verified: corpus_run, verdict:
contradicted`, dated 2026-09-19) independently establishes real unscripted `ATTACK` dispatch is
rare: 0-2 real `CombatResolutionSystem.resolve_attack()` calls per 1000-2000 ticks across three
real corpus worlds. Both facts are true and recorded separately; do not read either test below as
evidence combat deaths are routine.
"""
from __future__ import annotations

import os
from dataclasses import replace

from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository
from src.engine.kernel import Kernel
from src.config.profiles import PROD_SMALL
from src.platform.rng import DeterministicRNG
from src.core.state import TaskComponent
from src.core.builder import V2EntityBuilder
from src.core.social_constants import ALLY_TRUST_THRESHOLD

WORLD_ID = "mechanic_scenario_combat_judgement_withdrawal"
GOBLIN_ID = 1
ORC_ID = 2
BONDED_ALLY_ID = 3
UNRELATED_BYSTANDER_ID = 4
SEED = 42


def _compile_world():
    repo = WorldRepository(os.path.join("data", "worlds"))
    spec, context = repo.load_world_with_context(WORLD_ID)
    state, _report = WorldCompiler.compile(spec, SEED, context=context)
    return state


def _force_lethal_attack(state):
    """Stages the goblin-attacks-orc lethal dispatch shared by both tests below."""
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
    new_entities = dict(state.entities)
    new_entities[GOBLIN_ID] = goblin
    new_entities[ORC_ID] = orc
    object.__setattr__(state, "entities", new_entities)
    return state


def test_forced_combat_kill_produces_combat_death_reason_in_one_tick():
    """Pins Q1's empirical finding (investigation.md): a real, deterministic, forced-lethal
    ATTACK dispatched through Kernel.tick_once() against mechanic_scenario_combat_judgement_
    withdrawal produces entity.lifecycle.active is False and entity.lifecycle.death_reason ==
    "COMBAT" in the same tick, through the real CombatResolutionSystem.resolve_attack() ->
    LifecycleSystem.resolve_lifecycle() routing (src/systems/lifecycle_systems/lifecycle.py:
    202-217). Catches a future regression in that routing. See module docstring for the
    scripted-vs-unscripted caveat -- this is a dispatch-routing correctness pin, not a
    corpus-frequency claim.
    """
    state = _force_lethal_attack(_compile_world())

    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(SEED), flags={"no_frame_pacing": True})
    try:
        kernel.tick_once()
        final_state = kernel._state
    finally:
        kernel.shutdown()

    orc_after = final_state.entities[ORC_ID]
    assert orc_after.lifecycle.active is False, (
        f"expected the orc to be deactivated after a forced lethal attack in one tick, but "
        f"lifecycle.active={orc_after.lifecycle.active}."
    )
    assert orc_after.lifecycle.death_reason == "COMBAT", (
        f"expected death_reason=='COMBAT' for a real forced combat kill, got "
        f"{orc_after.lifecycle.death_reason!r}."
    )


def test_grief_trigger_is_the_only_real_trace_a_bonded_observer_receives_on_combat_death():
    """Pins Answer 2/Answer 3's own separation (investigation.md) in code: the grief trigger
    (src/observability/event_extractor.py:1722-1762) is the ONE real trace any runtime consumer
    legitimately receives from a combat death, and only for a BONDED observer
    (social.trust_history[dead_id] >= ALLY_TRUST_THRESHOLD) -- never for a co-located-but-
    unbonded observer, since the path has zero proximity/perception check. If a future change
    makes the grief trigger proximity-gated, or makes some other path newly perception-routed,
    this test fails loudly instead of the distinction silently eroding (test_plan.md's own
    framing for this test).
    """
    state = _force_lethal_attack(_compile_world())

    bonded_ally = (
        V2EntityBuilder(BONDED_ALLY_ID)
        .kind("hero")
        .location(2.8, 2.8)  # far corner of the arena's own [0,0,3,3] grid_bounds -- not co-located
        .social(trust_history={ORC_ID: 0.9})
        .build()
    )
    assert 0.9 >= ALLY_TRUST_THRESHOLD, "sanity check: the staged trust value must clear the real threshold"

    unrelated_bystander = (
        V2EntityBuilder(UNRELATED_BYSTANDER_ID)
        .kind("hero")
        .location(1.2, 0.1)  # adjacent to the orc -- co-located, but carries no bond
        .build()
    )

    new_entities = dict(state.entities)
    new_entities[BONDED_ALLY_ID] = bonded_ally
    new_entities[UNRELATED_BYSTANDER_ID] = unrelated_bystander
    object.__setattr__(state, "entities", new_entities)

    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(SEED), flags={"no_frame_pacing": True})
    try:
        # Tick 1: the orc dies; the grief trigger is detected and queued (not yet applied), per
        # the same detect-then-drain-next-tick sequencing test_mid_episode_grief_trigger.py pins.
        kernel.tick_once()

        died = kernel.state.entities[ORC_ID]
        assert died.lifecycle.active is False and died.lifecycle.death_reason == "COMBAT", (
            "scenario reach check: the orc must actually die in combat this tick for the grief "
            "trigger to have anything to detect."
        )

        expected_urgency = round(min(1.0, 0.9 * 0.8), 6)
        assert (BONDED_ALLY_ID, ORC_ID, expected_urgency) in kernel._pending_grief_triggers, (
            "the grief trigger must fire for the bonded (trust >= ALLY_TRUST_THRESHOLD) observer "
            "even though it is NOT co-located with the death -- Answer 3's location-independence "
            "finding."
        )
        assert not any(
            trigger[0] == UNRELATED_BYSTANDER_ID for trigger in kernel._pending_grief_triggers
        ), (
            "the grief trigger must NOT fire for the unrelated, unbonded observer even though it "
            "IS co-located/adjacent to the death -- pinning that this path is trust-keyed, never a "
            "proximity/perception channel."
        )

        # Clear the goblin's now-stale forced ATTACK task before the drain tick -- its target is
        # already dead, and post-death re-targeting is not what this test exercises.
        current_state = kernel.state
        drained_entities = dict(current_state.entities)
        drained_entities[GOBLIN_ID] = replace(drained_entities[GOBLIN_ID], task=TaskComponent())
        object.__setattr__(current_state, "entities", drained_entities)

        # Tick 2: _phase_resolution drains the queue and applies via StrategicPatch/ApplyPath --
        # the real authoritative write, not a developer-only observability artifact.
        kernel.tick_once()

        concern_id = f"grief_ally_{ORC_ID}"
        bonded_concerns = kernel.state.entities[BONDED_ALLY_ID].strategic.concerns
        unrelated_concerns = kernel.state.entities[UNRELATED_BYSTANDER_ID].strategic.concerns

        assert concern_id in bonded_concerns, (
            "the bonded observer's strategic.concerns must gain the real ConcernState -- the one "
            "legitimate encounterable trace of this combat death (Answer 3)."
        )
        assert concern_id not in unrelated_concerns, (
            "the unrelated, co-located observer must receive nothing -- confirming the grief "
            "trigger is bonded-only, not a co-located/perception channel."
        )
    finally:
        kernel.shutdown()
