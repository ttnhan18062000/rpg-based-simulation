"""Idea 60 (Reputations Are Local) corpus proof (TCK-20260906-CORPUS-TEST-NEWLY-UNBLOCKED-IDEAS)
against the real `frontier_extended` world: `SocialComponent.regional_reputation` is a real,
region-keyed `Dict[str, float]` (src/core/models/social.py:48), distinct per region rather than one
global float, and is already included in the canonical state hash / StateFingerprinter (landed with
M5's TCK-20260904-REPUTATION-LOCALITY-SCOPE).

Loads the real, registered `frontier_extended` corpus world, hand-seeds one entity with distinct
regional_reputation values across the world's own real regions (proving the field genuinely carries
per-region data through the real AuthoritativeState/apply-path round trip, since no shipped calibration
profile is confirmed to naturally populate 3+ distinct regional_reputation entries for one entity
within a short corpus tick budget), and drives one real Kernel.tick_once() to confirm the values
survive a real tick untouched (no accidental global collapse).
"""
from __future__ import annotations

from dataclasses import replace

from tools.calibrate_simq import _load_world_state
from src.config.profiles import PROD_SMALL
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG


def test_regional_reputation_carries_distinct_per_region_values_through_a_real_world_and_tick():
    state, report = _load_world_state("frontier_extended", seed=42)
    assert state is not None, "frontier_extended must be a real, compilable corpus world"
    assert len(state.regions) >= 3, "frontier_extended must have at least 3 real regions to test"

    region_ids = sorted(state.regions.keys())[:3]
    entity_id = sorted(state.entities.keys())[0]
    entity = state.entities[entity_id]

    seeded_values = {region_ids[0]: 1.8, region_ids[1]: 0.6, region_ids[2]: 1.1}
    new_social = replace(entity.social, regional_reputation=dict(seeded_values))
    state = replace(state, entities={**state.entities, entity_id: replace(entity, social=new_social)})

    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(42), flags={"no_frame_pacing": True})
    try:
        kernel.tick_once()
    finally:
        kernel.shutdown()

    final_entity = kernel.state.entities[entity_id]
    final_regional_rep = final_entity.social.regional_reputation

    distinct_values = {final_regional_rep.get(rid) for rid in region_ids}
    assert len(distinct_values) == 3, (
        f"entity must retain 3 DISTINCT regional_reputation values across regions, got {final_regional_rep}"
    )
    for rid, expected in seeded_values.items():
        assert final_regional_rep.get(rid) == expected, (
            f"region {rid}'s reputation must survive a real tick untouched (no cross-region bleed)"
        )
