"""
src/world/displacement.py
───────────────────────────────────────────────────────────────────────────────
DisplacementService (idea 65, "Named Refugee Threads"): when a region's
calamity_intensity crosses a threshold, living entities positioned there are
relocated to their lowest-calamity_intensity adjacent region -- carrying their
StrategicComponent.home_region_id forward as their *original* home (idea 59)
if they didn't already have one, never overwriting an existing value.

This is a pure function: reads AuthoritativeState, returns a StateUpdate. All
durable writes go through the authoritative apply-path (EntityUpdate.new_position,
StrategicUpdate.home_region_id_set) -- this module never mutates state directly.
"""
from __future__ import annotations
from typing import Dict, List, Optional

from src.core.state import AuthoritativeState, RegionState
from src.core.updates import StateUpdate, EntityUpdate, StrategicUpdate


class DisplacementService:
    """Calamity-driven displacement: a region in crisis pushes its living population
    toward the nearest safer neighbor, and (if unset) records that region as each
    displaced entity's home -- distinct from idea 39's faction-mutation trigger and
    idea 56's loyalty-drift signal, which are unrelated social/political mechanisms."""

    # One tier above CalamityService.apply_calamity_consequences()'s own hazard_level > 0.5
    # threshold -- that threshold gates calamity_intensity *growth*, this one gates its
    # *consequence* (displacement), deliberately distinct events on the same underlying signal.
    DISPLACEMENT_THRESHOLD: float = 0.6

    @staticmethod
    def compute_displacement(state: AuthoritativeState) -> StateUpdate:
        from src.engine.legality import LegalityServiceV2

        struck_regions = sorted(
            (r for r in state.regions.values()
             if r.calamity_intensity >= DisplacementService.DISPLACEMENT_THRESHOLD),
            key=lambda r: r.id,
        )
        if not struck_regions:
            return StateUpdate()

        entity_updates: Dict[int, EntityUpdate] = {}
        for region in struck_regions:
            safe_region = DisplacementService._find_safe_neighbor(region, state)
            if safe_region is None:
                continue

            affected = sorted(
                (
                    entity for entity in state.entities.values()
                    if entity.lifecycle.active and entity.combat.alive
                    and LegalityServiceV2.get_region_for_position(entity.navigation.position, state) is region
                ),
                key=lambda entity: entity.id,
            )
            for entity in affected:
                strategic_update = (
                    StrategicUpdate(home_region_id_set=region.id)
                    if entity.strategic.home_region_id is None else None
                )
                entity_updates[entity.id] = EntityUpdate(
                    entity_id=entity.id,
                    new_position=safe_region.center,
                    strategic=strategic_update,
                )

        return StateUpdate(entity_updates=entity_updates)

    @staticmethod
    def _find_safe_neighbor(region: RegionState, state: AuthoritativeState) -> Optional[RegionState]:
        """Lowest-calamity_intensity region adjacent to `region`; ties broken by region id.
        Reuses RegionalPressureModel's own adjacency test read-only -- never mutates it."""
        from src.domains.world_emergence.models import RegionalPressureModel

        neighbors: List[RegionState] = sorted(
            (
                candidate for candidate in state.regions.values()
                if candidate.id != region.id
                and RegionalPressureModel._are_adjacent(region, candidate)
            ),
            key=lambda candidate: (candidate.calamity_intensity, candidate.id),
        )
        return neighbors[0] if neighbors else None
