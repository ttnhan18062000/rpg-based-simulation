from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Dict

from src_v2.core.state import AuthoritativeState, EntityState

if TYPE_CHECKING:
    from src_v2.core.updates import StateUpdate, EntityUpdate


class ApplyPath:
    """
    The singular authority for state transitions.
    Milestone A Law: apply_generation is the ONLY entry point for AuthoritativeState mutation.
    Implements generation-based state application (immutable transitions).
    """

    @staticmethod
    def apply_generation(
        prior_state: AuthoritativeState,
        update: StateUpdate,
        next_tick: int,
        next_world_time: int
    ) -> AuthoritativeState:
        """
        Produce a new state generation from the prior state and updates.
        Invariant: All input collections MUST be sorted before application.
        """
        # 1. Update entities
        new_entities = dict(prior_state.entities)
        
        # Explicitly sort entity IDs to ensure deterministic apply order
        sorted_entity_ids = sorted(update.entity_updates.keys())
        
        for e_id in sorted_entity_ids:
            ent_upd = update.entity_updates[e_id]
            if e_id in new_entities:
                new_entities[e_id] = ApplyPath._apply_entity_update(
                    new_entities[e_id], ent_upd
                )
        
        # 2. Update global resources
        new_resources = dict(prior_state.global_resources)
        sorted_resource_keys = sorted(update.resource_updates.keys())
        for r_key in sorted_resource_keys:
            delta = update.resource_updates[r_key]
            new_resources[r_key] = new_resources.get(r_key, 0.0) + delta
            
        # 3. Update periodic due ticks
        new_periodic = dict(prior_state.periodic_due_ticks)
        sorted_periodic_keys = sorted(update.periodic_updates.keys())
        for p_key in sorted_periodic_keys:
            new_periodic[p_key] = update.periodic_updates[p_key]
            
        # 4. Update work debt
        new_debt = dict(prior_state.work_debt)
        sorted_debt_keys = sorted(update.work_debt_updates.keys())
        for d_key in sorted_debt_keys:
            delta = update.work_debt_updates[d_key]
            # M4 Law: Debt should be clamped to absolute zero
            new_debt[d_key] = max(0, new_debt.get(d_key, 0) + delta)
            
        # 5. Create new generation
        return replace(
            prior_state,
            tick=next_tick,
            world_time=next_world_time,
            entities=new_entities,
            global_resources=new_resources,
            periodic_due_ticks=new_periodic,
            work_debt=new_debt,
            rng_checkpoint=update.rng_checkpoint or prior_state.rng_checkpoint
        )

    @staticmethod
    def _apply_entity_update(entity: EntityState, update: EntityUpdate) -> EntityState:
        """
        Apply updates to a single entity, producing a new EntityState instance.
        Law: This MUST produce a new instance to ensure prior-generation purity.
        """
        # Shallow clone of properties to prevent immediate aliasing.
        # Deep nesting in properties is highly discouraged in Milestone A baseline.
        # We use dict() which is sufficient for non-nested properties.
        new_properties = dict(entity.properties)
        if update.property_updates:
            new_properties.update(update.property_updates)
        
        return replace(
            entity,
            position=update.new_position if update.new_position is not None else entity.position,
            readiness=entity.readiness + update.readiness_delta,
            active=update.active if update.active is not None else entity.active,
            properties=new_properties
        )
