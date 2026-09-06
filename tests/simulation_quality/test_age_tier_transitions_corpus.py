"""Unit-tier SimQ corpus proof (TCK-20260906-AGE-TIER-TIMING-BUG-AND-CORPUS-TEST) that idea 20
(life-stage transitions) and idea 34 (Coming of Age) are observable at the REAL fantasy-year-scaled
age-bracket thresholds (TCK-20260904-TEMPORAL-FANTASY-YEAR-AGING-MIGRATION: 3,456,000 ticks
young->adult, 17,280,000 ticks adult->elder) through a real Kernel.tick_once() run.

Synthetic content is intentional and idiomatic here (corpus_tier_taxonomy.md's Unit tier explicitly
allows it) -- this proves the wiring works at the real thresholds via a small, hand-seeded,
deterministic scenario, rather than an emergent multi-million-tick corpus run (confirmed impractical
in investigation.md). Does not duplicate tests/unit/progression/test_lifecycle.py or
tests/unit/strategic/test_coming_of_age_archetype_choice.py's own pure-function/isolated-call
coverage -- this is the SimQ-corpus-framed angle (both transitions, both mechanics, in one scenario,
driven end-to-end through Kernel.tick_once()), the actual gap this ticket closes.

There is no `archetype_locked` field anywhere in real code (confirmed via grep) -- idea 34's real,
observable mechanism is a one-shot `role_set` at the CHILD->ADULT transition
(src/ai/coming_of_age.py::choose_archetype(), src/systems/lifecycle_systems/lifecycle.py), asserted
on directly below.
"""
from __future__ import annotations

from src.config.profiles import PROD_SMALL
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.state import AuthoritativeState, LifeStage
from src.domains.demographics.cohort import ADULT_ELDER_BOUNDARY_TICKS, YOUNG_ADULT_BOUNDARY_TICKS
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG


def _child_about_to_come_of_age(entity_id: int) -> "EntityState":
    # parent_a/b_entity_id set so is_excluded_no_birth_record() is False -- required for the
    # Coming-of-Age roll to fire, matching every real CHILD-construction path in the codebase.
    return (
        V2EntityBuilder(entity_id)
        .kind("citizen")
        .location(0.0, 0.0)
        .identity(role=EntityRole.CITIZEN, faction=Faction.TOWN_COUNCIL, life_stage=LifeStage.CHILD)
        .lifecycle(
            age_ticks=YOUNG_ADULT_BOUNDARY_TICKS,
            max_age_ticks=99_999_999,
            parent_a_entity_id=1001,
            parent_b_entity_id=1002,
            birth_tick=1,
        )
        .build()
    )


def _adult_about_to_become_elder(entity_id: int) -> "EntityState":
    return (
        V2EntityBuilder(entity_id)
        .kind("citizen")
        .location(5.0, 5.0)
        .identity(role=EntityRole.CITIZEN, faction=Faction.TOWN_COUNCIL, life_stage=LifeStage.ADULT)
        .lifecycle(age_ticks=ADULT_ELDER_BOUNDARY_TICKS, max_age_ticks=99_999_999)
        .build()
    )


def test_young_adult_transition_and_coming_of_age_fire_at_real_threshold():
    child = _child_about_to_come_of_age(1)
    state = AuthoritativeState(tick=0, seed=42, entities={1: child})

    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(42), flags={"no_frame_pacing": True})
    try:
        kernel.tick_once()
    finally:
        kernel.shutdown()

    final = kernel.state.entities[1]

    assert final.identity.life_stage == LifeStage.ADULT, (
        "identity.life_stage must flip CHILD->ADULT at the real 3,456,000-tick young->adult boundary"
    )
    # Coming of Age fires a one-shot occupation roll over _CANDIDATE_ROLES = (SHOPKEEPER, WORKER,
    # GUARD) -- CITIZEN is never a candidate, so a real fire must move the role away from CITIZEN.
    # This is the real, observable proxy for "archetype_locked" (that field does not exist
    # anywhere in real code) -- a regression-catching assertion, not a tautology.
    assert final.identity.role != EntityRole.CITIZEN, (
        "Coming of Age roll must move role off CITIZEN at the young->adult transition"
    )
    assert final.identity.role in (EntityRole.SHOPKEEPER, EntityRole.WORKER, EntityRole.GUARD), (
        f"unexpected post-Coming-of-Age role: {final.identity.role}"
    )


def test_adult_elder_transition_and_elder_attribute_deltas_fire_at_real_threshold():
    adult = _adult_about_to_become_elder(2)
    state = AuthoritativeState(tick=0, seed=42, entities={2: adult})
    pre_strength = adult.attributes.strength
    pre_agility = adult.attributes.agility

    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(42), flags={"no_frame_pacing": True})
    try:
        kernel.tick_once()
    finally:
        kernel.shutdown()

    final = kernel.state.entities[2]

    assert final.identity.life_stage == LifeStage.ELDER, (
        "identity.life_stage must flip ADULT->ELDER at the real 17,280,000-tick adult->elder boundary"
    )
    assert final.attributes.strength < pre_strength, "elder attribute penalty must reduce strength"
    assert final.attributes.agility < pre_agility, "elder attribute penalty must reduce agility"
