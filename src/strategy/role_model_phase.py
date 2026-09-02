# Compliance IDs: STRAT-264
"""
src/strategy/role_model_phase.py
───────────────────────────────────────────────────────────────────────────────
RoleModelSelectionPhase (TCK-20260831-ROLE-MODEL-IMITATION)

Mirrors HabitBiasUpdatePhase.apply()'s (src/domains/emotion/habit_phase.py)
read-through-then-replace shape: reads entity_update.cognition_bundle_set,
falling back to entity.cognition, before replacing -- so a same-tick
cognition_bundle_set write staged by an earlier sequentially-threaded phase
(e.g. habit_bias_action_style) is preserved, not clobbered. Registered via
plain sequential run_phase() threading in pipeline.py, never via
StateUpdate.merge() -- see plan.md's "Merge-atomicity resolution" for why that
distinction matters for this phase's write pattern.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from dataclasses import replace

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate


class RoleModelSelectionPhase:
    """Authoritative per-tick (cadence-gated) writer for role-model watching/choosing."""

    RADIUS = 10.0  # matches SpatialQueryService.nearby_entities call convention elsewhere
                   # (src/systems/strategic_systems/intelligence.py:144)

    @staticmethod
    def apply(state: "AuthoritativeState", update: "StateUpdate") -> "StateUpdate":
        from src.core.updates import EntityUpdate
        from src.engine.cadence import should_run, SystemCadence
        from src.engine.spatial_query import SpatialQueryService
        from src.strategy.role_model_imitation import RoleModelImitationService

        cadence = SystemCadence().social_memory  # reuse existing tier, no new SystemCadence field
        entity_updates = dict(update.entity_updates)
        for entity_id, entity in state.entities.items():
            if not should_run(state.tick, entity_id, cadence):
                continue

            entity_update = entity_updates.get(entity_id, EntityUpdate(entity_id=entity_id))
            base_cognition = (
                entity_update.cognition_bundle_set
                if entity_update.cognition_bundle_set is not None
                else entity.cognition
            )
            current = base_cognition.role_model

            nearby_ids = SpatialQueryService.nearby_entities(
                state, entity.navigation.position, radius=RoleModelSelectionPhase.RADIUS
            )
            best_id, best_level = None, entity.identity.evolution_level
            for nid in sorted(nearby_ids):  # deterministic tie-break: lowest entity_id
                if nid == entity_id:
                    continue
                other = state.entities.get(nid)
                if other is None:
                    continue
                if other.identity.evolution_level > best_level:
                    best_id, best_level = nid, other.identity.evolution_level

            # Every cadence tick recomputes fresh -- no special "keep current unless a
            # strictly-better candidate exists" carve-out. If the previously-admired entity
            # is no longer present/no longer the best candidate, it is implicitly cleared.
            if best_id != current.admired_entity_id:
                new_role_model = replace(
                    current,
                    admired_entity_id=best_id,
                    admired_since_tick=state.tick,
                    last_reconsidered_tick=state.tick,
                    imitation_fidelity=RoleModelImitationService.compute_imitation_fidelity(entity),
                )
            else:
                new_role_model = replace(
                    current,
                    last_reconsidered_tick=state.tick,
                    imitation_fidelity=RoleModelImitationService.compute_imitation_fidelity(entity),
                )
            new_cognition = replace(base_cognition, role_model=new_role_model)
            entity_updates[entity_id] = replace(entity_update, cognition_bundle_set=new_cognition)

        return replace(update, entity_updates=entity_updates)
