# Compliance IDs: WORLD-122
# src/world/reproduction_humanoid.py
# TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE
from __future__ import annotations

from typing import TYPE_CHECKING, Set

from src.core.state import LifeStage
from src.core.updates import StateUpdate, EntityUpdate, LifecycleUpdate, WorldUpdate

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.systems.world_systems.generator import EntityGenerator


class HumanoidReproductionService:
    """
    Behind ENABLE_REPRODUCTION_HUMANOID_PATH, pairs existing ADULT/alive/active
    same-kind entities within HUMANOID_PAIRING_RADIUS and produces a tracked-parent
    birth via EntityGenerator.spawn_humanoid_offspring() -- unlike the parentless
    Natural-Creature/Magical-Demonic siblings, this path operates on existing entity
    pairs, not a per-camp/per-calamity spawn anchor.
    """

    HUMANOID_PAIRING_RADIUS = 10.0
    REPRODUCTION_COOLDOWN_TICKS = 400

    @staticmethod
    def process_reproduction(state: AuthoritativeState, generator: EntityGenerator) -> StateUpdate:
        from src.engine.spatial_query import SpatialQueryService
        from src.domains.demographics.cohort import compute_regional_scarcity
        from src.core.builder import build_parent_bond_updates_for_birth
        from src.systems.lifecycle_systems.genetics import GeneticsSystem

        candidates = sorted(
            (e for e in state.entities.values()
             if e.identity.life_stage == LifeStage.ADULT and e.combat.alive and e.lifecycle.active),
            key=lambda e: e.id,
        )
        by_id = {e.id: e for e in candidates}
        paired: Set[int] = set()
        result = StateUpdate()

        for a in candidates:
            if a.id in paired:
                continue

            nearby_ids = SpatialQueryService.nearby_entities(
                state, a.navigation.position, HumanoidReproductionService.HUMANOID_PAIRING_RADIUS,
            )
            b = None
            for b_id in sorted(nearby_ids):
                if b_id == a.id or b_id in paired:
                    continue
                candidate_b = by_id.get(b_id)
                if candidate_b is None or candidate_b.kind != a.kind:
                    continue
                if a.lifecycle.reproduction_cooldowns.get(b_id, 0) > state.tick:
                    continue
                if candidate_b.lifecycle.reproduction_cooldowns.get(a.id, 0) > state.tick:
                    continue
                b = candidate_b
                break
            if b is None:
                continue

            region = SpatialQueryService.get_region_at(state, a.navigation.position)
            if region is not None and region.population_cohorts:
                young = region.population_cohorts.get("young")
                threshold = young.migration_threshold if young is not None else 0.7
                if compute_regional_scarcity(region.id, state) > threshold:
                    continue

            paired.add(a.id)
            paired.add(b.id)

            # birth_record()'s internal combine_profiles() call only fires when at least one
            # parent profile is non-None (src/core/builder.py); first-generation parents have no
            # genetic_profile of their own (Risk #5), so this resolves both parents to a
            # concrete profile here -- via the same GeneticsSystem.generate_profile_from_seed()
            # fallback birth_record() itself would use per-parent -- rather than ever passing
            # None/None through, which would silently skip genetics combination for every
            # first-generation pairing.
            a_profile = a.lifecycle.genetic_profile or GeneticsSystem.generate_profile_from_seed(a.id)
            b_profile = b.lifecycle.genetic_profile or GeneticsSystem.generate_profile_from_seed(b.id)

            child = generator.spawn_humanoid_offspring(
                a.navigation.position, state, a.kind,
                a.id, b.id, state.tick, None,
                a_profile, b_profile,
                a.identity.role, b.identity.role,
            )

            expiry = state.tick + HumanoidReproductionService.REPRODUCTION_COOLDOWN_TICKS
            # TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE: coarse +1 nudge; no local
            # accumulation needed since result.merge(pair_update) below already sums
            # population_young_births_delta additively across pairs via WorldUpdate.merge().
            world_updates = {region.id: WorldUpdate(region_id=region.id, population_young_births_delta=1)} if region is not None else {}
            pair_update = StateUpdate(
                entities_add=[child],
                entity_updates={
                    a.id: EntityUpdate(entity_id=a.id, lifecycle=LifecycleUpdate(reproduction_cooldowns_add={b.id: expiry})),
                    b.id: EntityUpdate(entity_id=b.id, lifecycle=LifecycleUpdate(reproduction_cooldowns_add={a.id: expiry})),
                },
                world_updates=world_updates,
            )
            bond_update = StateUpdate(
                entity_updates={
                    u.entity_id: u
                    for u in build_parent_bond_updates_for_birth([a.id, b.id], child.id, state.tick)
                },
            )
            result = result.merge(pair_update).merge(bond_update)

        return result
