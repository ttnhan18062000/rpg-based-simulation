"""Idea 65 (Named Refugee Threads) corpus proof (TCK-20260906-CORPUS-TEST-NEWLY-UNBLOCKED-IDEAS)
against the real `crowded_frontier` world: a region driven to/above `DisplacementService.
DISPLACEMENT_THRESHOLD` (0.6, src/world/displacement.py) pushes its living population to a safer
neighbor through the real `src/engine/world_dynamics.py` pipeline call, carrying
`StrategicComponent.home_region_id` forward as the *original* (fled-from) region.

Loads the real, registered `crowded_frontier` corpus world, then sets one region's
`calamity_intensity` directly (a controlled, disclosed variant of a real loaded world — the real
tick-by-tick calamity-growth path is a separate, already-tested mechanism; this test targets
DisplacementService's own consequence step specifically) and drives one real `Kernel.tick_once()`.
"""
from __future__ import annotations

from dataclasses import replace

from tools.calibrate_simq import _load_world_state
from src.config.profiles import PROD_SMALL
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.world.displacement import DisplacementService


def test_displaced_entity_retains_fled_from_region_as_home():
    state, report = _load_world_state("crowded_frontier", seed=42)
    assert state is not None, "crowded_frontier must be a real, compilable corpus world"

    struck_region_id = sorted(state.regions.keys())[0]
    struck_region = state.regions[struck_region_id]
    state = replace(
        state,
        regions={
            **state.regions,
            struck_region_id: replace(
                struck_region, calamity_intensity=DisplacementService.DISPLACEMENT_THRESHOLD
            ),
        },
    )

    from src.engine.legality import LegalityServiceV2

    resident_ids = sorted(
        eid for eid, ent in state.entities.items()
        if ent.lifecycle.active and ent.combat.alive
        and LegalityServiceV2.get_region_for_position(ent.navigation.position, state) is state.regions[struck_region_id]
        and ent.strategic.home_region_id is None
    )
    assert resident_ids, "crowded_frontier must have at least one living, home-unset resident in the struck region"
    resident_id = resident_ids[0]

    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(42), flags={"no_frame_pacing": True})
    try:
        kernel.tick_once()
    finally:
        kernel.shutdown()

    final_resident = kernel.state.entities[resident_id]
    assert final_resident.strategic.home_region_id == struck_region_id, (
        "displaced entity's home_region_id must be set to the fled-FROM region, not the new one"
    )

    from src.engine.legality import LegalityServiceV2 as LSV2
    final_region = LSV2.get_region_for_position(final_resident.navigation.position, kernel.state)
    assert final_region is not None and final_region.id != struck_region_id, (
        "entity must actually have relocated out of the struck region this tick"
    )
