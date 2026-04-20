from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Dict

from src_v2.core.state import AuthoritativeState, EntityState

if TYPE_CHECKING:
    from src_v2.core.updates import StateUpdate, EntityUpdate


class ApplyPath:
    """
    The singular authority for state transitions.
    Status: FROZEN (Resource Phase 4 Milestone 1)
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
        Status: FROZEN (Resource Phase 4 Milestone 1)
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
        
        # 2. Update resource nodes
        new_nodes = dict(prior_state.resource_nodes)
        sorted_node_ids = sorted(update.node_updates.keys())
        for n_id in sorted_node_ids:
            node_upd = update.node_updates[n_id]
            if n_id in new_nodes:
                node = new_nodes[n_id]
                new_nodes[n_id] = replace(
                    node,
                    remaining_charges=max(0, node.remaining_charges + node_upd.charges_delta),
                    cooldown_remaining=node_upd.cooldown_set if node_upd.cooldown_set is not None else node.cooldown_remaining
                )

        # 3. Update global resources
        new_resources = dict(prior_state.global_resources)
        sorted_resource_keys = sorted(update.resource_updates.keys())
        for r_key in sorted_resource_keys:
            delta = update.resource_updates[r_key]
            new_resources[r_key] = new_resources.get(r_key, 0.0) + delta
            
        # 4. Update periodic due ticks
        new_periodic = dict(prior_state.periodic_due_ticks)
        sorted_periodic_keys = sorted(update.periodic_updates.keys())
        for p_key in sorted_periodic_keys:
            new_periodic[p_key] = update.periodic_updates[p_key]
            
        # 5. Update work debt
        new_debt = dict(prior_state.work_debt)
        sorted_debt_keys = sorted(update.work_debt_updates.keys())
        for d_key in sorted_debt_keys:
            delta = update.work_debt_updates[d_key]
            # M4 Law: Debt should be clamped to absolute zero
            new_debt[d_key] = max(0, new_debt.get(d_key, 0) + delta)
            
        # 6. Create new generation
        return replace(
            prior_state,
            tick=next_tick,
            world_time=next_world_time,
            entities=new_entities,
            resource_nodes=new_nodes,
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
        new_properties = entity.properties
        if update.property_updates:
            new_properties = dict(entity.properties)
            new_properties.update(update.property_updates)
        
        # Multi-tick interaction updates
        new_interaction = entity.interaction
        if update.interaction:
            if update.interaction.reset:
                from src_v2.core.state import InteractionComponent
                new_interaction = InteractionComponent()
            else:
                new_interaction = replace(
                    entity.interaction,
                    target_node_id=update.interaction.target_node_id if update.interaction.target_node_id is not None else entity.interaction.target_node_id,
                    progress=entity.interaction.progress + update.interaction.progress_delta
                )

        # Inventory updates (Authoritative weight/slot accounting)
        new_inventory = entity.inventory
        if update.inventory:
            from src_v2.engine.interaction import InteractionSystem
            
            new_items = list(entity.inventory.items)
            new_items.extend(update.inventory.items_added)
            for item in update.inventory.items_removed:
                if item in new_items:
                    new_items.remove(item)
            
            # Recalculate weight from the authoritative system
            new_weight = sum(InteractionSystem.get_weight(item) for item in new_items)
            
            new_inventory = replace(
                entity.inventory,
                items=new_items,
                current_slots_used=len(new_items),
                current_weight=new_weight
            )

        return replace(
            entity,
            position=update.new_position if update.new_position is not None else entity.position,
            readiness=entity.readiness + update.readiness_delta,
            active=update.active if update.active is not None else entity.active,
            interaction=new_interaction,
            inventory=new_inventory,
            properties=new_properties
        )
