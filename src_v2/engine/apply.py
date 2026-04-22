from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Dict

from src_v2.core.state import AuthoritativeState, EntityState

if TYPE_CHECKING:
    from src_v2.core.updates import StateUpdate, EntityUpdate


class ApplyPath:
    """
    The singular authority for state transitions.
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
        """
        new_entities = {}
        for e_id, entity in prior_state.entities.items():
            # Milestone 5 Law: Passive Advancement (Readiness gain)
            # Every tick, entities gain 10.0 readiness (capped at 100.0)
            passive_readiness = min(100.0, entity.readiness + 10.0)
            entity = replace(entity, readiness=passive_readiness)
            
            ent_upd = update.entity_updates.get(e_id)
            if ent_upd:
                new_entities[e_id] = ApplyPath._apply_entity_update(
                    entity, ent_upd
                )
            else:
                new_entities[e_id] = entity
        
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

        new_buildings = dict(prior_state.buildings)
        sorted_building_ids = sorted(update.building_updates.keys())
        for b_id in sorted_building_ids:
            build_upd = update.building_updates[b_id]
            if b_id in new_buildings:
                building = new_buildings[b_id]
                new_buildings[b_id] = replace(
                    building,
                    hp=max(0, building.hp + build_upd.hp_delta),
                    functional=build_upd.functional_set if build_upd.functional_set is not None else building.functional
                )

        new_regions = dict(prior_state.regions)
        sorted_region_ids = sorted(update.world_updates.keys())
        for r_id in sorted_region_ids:
            world_upd = update.world_updates[r_id]
            if r_id in new_regions:
                region = new_regions[r_id]
                new_regions[r_id] = replace(
                    region,
                    hazard_level=world_upd.hazard_level_set if world_upd.hazard_level_set is not None else region.hazard_level,
                    suppression_active=world_upd.suppression_set if world_upd.suppression_set is not None else region.suppression_active,
                    calamity_intensity=world_upd.calamity_intensity_set if world_upd.calamity_intensity_set is not None else region.calamity_intensity,
                    trauma_score=region.trauma_score + world_upd.trauma_delta
                )

        new_resources = dict(prior_state.global_resources)
        sorted_resource_keys = sorted(update.resource_updates.keys())
        for r_key in sorted_resource_keys:
            delta = update.resource_updates[r_key]
            new_resources[r_key] = new_resources.get(r_key, 0.0) + delta
            
        new_periodic = dict(prior_state.periodic_due_ticks)
        sorted_periodic_keys = sorted(update.periodic_updates.keys())
        for p_key in sorted_periodic_keys:
            new_periodic[p_key] = update.periodic_updates[p_key]
            
        new_debt = dict(prior_state.work_debt)
        sorted_debt_keys = sorted(update.work_debt_updates.keys())
        for d_key in sorted_debt_keys:
            delta = update.work_debt_updates[d_key]
            new_debt[d_key] = max(0, new_debt.get(d_key, 0) + delta)

        return replace(
            prior_state,
            tick=next_tick,
            world_time=next_world_time,
            entities=new_entities,
            resource_nodes=new_nodes,
            buildings=new_buildings,
            regions=new_regions,
            global_resources=new_resources,
            periodic_due_ticks=new_periodic,
            work_debt=new_debt,
            rng_checkpoint=update.rng_checkpoint or prior_state.rng_checkpoint
        )

    @staticmethod
    def _apply_entity_update(entity: EntityState, update: EntityUpdate) -> EntityState:
        """
        Apply updates to a single entity, producing a new EntityState instance.
        """
        new_properties = entity.properties
        if update.property_updates:
            new_properties = dict(entity.properties)
            new_properties.update(update.property_updates)
        
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

        new_inventory = entity.inventory
        if update.inventory:
            from src_v2.engine.interaction import InteractionSystem
            new_items = list(entity.inventory.items)
            new_items.extend(update.inventory.items_added)
            for item in update.inventory.items_removed:
                if item in new_items:
                    new_items.remove(item)
            new_weight = sum(InteractionSystem.get_weight(item) for item in new_items)
            new_inventory = replace(
                entity.inventory,
                items=new_items,
                current_slots_used=len(new_items),
                current_weight=new_weight,
                gold=entity.inventory.gold + update.inventory.gold_delta
            )

        new_identity = entity.identity
        if update.identity:
            new_recipes = set(entity.identity.known_recipes)
            new_recipes.update(update.identity.recipes_learned)
            new_identity = replace(
                entity.identity,
                role=update.identity.role_set if update.identity.role_set is not None else entity.identity.role,
                faction=update.identity.faction_set if update.identity.faction_set is not None else entity.identity.faction,
                known_recipes=new_recipes,
                craft_target=update.identity.craft_target if update.identity.craft_target is not None else entity.identity.craft_target,
                evolution_level=update.identity.evolution_level_set if update.identity.evolution_level_set is not None else entity.identity.evolution_level,
                evolution_points=entity.identity.evolution_points + update.identity.evolution_points_delta
            )

        new_strategic = entity.strategic
        if update.strategic:
            from src_v2.core.strategic import StrategicComponent
            new_blockers = dict(entity.strategic.blockers)
            new_leads = dict(entity.strategic.leads)
            for b in update.strategic.blockers_add_or_update:
                new_blockers[b.id] = b
            for bid in update.strategic.blockers_remove:
                if bid in new_blockers:
                    del new_blockers[bid]
            for l in update.strategic.leads_add_or_update:
                new_leads[l.id] = l
            for lid in update.strategic.leads_remove:
                if lid in new_leads:
                    del new_leads[lid]
            new_strategic = StrategicComponent(blockers=new_blockers, leads=new_leads)

        new_social = entity.social
        if update.social:
            from src_v2.core.state import SocialComponent
            new_trust = dict(entity.social.trust_history)
            for eid, delta in update.social.trust_delta.items():
                new_trust[eid] = max(0.0, min(1.0, new_trust.get(eid, 0.5) + delta))
            new_social = SocialComponent(
                trust_history=new_trust,
                betrayal_count=entity.social.betrayal_count + update.social.betrayal_increment,
                public_reputation=update.social.reputation_set if update.social.reputation_set is not None else entity.social.public_reputation
            )

        new_combat = entity.combat
        if update.combat:
            new_hp = max(0, entity.combat.hp + update.combat.hp_delta - update.combat.damage_taken)
            is_alive = update.combat.alive_set if update.combat.alive_set is not None else (new_hp > 0)
            from src_v2.core.state import CombatComponent
            new_combat = CombatComponent(
                hp=new_hp, max_hp=entity.combat.max_hp,
                atk=entity.combat.atk, def_stat=entity.combat.def_stat,
                evasion=entity.combat.evasion, alive=is_alive
            )

        new_navigation = entity.navigation
        if update.navigation:
            from src_v2.core.state import NavigationComponent
            new_navigation = replace(
                entity.navigation,
                target=update.navigation.target_set if update.navigation.target_set is not None else entity.navigation.target,
                path=update.navigation.path_set if update.navigation.path_set is not None else entity.navigation.path,
                moved_recently=update.navigation.moved_recently_set if update.navigation.moved_recently_set is not None else entity.navigation.moved_recently,
                last_failure_reason=update.navigation.failure_reason if update.navigation.failure_reason is not None else entity.navigation.last_failure_reason
            )

        new_task = entity.task
        if update.task:
            from src_v2.core.state import TaskComponent
            new_task = replace(
                entity.task,
                work_kind=update.task.work_kind_set if update.task.work_kind_set is not None else entity.task.work_kind,
                payload=update.task.payload_set if update.task.payload_set is not None else entity.task.payload
            )

        return replace(
            entity,
            kind=update.kind_set if update.kind_set is not None else entity.kind,
            position=update.new_position if update.new_position is not None else entity.position,
            readiness=entity.readiness + update.readiness_delta,
            active=update.active if update.active is not None else entity.active,
            interaction=new_interaction,
            identity=new_identity,
            inventory=new_inventory,
            strategic=new_strategic,
            social=new_social,
            combat=new_combat,
            navigation=new_navigation,
            task=new_task,
            properties=new_properties
        )
