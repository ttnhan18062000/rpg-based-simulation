from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Dict, Any

from src.core.state import AuthoritativeState, EntityState, InventoryComponent
from src.core.inventory import InventoryService
from src.core.enums import EntityRole, Faction

if TYPE_CHECKING:
    from src.core.updates import StateUpdate, EntityUpdate


class ApplyPath:
    """
    The singular authority for state transitions.
    """

    @staticmethod
    def apply_generation(
        prior_state: AuthoritativeState,
        update: StateUpdate,
        next_tick: int | None = None,
        next_world_time: int | None = None
    ) -> AuthoritativeState:
        """
        Produce a new state generation from the prior state and updates.
        """
        new_entities = {}
        
        # Phase 11: Regional Recovery (Passive decay of trauma and scars)
        from src.world.consequences import RegionalConsequenceService
        from src.world.influence import FactionInfluenceService
        from src.world.regional_sovereignty import RegionalSovereigntyService
        
        new_regions, new_scars = RegionalConsequenceService.process_recovery(prior_state)
        
        # Phase 9: Corpse Decay
        current_corpses = {}
        for c_id, corpse in prior_state.corpses.items():
            if prior_state.tick < corpse.decay_tick:
                current_corpses[c_id] = corpse
        
        new_ground_items = dict(prior_state.ground_items)
        
        for e_id, entity in prior_state.entities.items():
            if e_id in update.entities_remove:
                continue
                
            
            # Phase 9: Biological Decay
            # Every tick, hunger and sleep debt increase slightly
            new_hunger = min(100.0, entity.biological.hunger + 0.1)
            new_sleep = min(100.0, entity.biological.sleep_debt + 0.05)
            new_biological = replace(entity.biological, hunger=new_hunger, sleep_debt=new_sleep)
            
            # Phase 9: Lifecycle Aging
            new_lifecycle = replace(entity.lifecycle, age_ticks=entity.lifecycle.age_ticks + 1)
            
            # Phase 9: Regional Hazard Drain
            from src.engine.legality import LegalityServiceV2
            region = LegalityServiceV2.get_region_for_position(entity.navigation.position, prior_state)
            hazard_damage = 0
            if region and region.hazard_level > 0:
                hazard_damage = int(region.hazard_level * 10 * (1.0 + region.calamity_intensity))
            
            # Phase 22: Starvation
            starvation_damage = 0
            if entity.biological.hunger >= 100.0:
                starvation_damage = 5
            
            new_hp = max(0, entity.combat.hp - hazard_damage - starvation_damage)
            new_combat = replace(entity.combat, hp=new_hp)
            
            # PH5 M2: Boredom Decay
            BOREDOM_DECAY = 0.05
            decayed_boredom = {}
            for kind, val in entity.strategic.boredom.items():
                new_val = max(0.0, val - BOREDOM_DECAY)
                if new_val > 0.001:
                    decayed_boredom[kind] = new_val
            
            new_strategic = replace(entity.strategic, boredom=decayed_boredom)

            # Milestone 5 Law: Passive Advancement (Readiness gain)
            # Global recovery (+10.0) is now provided by the AuthoritativeApplyPipeline.
            readiness_after_upd = entity.combat.readiness
            ent_upd = update.entity_updates.get(e_id)
            if ent_upd:
                readiness_after_upd += ent_upd.readiness_delta
            
            final_readiness = min(100.0, readiness_after_upd)

            entity = replace(entity, 
                biological=new_biological, 
                lifecycle=new_lifecycle,
                combat=new_combat,
                strategic=new_strategic
            )

            # Per-tick Stamina Passive Regen (Checklist Part 6 Section E)
            is_resting = entity.task.work_kind in ("REST", "SLEEP")
            from src.engine.rpg_depth import StaminaService
            stam_regen = StaminaService.tick_regen(entity.stamina, is_resting=is_resting)
            if stam_regen > 0:
                entity = replace(entity, stamina=replace(
                    entity.stamina,
                    current=min(entity.stamina.max_stamina, entity.stamina.current + stam_regen)
                ))
            
            # Domain 4: Social Passive Memory (Per-tick)
            from src.systems.social_memory import SocialMemoryService
            from src.core.updates import SocialUpdate, EntityUpdate
            mem_up = SocialMemoryService.tick_place_attachment(entity, prior_state)
            nem_up = SocialMemoryService.check_nemesis_promotion(entity)
            
            if mem_up or nem_up:
                if ent_upd:
                    merged_social = (ent_upd.social or SocialUpdate())
                    if mem_up: merged_social = merged_social.merge(mem_up)
                    if nem_up: merged_social = merged_social.merge(nem_up)
                    ent_upd = replace(ent_upd, social=merged_social)
                else:
                    final_social = mem_up or nem_up
                    if mem_up and nem_up: final_social = mem_up.merge(nem_up)
                    ent_upd = EntityUpdate(entity_id=e_id, social=final_social)
            
            if ent_upd:
                final_entity = ApplyPath._apply_entity_update(
                    entity, ent_upd
                )
                # Override readiness with the post-action+passive value
                final_entity = replace(final_entity, combat=replace(final_entity.combat, readiness=final_readiness))
                
                # PH6 M2: Corpse Spawning & Regional Trauma
                was_alive = prior_state.entities[e_id].combat.alive
                is_now_dead = was_alive and not final_entity.combat.alive
                if is_now_dead:
                    from src.core.state import CorpseState
                    from src.engine.legality import LegalityServiceV2
                    
                    # 1. Spawn Corpse
                    corpse_id = 1000000 + e_id # Deterministic ID mapping
                    current_corpses[corpse_id] = CorpseState(
                        id=corpse_id,
                        original_entity_id=e_id,
                        position=final_entity.navigation.position,
                        items=list(final_entity.inventory.items), # V2: Drops all loot
                        decay_tick=prior_state.tick + 100, # Milestone 5 baseline
                        generation=final_entity.lifecycle.generation
                    )
                    
                new_entities[e_id] = final_entity
            else:
                new_entities[e_id] = replace(entity, combat=replace(entity.combat, readiness=final_readiness))
        
        new_resources = dict(prior_state.global_resources)
                
        # Phase 11: Authoritative Addition of Entities
        for e in update.entities_add:
            new_entities[e.id] = e
        
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
        
        for node in update.nodes_add:
            new_nodes[node.id] = node

        new_buildings = dict(prior_state.buildings)
        sorted_building_ids = sorted(update.building_updates.keys())
        for b_id in sorted_building_ids:
            build_upd = update.building_updates[b_id]
            if b_id in new_buildings:
                building = new_buildings[b_id]
                new_hp = max(0, building.hp + build_upd.hp_delta)
                is_death = building.functional and new_hp == 0
                
                new_buildings[b_id] = replace(
                    building,
                    hp=new_hp,
                    functional=False if new_hp == 0 else (build_upd.functional_set if build_upd.functional_set is not None else building.functional),
                    inventory=InventoryService.apply_update(building.inventory, build_upd.inventory) if build_upd.inventory else building.inventory,
                    price_modifiers=build_upd.price_modifiers_set if build_upd.price_modifiers_set is not None else building.price_modifiers
                )
                
                # Regional Trauma for Building Destruction
                if is_death:
                    from src.engine.legality import LegalityServiceV2
                    region = LegalityServiceV2.get_region_for_position(building.position, prior_state)
                    if region and region.id in new_regions:
                        current_r = new_regions[region.id]
                        new_regions[region.id] = replace(current_r, trauma_score=current_r.trauma_score + 2.0)

        new_camps = dict(prior_state.camps)
        sorted_camp_ids = sorted(update.camp_updates.keys())
        for c_id in sorted_camp_ids:
            c_upd = update.camp_updates[c_id]
            if c_id in new_camps:
                camp = new_camps[c_id]
                new_camps[c_id] = replace(
                    camp,
                    maturity=max(0.0, camp.maturity + c_upd.maturity_delta),
                    active=c_upd.active_set if c_upd.active_set is not None else camp.active,
                    last_raid_tick=c_upd.last_raid_tick_set if c_upd.last_raid_tick_set is not None else camp.last_raid_tick
                )

        new_groups = dict(prior_state.groups)
        for g in update.groups_add_or_update:
            new_groups[g.id] = g
        for g_id in update.groups_remove:
            new_groups.pop(g_id, None)

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
                    trauma_score=max(0.0, min(100.0, world_upd.trauma_score_set if world_upd.trauma_score_set is not None else (region.trauma_score + world_upd.trauma_delta))),
                    retaliation_pressure=max(0.0, min(100.0, world_upd.retaliation_pressure_set if world_upd.retaliation_pressure_set is not None else (region.retaliation_pressure + world_upd.retaliation_pressure_delta))),
                    influence=max(-100.0, min(100.0, region.influence + world_upd.influence_delta)),
                    owner_faction_id=(None if world_upd.owner_faction_id_set == -1 else world_upd.owner_faction_id_set) if world_upd.owner_faction_id_set is not None else region.owner_faction_id,
                    kind=world_upd.kind_set if world_upd.kind_set is not None else region.kind,
                    weather=world_upd.weather_set if world_upd.weather_set is not None else region.weather,
                    active_modifiers=[m for m in list(region.active_modifiers) + world_upd.modifiers_add if m not in world_upd.modifiers_remove],
                    price_modifiers=world_upd.price_modifiers_set if world_upd.price_modifiers_set is not None else region.price_modifiers
                )

        new_resources = dict(prior_state.global_resources)
        sorted_resource_keys = sorted(update.resource_updates.keys())
        for r_key in sorted_resource_keys:
            delta = update.resource_updates[r_key]
            new_resources[r_key] = new_resources.get(r_key, 0.0) + delta
        
        # Phase 24: Merge resources
            
        new_periodic = dict(prior_state.periodic_due_ticks)
        sorted_periodic_keys = sorted(update.periodic_updates.keys())
        for p_key in sorted_periodic_keys:
            new_periodic[p_key] = update.periodic_updates[p_key]
            
        new_debt = dict(prior_state.work_debt)
        sorted_debt_keys = sorted(update.work_debt_updates.keys())
        for d_key in sorted_debt_keys:
            delta = update.work_debt_updates[d_key]
            new_debt[d_key] = max(0, new_debt.get(d_key, 0) + delta)

        new_state = replace(
            prior_state,
            tick=next_tick if next_tick is not None else prior_state.tick,
            world_time=next_world_time if next_world_time is not None else prior_state.world_time,
            entities=new_entities,
            resource_nodes=new_nodes,
            buildings=new_buildings,
            camps=new_camps,
            regions=new_regions,
            groups=new_groups,
            corpses=current_corpses,
            ground_items=new_ground_items,
            global_resources=new_resources,
            periodic_due_ticks=new_periodic,
            work_debt=new_debt,
            maturity=update.maturity_set if update.maturity_set is not None else prior_state.maturity,
            last_calamity_tick=update.last_calamity_tick_set if update.last_calamity_tick_set is not None else prior_state.last_calamity_tick,
            next_node_id=update.next_node_id_set if update.next_node_id_set is not None else prior_state.next_node_id,
            next_entity_id=update.next_entity_id_set if update.next_entity_id_set is not None else prior_state.next_entity_id,
            rng_checkpoint=update.rng_checkpoint or prior_state.rng_checkpoint,
            transaction_trace=update.transaction_trace,
            pressure_signals=update.pressure_signals_set if update.pressure_signals_set is not None else prior_state.pressure_signals,
            current_mode=update.current_mode_set if update.current_mode_set is not None else prior_state.current_mode,
            rejection_registry={k: prior_state.rejection_registry.get(k, 0) + v for k, v in update.rejections_delta.items()} if update.rejections_delta else prior_state.rejection_registry
        )
        
        # PH6 M2: Ground Items and Corpses
        for item in update.ground_items_add_or_update:
            new_ground_items[item.id] = item
        for item_id in update.ground_items_remove:
            new_ground_items.pop(item_id, None)
            
        for corpse in update.corpses_add_or_update:
            current_corpses[corpse.id] = corpse
        for corpse_id in update.corpses_remove:
            current_corpses.pop(corpse_id, None)
            
        # PH6 M5: Chests and Home Storage
        new_chests = dict(new_state.chests)
        for chest in update.chest_add_or_update:
            new_chests[chest.id] = chest
        sorted_chest_ids = sorted(update.chest_updates.keys())
        for c_id in sorted_chest_ids:
            c_upd = update.chest_updates[c_id]
            if c_id in new_chests:
                c = new_chests[c_id]
                new_chests[c_id] = replace(
                    c,
                    cooldown_remaining=c_upd.cooldown_set if c_upd.cooldown_set is not None else c.cooldown_remaining,
                    items=c_upd.items_set if c_upd.items_set is not None else c.items
                )
                
        new_storage = dict(new_state.home_storage)
        sorted_storage_ids = sorted(update.home_storage_updates.keys())
        for s_id in sorted_storage_ids:
            s_upd = update.home_storage_updates[s_id]
            # Use InventoryService to apply update to storage component
            current_inv = new_storage.get(s_id) or InventoryComponent()
            new_storage[s_id] = InventoryService.apply_update(current_inv, s_upd)
            
        new_state = replace(
            new_state,
            ground_items=new_ground_items,
            corpses=current_corpses,
            chests=new_chests,
            home_storage=new_storage
        )
        
        # Phase 11: Local Scars authoritative updates
        final_scars = dict(new_scars)
        for scar in update.scars_add_or_update:
            final_scars[scar.id] = scar
        for scar_id in update.scars_remove:
            final_scars.pop(scar_id, None)

        new_state = replace(new_state, local_scars=final_scars)
        
        # Merge rejections (External Truth Phase E4.7)
        if update.rejections_delta:
            new_registry = dict(new_state.rejection_registry)
            for key, delta in update.rejections_delta.items():
                new_registry[key] = new_registry.get(key, 0) + delta
            new_state = replace(new_state, rejection_registry=new_registry)
            
        if update.processed_transaction_ids:
            new_processed = set(new_state.processed_transaction_ids)
            new_processed.update(update.processed_transaction_ids)
            new_state = replace(new_state, processed_transaction_ids=new_processed)
            
        return new_state

    @staticmethod
    def _apply_entity_update(entity: EntityState, update: EntityUpdate) -> EntityState:
        """
        Apply updates to a single entity, producing a new EntityState instance.
        """
        from src.progression.leveling import LevelingService
        new_properties = entity.identity.properties
        if update.property_updates:
            new_properties = dict(entity.identity.properties)
            new_properties.update(update.property_updates)

        new_interaction = entity.interaction
        new_inventory = entity.inventory
        new_equipment = entity.equipment
        new_identity = entity.identity
        new_strategic = entity.strategic
        new_social = entity.social
        new_biological = entity.biological
        new_lifecycle = entity.lifecycle
        new_combat = entity.combat
        new_navigation = entity.navigation
        new_task = entity.task
        new_attributes = entity.attributes
        if update.interaction:
            if update.interaction.reset:
                from src.core.state import InteractionComponent
                new_interaction = InteractionComponent()
            else:
                new_interaction = replace(
                    entity.interaction,
                    target_node_id=update.interaction.target_node_id if update.interaction.target_node_id is not None else entity.interaction.target_node_id,
                    progress=entity.interaction.progress + update.interaction.progress_delta
                )

        if update.inventory:
            # RPG-RES-202: Atomic inventory application
            new_inventory = InventoryService.apply_update(entity.inventory, update.inventory)

        if update.equipment:
            new_slots = dict(entity.equipment.slots)
            for slot, item_id in update.equipment.slot_updates.items():
                new_slots[slot] = item_id
            
            # Phase 8: Durability Updates
            new_durability = dict(entity.equipment.durability)
            # 1. Deltas
            for slot, delta in update.equipment.durability_delta.items():
                new_durability[slot] = max(0.0, min(100.0, new_durability.get(slot, 100.0) + delta))
            # 2. Sets
            for slot, val in update.equipment.durability_set.items():
                new_durability[slot] = max(0.0, min(100.0, val))
                
            new_equipment = replace(entity.equipment, slots=new_slots, durability=new_durability)

        if update.identity:
            new_recipes = set(entity.identity.known_recipes)
            new_recipes.update(update.identity.recipes_learned)
            
            new_cooldowns = dict(entity.identity.cooldowns)
            for skill_id, tick in update.identity.cooldown_updates.items():
                new_cooldowns[skill_id] = tick
                
            new_identity = replace(
                entity.identity,
                role=update.identity.role_set if update.identity.role_set is not None else entity.identity.role,
                faction=update.identity.faction_set if update.identity.faction_set is not None else entity.identity.faction,
                known_recipes=new_recipes,
                craft_target=update.identity.craft_target if update.identity.craft_target is not None else entity.identity.craft_target,
                evolution_level=update.identity.evolution_level_set if update.identity.evolution_level_set is not None else entity.identity.evolution_level,
                evolution_points=entity.identity.evolution_points + update.identity.evolution_points_delta,
                unspent_ap=entity.identity.unspent_ap + update.identity.unspent_ap_delta,
                learned_skills=entity.identity.learned_skills.union(update.identity.learned_skills),
                traits=set(list(entity.identity.traits) + update.identity.traits_add),
                cooldowns=new_cooldowns
            )
            if update.identity.traits_remove:
                new_traits = set(new_identity.traits)
                for t in update.identity.traits_remove:
                    new_traits.discard(t)
                new_identity = replace(new_identity, traits=new_traits)
            if update.identity.breakthroughs_add:
                new_breakthroughs = set(new_identity.active_breakthroughs)
                new_breakthroughs.update(update.identity.breakthroughs_add)
                new_identity = replace(new_identity, active_breakthroughs=new_breakthroughs)
            if update.identity.unspent_ap_set is not None:
                 new_identity = replace(new_identity, unspent_ap=update.identity.unspent_ap_set)
            
            if update.identity.veterancy_points_delta != 0:
                from src.progression.veterancy import VeterancyService
                new_identity = VeterancyService.process_points(new_identity, update.identity.veterancy_points_delta)
        if update.attributes:
            new_attributes = replace(
                entity.attributes,
                strength=max(1, min(100, entity.attributes.strength + update.attributes.strength_delta)),
                agility=max(1, min(100, entity.attributes.agility + update.attributes.agility_delta)),
                vitality=max(1, min(100, entity.attributes.vitality + update.attributes.vitality_delta)),
                endurance=max(1, min(100, entity.attributes.endurance + update.attributes.endurance_delta)),
                intelligence=max(1, min(100, entity.attributes.intelligence + update.attributes.intelligence_delta)),
                spirit=max(1, min(100, entity.attributes.spirit + update.attributes.spirit_delta)),
                wisdom=max(1, min(100, entity.attributes.wisdom + update.attributes.wisdom_delta)),
                perception=max(1, min(100, entity.attributes.perception + update.attributes.perception_delta)),
                charisma=max(1, min(100, entity.attributes.charisma + update.attributes.charisma_delta))
            )
            # Recalculate derived stats - REMOVED (Handled by FINAL RECALCULATION GATE)

        if update.strategic:
            # Helper to merge dict-based updates
            def merge_dict(current_dict, add_list, remove_list):
                res = dict(current_dict)
                for item in add_list:
                    res[item.id] = item
                for item_id in remove_list:
                    res.pop(item_id, None)
                return res

            new_strategic = replace(
                entity.strategic,
                blockers=merge_dict(entity.strategic.blockers, update.strategic.blockers_add_or_update, update.strategic.blockers_remove),
                leads=merge_dict(entity.strategic.leads, update.strategic.leads_add_or_update, update.strategic.leads_remove),
                directives=merge_dict(entity.strategic.directives, update.strategic.directives_add_or_update, update.strategic.directives_remove),
                projects=merge_dict(entity.strategic.projects, update.strategic.projects_add_or_update, update.strategic.projects_remove),
                concerns=merge_dict(entity.strategic.concerns, update.strategic.concerns_add_or_update, update.strategic.concerns_remove),
                candidate_zones=merge_dict(entity.strategic.candidate_zones, update.strategic.candidate_zones_add_or_update, update.strategic.candidate_zones_remove),
                hypotheses=merge_dict(entity.strategic.hypotheses, update.strategic.hypotheses_add_or_update, update.strategic.hypotheses_remove),
                current_project_id=update.strategic.current_project_id_set if update.strategic.current_project_id_set is not None else entity.strategic.current_project_id,
                current_objective_id=update.strategic.current_objective_id_set if update.strategic.current_objective_id_set is not None else entity.strategic.current_objective_id,
                contracts=merge_dict(entity.strategic.contracts, update.strategic.contracts_add_or_update, update.strategic.contracts_remove)
            )
            
            # PH5 M2: Handle boredom_delta
            if update.strategic.boredom_delta:
                merged_boredom = dict(new_strategic.boredom)
                for kind, delta in update.strategic.boredom_delta.items():
                    merged_boredom[kind] = merged_boredom.get(kind, 0.0) + delta
                new_strategic = replace(new_strategic, boredom=merged_boredom)
            
            # Handle source trust separately as key is entity_id
            if update.strategic.source_trust_updates:
                new_trust = dict(new_strategic.source_trust)
                for entry in update.strategic.source_trust_updates:
                    new_trust[entry.entity_id] = entry
                new_strategic = replace(new_strategic, source_trust=new_trust)

        if update.social:
            from src.social.relationships import RelationshipService
            new_social = RelationshipService.process_update(entity.social, update.social)

        if update.biological:
            from src.core.state import BiologicalComponent
            new_biological = replace(
                entity.biological,
                sleep_debt=update.biological.sleep_debt_set if update.biological.sleep_debt_set is not None else max(0.0, min(100.0, entity.biological.sleep_debt + update.biological.sleep_debt_delta)),
                hunger=update.biological.hunger_set if update.biological.hunger_set is not None else max(0.0, min(100.0, entity.biological.hunger + update.biological.hunger_delta)),
                rest_pressure=entity.biological.rest_pressure + update.biological.rest_pressure_delta,
                last_meal_tick=update.biological.last_meal_tick_set if update.biological.last_meal_tick_set is not None else entity.biological.last_meal_tick,
                last_sleep_tick=update.biological.last_sleep_tick_set if update.biological.last_sleep_tick_set is not None else entity.biological.last_sleep_tick,
                well_rested_until=update.biological.well_rested_until_set if update.biological.well_rested_until_set is not None else entity.biological.well_rested_until
            )

        if update.lifecycle:
            from src.core.state import LifecycleComponent
            new_heirlooms = list(entity.lifecycle.heirlooms)
            new_heirlooms.extend(update.lifecycle.heirlooms_add)
            new_lifecycle = replace(
                entity.lifecycle,
                age_ticks=entity.lifecycle.age_ticks + update.lifecycle.age_delta,
                generation=entity.lifecycle.generation + update.lifecycle.generation_delta,
                is_permadeath=update.lifecycle.is_permadeath_set if update.lifecycle.is_permadeath_set is not None else entity.lifecycle.is_permadeath,
                death_tick=update.lifecycle.death_tick_set if update.lifecycle.death_tick_set is not None else entity.lifecycle.death_tick,
                death_reason=update.lifecycle.death_reason_set if update.lifecycle.death_reason_set is not None else entity.lifecycle.death_reason,
                heir_entity_id=update.lifecycle.heir_entity_id_set if update.lifecycle.heir_entity_id_set is not None else entity.lifecycle.heir_entity_id,
                heirlooms=new_heirlooms
            )

        if update.combat and update.combat.outcome_kind != "REJECTED":
            new_max_hp = entity.combat.max_hp + update.combat.max_hp_delta
            new_hp = max(0, min(new_max_hp, entity.combat.hp + update.combat.hp_delta))
            is_alive = update.combat.alive_set if update.combat.alive_set is not None else (new_hp > 0)
            
            new_combat = replace(
                entity.combat,
                hp=new_hp,
                max_hp=new_max_hp,
                atk=int(entity.combat.atk + update.combat.atk_delta),
                def_stat=int(entity.combat.def_stat + update.combat.def_delta),
                speed=int(max(1, entity.combat.speed + update.combat.speed_delta)),
                alive=is_alive
            )

        if update.navigation:
            from src.core.state import NavigationComponent
            target_val = update.navigation.target_set if update.navigation.target_set is not None else entity.navigation.target
            if update.navigation.clear_target: target_val = None
            
            path_val = update.navigation.path_set if update.navigation.path_set is not None else entity.navigation.path
            if update.navigation.clear_path: path_val = []

            new_navigation = replace(
                entity.navigation,
                target=target_val,
                path=path_val,
                moved_recently=update.navigation.moved_recently_set if update.navigation.moved_recently_set is not None else entity.navigation.moved_recently,
                movement_mode=update.navigation.movement_mode_set if update.navigation.movement_mode_set is not None else entity.navigation.movement_mode,
                last_failure_reason=update.navigation.failure_reason if update.navigation.failure_reason is not None else entity.navigation.last_failure_reason,
                wait_count=entity.navigation.wait_count + update.navigation.wait_count_delta,
                oscillation_count=entity.navigation.oscillation_count + update.navigation.oscillation_count_delta,
                last_position=update.navigation.last_position_set if update.navigation.last_position_set is not None else entity.navigation.last_position
            )

        if update.task:
            from src.core.state import TaskComponent
            new_task = replace(
                entity.task,
                work_kind=update.task.work_kind_set if update.task.work_kind_set is not None else entity.task.work_kind,
                payload=update.task.payload_set if update.task.payload_set is not None else entity.task.payload
            )

        # Stamina Update (Checklist Part 6 Section E)
        new_stamina = entity.stamina
        if update.stamina_update:
            new_current = entity.stamina.current
            if update.stamina_update.current_set is not None:
                new_current = update.stamina_update.current_set
            else:
                new_current += update.stamina_update.current_delta
            # VERIFIED v2: test_stamina_cannot_go_below_zero
            new_current = max(0.0, min(entity.stamina.max_stamina, new_current))
            new_stamina = replace(
                entity.stamina,
                current=new_current,
                max_stamina=update.stamina_update.max_stamina_set if update.stamina_update.max_stamina_set is not None else entity.stamina.max_stamina
            )

        # Wound/Scar Update (Checklist Part 6 Section E)
        new_wounds = list(entity.combat.wounds)
        new_scars = list(entity.combat.scars)
        if update.wound_update:
            new_wounds.extend(update.wound_update.wounds_add)
            new_scars.extend(update.wound_update.scars_add)
            if update.wound_update.wounds_heal:
                new_wounds = [w if w.id not in update.wound_update.wounds_heal else replace(w, healed=True) for w in new_wounds]

        if update.quest:
            from src.core.quests import QuestState, QuestStatus
            from src.quests.service import QuestService
            
            q_updates = update.quest.multi_updates if update.quest.multi_updates else [update.quest]
            new_projs = dict(new_strategic.projects)
            
            for qu in q_updates:
                q_id = qu.quest_id
                if q_id in new_projs:
                    proj = new_projs[q_id]
                    if isinstance(proj, QuestState):
                        # 1. Apply progress
                        updated_quest = QuestService.add_progress(proj, qu.progress_delta)
                        
                        # 2. Manual status override (if any)
                        if qu.status_set is not None:
                            updated_quest = replace(updated_quest, quest_status=qu.status_set)
                        
                        new_projs[q_id] = updated_quest
            
            new_strategic = replace(new_strategic, projects=new_projs)

        if update.reward and update.reward.xp_gain > 0:
            from src.progression.leveling import LevelingService
            prog_upd = LevelingService.process_progression(new_identity, update.reward.xp_gain)
            
            # Merge progression update into new_identity
            new_identity = replace(
                new_identity,
                evolution_level=prog_upd.evolution_level_set if prog_upd.evolution_level_set is not None else new_identity.evolution_level,
                evolution_points=new_identity.evolution_points + prog_upd.evolution_points_delta,
                unspent_ap=new_identity.unspent_ap + prog_upd.unspent_ap_delta
            )
            # Flag stats as dirty if level changed
            if prog_upd.evolution_level_set is not None:
                stats_dirty = True

        # ---------------------------------------------------------------------
        # FINAL RECALCULATION GATE (PH8: Derived Stats Law)
        # ---------------------------------------------------------------------
        # If anything that impacts base stats changed, perform a final derivation.
        stats_dirty = (
            update.attributes is not None or 
            update.equipment is not None or 
            (update.identity is not None and (
                update.identity.learned_skills or 
                update.identity.traits_add or 
                update.identity.traits_remove
            )) or
            update.wound_update is not None
        )
        
        if stats_dirty:
            from src.engine.rpg_depth import SkillScalingService
            derived = SkillScalingService.get_effective_stats(
                new_attributes, new_equipment,
                wounds=new_wounds, scars=new_scars,
                learned_skills=new_identity.learned_skills,
                traits=new_identity.traits,
                current_role=entity.combat.tactical_role
            )
            
            # Apply derived values. 
            # Note: We preserve the current HP (after deltas) but cap it at new max.
            new_combat = replace(
                new_combat,
                max_hp=derived["max_hp"],
                atk=derived["atk"],
                def_stat=derived["def_stat"],
                evasion=derived["evasion"],
                move_cost=derived.get("move_cost", new_combat.move_cost),
                range=derived.get("range", new_combat.range),
                tactical_role=derived.get("tactical_role", new_combat.tactical_role)
            )
            
            # RPG-0064: Level up results in resource refills
            if update.identity and update.identity.evolution_level_set is not None:
                new_combat = replace(new_combat, hp=derived["max_hp"])
                new_stamina = replace(new_stamina, current=new_stamina.max_stamina)
            elif (update.reward and update.reward.xp_gain > 0 and 
                  new_identity.evolution_level > entity.identity.evolution_level):
                # Also check for XP-triggered level ups
                new_combat = replace(new_combat, hp=derived["max_hp"])
                new_stamina = replace(new_stamina, current=new_stamina.max_stamina)
            else:
                if new_combat.hp > new_combat.max_hp:
                    new_combat = replace(new_combat, hp=new_combat.max_hp)

        # Final assembly with AOA compliance
        res = replace(
            entity,
            kind=update.kind_set if update.kind_set is not None else entity.kind,
            interaction=new_interaction,
            identity=replace(new_identity, 
                group_id=update.group_id_set if update.group_id_set is not None and update.group_id_set != -1 else (None if update.group_id_set == -1 else entity.identity.group_id),
                properties=new_properties,
                latest_intent_results=update.intent_results
            ),
            inventory=new_inventory,
            strategic=new_strategic,
            social=new_social,
            biological=new_biological,
            lifecycle=replace(new_lifecycle,
                active=update.active if update.active is not None else entity.lifecycle.active
            ),
            attributes=new_attributes,
            combat=replace(new_combat,
                readiness=entity.combat.readiness + update.readiness_delta,
                wounds=new_wounds,
                scars=new_scars,
                latest_result=update.combat
            ),
            equipment=new_equipment,
            navigation=replace(new_navigation,
                position=update.new_position if update.new_position is not None else entity.navigation.position
            ),
            task=new_task,
            stamina=new_stamina
        )
        return res
