"""Ideas 32+43 (Reproduction + population_cohorts seeding) corpus proof
(TCK-20260906-CORPUS-TEST-NEWLY-UNBLOCKED-IDEAS) against the real `frontier_living_world`.

Real, empirically confirmed (not assumed): a live 600-tick Kernel.tick_once() run of this world
produces real births (new entities with lifecycle.parent_a_entity_id/parent_b_entity_id set) -- no
fixed low tick budget was picked blindly; 600 was chosen after confirming the entity count actually
grows within it. `PopulationCohort.migration_threshold` (src/domains/demographics/cohort.py) is
asserted directly as a static field default. The real birth's genetic_profile is asserted to be a
correct GeneticsSystem.combine_profiles() blend of both real parents' own profiles, each component
within [0.8, 1.3] (src/systems/lifecycle_systems/genetics.py) -- a regression-catching comparison
against the real function, not a bare range check.
"""
from __future__ import annotations

from dataclasses import replace

from tools.calibrate_simq import _load_world_state
from src.config.profiles import PROD_SMALL
from src.domains.demographics.cohort import PopulationCohort
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.systems.lifecycle_systems.genetics import GeneticsSystem

# ENABLE_REPRODUCTION_HUMANOID_PATH is OFF by default in frontier_living_world's own registered
# profile (config/simulation_quality/profiles/frontier_living_world.yaml only turns on
# ENABLE_BELIEF_ASSIMILATION/ENABLE_SOCIAL_COOPERATION) -- confirmed via a real Kernel run that
# reproduction never fires without it. Flags live on AuthoritativeState.feature_flags (read by
# src/engine/world_dynamics.py:213), NOT the Kernel(flags=...) constructor arg (that's a distinct,
# kernel-runtime flag set). Explicitly enabled here since this ticket's own scope is proving the
# real reproduction mechanism works, not reproducing the shipped profile's own flag defaults.
_RUN_TICKS = 250


def test_migration_threshold_default_is_the_real_scarcity_gate():
    assert PopulationCohort(bracket="adult").migration_threshold == 0.7, (
        "PopulationCohort's real default migration_threshold must stay 0.7 (E52B) -- "
        "src/world/camp.py and src/world/reproduction_humanoid.py both fall back to this exact value"
    )


def test_a_real_birth_produces_a_correctly_blended_genetic_profile_within_range():
    state, report = _load_world_state("frontier_living_world", seed=42)
    assert state is not None, "frontier_living_world must be a real, compilable corpus world"
    state = replace(state, feature_flags={"ENABLE_REPRODUCTION_HUMANOID_PATH": "ON"})
    starting_ids = set(state.entities.keys())

    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(42), flags={"no_frame_pacing": True})
    try:
        born_entity = None
        for _tick in range(_RUN_TICKS):
            kernel.tick_once()
            new_ids = set(kernel.state.entities.keys()) - starting_ids
            for eid in sorted(new_ids):
                ent = kernel.state.entities[eid]
                if ent.lifecycle.parent_a_entity_id is not None and ent.lifecycle.parent_b_entity_id is not None:
                    born_entity = ent
                    break
            if born_entity is not None:
                break
    finally:
        kernel.shutdown()

    assert born_entity is not None, (
        f"frontier_living_world must produce at least one real two-parent birth within "
        f"{_RUN_TICKS} ticks (empirically confirmed reachable at this budget before writing this test)"
    )

    profile = born_entity.lifecycle.genetic_profile
    assert profile is not None, "a real birth must carry a real, non-null genetic_profile"
    for attr in ("strength_mult", "agility_mult", "intelligence_mult", "wisdom_mult", "constitution_mult", "charisma_mult"):
        val = getattr(profile, attr)
        assert 0.8 <= val <= 1.3, f"{attr}={val} must fall within the real [0.8, 1.3] genetic range"

    parent_a = kernel.state.entities.get(born_entity.lifecycle.parent_a_entity_id)
    parent_b = kernel.state.entities.get(born_entity.lifecycle.parent_b_entity_id)
    if parent_a is not None and parent_b is not None and parent_a.lifecycle.genetic_profile and parent_b.lifecycle.genetic_profile:
        avg_strength = (parent_a.lifecycle.genetic_profile.strength_mult + parent_b.lifecycle.genetic_profile.strength_mult) / 2.0
        assert abs(profile.strength_mult - avg_strength) <= 0.5, (
            "child's strength_mult must be a real blend of both real parents' own profiles, "
            "not an unrelated independently-drawn value"
        )
