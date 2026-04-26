from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Dict, Any

from src.core.state import AuthoritativeState, EntityState, InventoryComponent
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
        current_corpses = dict(prior_state.corpses)
        new_ground_items = dict(prior_state.ground_items)
        
        # Phase 16: Splash Damage Resolution (Pre-loop)
        extra_damage = {} # entity_id -> total_splash_damage
        from src.engine.legality import LegalityServiceV2
        for e_id, ent_upd in update.entity_updates.items():
            if ent_upd.combat:
                for intent in ent_upd.combat.simultaneous_intents:
                    if intent.splash_radius > 0:
                        impact_pos = ent_upd.new_position or prior_state.entities[e_id].position
                        for other_id, other_ent in prior_state.entities.items():
                            if other_id == e_id: continue # Skip primary target (usually)
                            dist = LegalityServiceV2.get_manhattan_dist(impact_pos, other_ent.position)
                            if dist <= intent.splash_radius:
                                extra_damage[other_id] = extra_damage.get(other_id, 0) + intent.splash_damage

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
            region = LegalityServiceV2.get_region_for_position(entity.position, prior_state)
            hazard_damage = 0
            if region and region.hazard_level > 0:
                hazard_damage = int(region.hazard_level * 10 * (1.0 + region.calamity_intensity))
            
            # Phase 22: Starvation
            starvation_damage = 0
            if entity.biological.hunger >= 100.0:
                starvation_damage = 5
            
            new_hp = max(0, entity.combat.hp - hazard_damage - starvation_damage - extra_damage.get(e_id, 0))
            new_combat = replace(entity.combat, hp=new_hp)
            
            # Phase 24: Regional Sovereignty Debuffs (CONQUERED_DEBUFF)
            if entity.identity.role == EntityRole.HERO and region and region.owner_faction_id == Faction.MONSTER_HORDE:
                from src.world.regional_sovereignty import RegionalSovereigntyService
                new_combat = replace(new_combat, 
                    atk=int(new_combat.atk * RegionalSovereigntyService.CONQUERED_ATK_DEF_MOD),
                    def_stat=int(new_combat.def_stat * RegionalSovereigntyService.CONQUERED_ATK_DEF_MOD),
                    speed=int(new_combat.speed * RegionalSovereigntyService.CONQUERED_SPD_MOD)
                )
            
            # PH5 M2: Boredom Decay
            BOREDOM_DECAY = 0.05
            decayed_boredom = {}
            for kind, val in entity.strategic.boredom.items():
                new_val = max(0.0, val - BOREDOM_DECAY)
                if new_val > 0.001:
                    decayed_boredom[kind] = new_val
            new_strategic = replace(entity.strategic, boredom=decayed_boredom)

            # Milestone 5 Law: Passive Advancement (Readiness gain)
            # Applied AFTER action costs to ensure gain during active ticks.
            readiness_after_upd = entity.readiness
            ent_upd = update.entity_updates.get(e_id)
            if ent_upd:
                readiness_after_upd += ent_upd.readiness_delta
            
            # Phase 22: Exhaustion Penalty (50% slower readiness gain)
            passive_gain = 10.0
            if entity.biological.sleep_debt > 80.0:
                passive_gain *= 0.5
                
            final_readiness = min(100.0, readiness_after_upd + passive_gain)

            entity = replace(entity, 
                biological=new_biological, 
                lifecycle=new_lifecycle,
                combat=new_combat,
                strategic=new_strategic
            )
            
            if ent_upd:
                final_entity = ApplyPath._apply_entity_update(
                    entity, ent_upd
                )
                # Override readiness with the post-action+passive value
                final_entity = replace(final_entity, readiness=final_readiness)
                
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
                        position=final_entity.position,
                        items=list(final_entity.inventory.items), # V2: Drops all loot
                        decay_tick=prior_state.tick + 100, # Milestone 5 baseline
                        generation=final_entity.lifecycle.generation
                    )
                    
                new_entities[e_id] = final_entity
            else:
                new_entities[e_id] = replace(entity, readiness=final_readiness)
        
        taxation_upd = RegionalSovereigntyService.process_taxation(prior_state)
        
        # Merge Taxation into new_entities and global resources
        for e_id, ent_upd in taxation_upd.entity_updates.items():
            if e_id in new_entities:
                e = new_entities[e_id]
                if ent_upd.inventory:
                    from src.core.inventory import InventoryService
                    new_inv = InventoryService.apply_update(e.inventory, ent_upd.inventory)
                    new_entities[e_id] = replace(e, inventory=new_inv)
        
        new_resources = dict(prior_state.global_resources)
        for res_key, delta in taxation_upd.resource_updates.items():
            new_resources[res_key] = new_resources.get(res_key, 0.0) + delta
                
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
                    functional=False if new_hp == 0 else (build_upd.functional_set if build_upd.functional_set is not None else building.functional)
                )
                
                # Regional Trauma for Building Destruction
                if is_death:
                    from src.engine.legality import LegalityServiceV2
                    region = LegalityServiceV2.get_region_for_position(building.position, prior_state)
                    if region and region.id in new_regions:
                        current_r = new_regions[region.id]
                        new_regions[region.id] = replace(current_r, trauma_score=current_r.trauma_score + 2.0)

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
                    trauma_score=region.trauma_score + world_upd.trauma_delta,
                    influence=max(-100.0, min(100.0, region.influence + world_upd.influence_delta)),
                    owner_faction_id=(None if world_upd.owner_faction_id_set == -1 else world_upd.owner_faction_id_set) if world_upd.owner_faction_id_set is not None else region.owner_faction_id,
                    kind=world_upd.kind_set if world_upd.kind_set is not None else region.kind,
                    weather=world_upd.weather_set if world_upd.weather_set is not None else region.weather,
                    active_modifiers=[m for m in list(region.active_modifiers) + world_upd.modifiers_add if m not in world_upd.modifiers_remove]
                )

        new_resources = dict(prior_state.global_resources)
        sorted_resource_keys = sorted(update.resource_updates.keys())
        for r_key in sorted_resource_keys:
            delta = update.resource_updates[r_key]
            new_resources[r_key] = new_resources.get(r_key, 0.0) + delta
        
        # Phase 24: Merge Taxation resources
        for r_key, delta in taxation_upd.resource_updates.items():
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

        new_state = replace(
            prior_state,
            tick=next_tick if next_tick is not None else prior_state.tick,
            world_time=next_world_time if next_world_time is not None else prior_state.world_time,
            entities=new_entities,
            resource_nodes=new_nodes,
            buildings=new_buildings,
            groups=new_groups,
            regions=new_regions,
            corpses=current_corpses,
            ground_items=new_ground_items,
            global_resources=new_resources,
            periodic_due_ticks=new_periodic,
            work_debt=new_debt,
            maturity=update.maturity_set if update.maturity_set is not None else prior_state.maturity,
            last_calamity_tick=update.last_calamity_tick_set if update.last_calamity_tick_set is not None else prior_state.last_calamity_tick,
            rng_checkpoint=update.rng_checkpoint or prior_state.rng_checkpoint
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
            from src.core.inventory import InventoryService
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
        
        return new_state

    @staticmethod
    def _apply_entity_update(entity: EntityState, update: EntityUpdate) -> EntityState:
        """
        Apply updates to a single entity, producing a new EntityState instance.
        """
        from src.progression.leveling import LevelingService
        new_properties = entity.properties
        if update.property_updates:
            new_properties = dict(entity.properties)
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
            from src.core.inventory import InventoryService
            new_inventory = InventoryService.apply_update(entity.inventory, update.inventory)

        if update.equipment:
            new_slots = dict(entity.equipment.slots)
            for slot, item_id in update.equipment.slot_updates.items():
                new_slots[slot] = item_id
            new_equipment = replace(entity.equipment, slots=new_slots)

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
                evolution_points=entity.identity.evolution_points + update.identity.evolution_points_delta,
                unspent_ap=entity.identity.unspent_ap + update.identity.unspent_ap_delta
            )
            if update.identity.breakthroughs_add:
                new_breakthroughs = set(new_identity.active_breakthroughs)
                new_breakthroughs.update(update.identity.breakthroughs_add)
                new_identity = replace(new_identity, active_breakthroughs=new_breakthroughs)
            if update.identity.unspent_ap_set is not None:
                 new_identity = replace(new_identity, unspent_ap=update.identity.unspent_ap_set)
            
            # PH8 Task 8.3: Veterancy processing
            if update.identity.veterancy_points_delta != 0:
                from src.progression.veterancy import VeterancyService
                new_identity = VeterancyService.process_points(new_identity, update.identity.veterancy_points_delta)
        if update.attributes:
            new_attributes = replace(
                entity.attributes,
                strength=max(0, min(100, entity.attributes.strength + update.attributes.strength_delta)),
                agility=max(0, min(100, entity.attributes.agility + update.attributes.agility_delta)),
                vitality=max(0, min(100, entity.attributes.vitality + update.attributes.vitality_delta)),
                endurance=max(0, min(100, entity.attributes.endurance + update.attributes.endurance_delta)),
                intelligence=max(0, min(100, entity.attributes.intelligence + update.attributes.intelligence_delta)),
                spirit=max(0, min(100, entity.attributes.spirit + update.attributes.spirit_delta)),
                wisdom=max(0, min(100, entity.attributes.wisdom + update.attributes.wisdom_delta)),
                perception=max(0, min(100, entity.attributes.perception + update.attributes.perception_delta)),
                charisma=max(0, min(100, entity.attributes.charisma + update.attributes.charisma_delta))
            )
            # Recalculate derived stats
            derived = LevelingService.recalculate_combat_stats(new_attributes)
            new_combat = replace(
                new_combat,
                max_hp=derived["max_hp"],
                atk=derived["atk"],
                def_stat=derived["def_stat"],
                evasion=derived["evasion"]
            )
            # Ensure HP doesn't exceed new max
            if new_combat.hp > new_combat.max_hp:
                new_combat = replace(new_combat, hp=new_combat.max_hp)

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

        if update.combat:
            new_max_hp = entity.combat.max_hp + update.combat.max_hp_delta
            new_hp = max(0, min(new_max_hp, entity.combat.hp + update.combat.hp_delta))
            is_alive = update.combat.alive_set if update.combat.alive_set is not None else (new_hp > 0)
            from src.core.state import CombatComponent
            new_combat = CombatComponent(
                hp=new_hp, 
                max_hp=new_max_hp,
                atk=entity.combat.atk + update.combat.atk_delta, 
                def_stat=entity.combat.def_stat + update.combat.def_delta,
                range=entity.combat.range,
                evasion=entity.combat.evasion, 
                alive=is_alive
            )

        if update.navigation:
            from src.core.state import NavigationComponent
            new_navigation = replace(
                entity.navigation,
                target=update.navigation.target_set if update.navigation.target_set is not None else entity.navigation.target,
                path=update.navigation.path_set if update.navigation.path_set is not None else entity.navigation.path,
                moved_recently=update.navigation.moved_recently_set if update.navigation.moved_recently_set is not None else entity.navigation.moved_recently,
                last_failure_reason=update.navigation.failure_reason if update.navigation.failure_reason is not None else entity.navigation.last_failure_reason
            )

        if update.task:
            from src.core.state import TaskComponent
            new_task = replace(
                entity.task,
                work_kind=update.task.work_kind_set if update.task.work_kind_set is not None else entity.task.work_kind,
                payload=update.task.payload_set if update.task.payload_set is not None else entity.task.payload
            )

        if update.quest:
            from src.core.quests import QuestState, QuestStatus
            from src.quests.service import QuestService
            q_id = update.quest.quest_id
            if q_id in new_strategic.projects:
                proj = new_strategic.projects[q_id]
                if isinstance(proj, QuestState):
                    # 1. Apply progress
                    updated_quest = QuestService.add_progress(proj, update.quest.progress_delta)
                    
                    # 2. Manual status override (if any)
                    if update.quest.status_set is not None:
                        updated_quest = replace(updated_quest, quest_status=update.quest.status_set)
                    
                    # 3. Handle Completion -> Rewarded transition (Authoritative Reward Emission)
                    if updated_quest.quest_status == QuestStatus.COMPLETED and proj.quest_status == QuestStatus.ACTIVE:
                        # Auto-transition to REWARDED to prevent double-rewards
                        updated_quest = QuestService.mark_rewarded(updated_quest)
                        
                        # Grant XP
                        new_identity = replace(
                            new_identity, 
                            evolution_points=new_identity.evolution_points + updated_quest.reward.xp
                        )
                        # Grant Gold and Items
                        from src.core.updates import InventoryUpdate
                        from src.core.inventory import InventoryService
                        from src.core.state import ItemStack
                        reward_inv_upd = InventoryUpdate(
                            gold_delta=updated_quest.reward.gold,
                            items_add=[ItemStack(item_id=tid, quantity=1) for tid in updated_quest.reward.items]
                        )
                        new_inventory = InventoryService.apply_update(new_inventory, reward_inv_upd)
                    
                    new_projs = dict(new_strategic.projects)
                    new_projs[q_id] = updated_quest
                    new_strategic = replace(new_strategic, projects=new_projs)

        if update.reward:
            # XP Gain
            new_identity = replace(
                new_identity,
                evolution_points=new_identity.evolution_points + update.reward.xp_gain
            )
            # Gold Gain
            from src.core.updates import InventoryUpdate
            inv_upd = InventoryUpdate(gold_delta=update.reward.gold_gain)
            from src.core.inventory import InventoryService
            new_inventory = InventoryService.apply_update(new_inventory, inv_upd)
            # Item Gain (deferred to InventoryService)
            if update.reward.items_gain:
                from src.core.state import ItemStack
                items_to_add = [ItemStack(item_id=tid, quantity=1) for tid in update.reward.items_gain]
                inv_upd_items = InventoryUpdate(items_add=items_to_add)
                new_inventory = InventoryService.apply_update(new_inventory, inv_upd_items)

        # PH8 M3: Authoritative Leveling
        curr_xp = new_identity.evolution_points
        curr_lvl = new_identity.evolution_level
        
        # PROG-015: Learning Rate / Undead No-Level Law
        learning_rate = getattr(entity.aptitude, "learning_rate", 1.0)
        
        if learning_rate > 0:
            while curr_lvl < 100: # PH8 Task 8.3: Level-up respects cap (100)
                xp_needed = LevelingService.get_xp_required(curr_lvl)
                if curr_xp >= xp_needed:
                    curr_xp -= xp_needed
                    curr_lvl += 1
                    # Scale stats (Hybrid logic)
                    new_combat = LevelingService.scale_combat_stats(new_combat, curr_lvl, role=new_identity.role)
                    # Grant AP for Heroes (Base 5 + Milestone 5 every 5 levels)
                    if new_identity.role == EntityRole.HERO:
                        ap_gain = 5
                        if curr_lvl % 5 == 0:
                            ap_gain += 5 # Milestone bonus
                        new_identity = replace(new_identity, unspent_ap=new_identity.unspent_ap + ap_gain)
                else:
                    break
            
            if curr_lvl >= 100:
                curr_xp = 0
        
        # PH8 Task 8.5: Evolution Check
        final_kind = update.kind_set if update.kind_set is not None else entity.kind
        from src.progression.evolution import EvolutionService
        evo_kind = EvolutionService.check_evolution(final_kind, curr_lvl)
        if evo_kind:
            final_kind = evo_kind
            # Refresh gear for evolved form
            from src.core.state import EquipmentComponent, EquipSlot
            evo_gear = EvolutionService.get_evolution_gear(evo_kind)
            if evo_gear:
                new_equipment = EquipmentComponent(
                    slots={EquipSlot(k): v for k, v in evo_gear.items()}
                )
        
        if curr_lvl != new_identity.evolution_level or final_kind != entity.kind:
            new_identity = replace(new_identity, evolution_level=curr_lvl, evolution_points=curr_xp)

        return replace(
            entity,
            kind=final_kind,
            position=update.new_position if update.new_position is not None else entity.position,
            readiness=entity.readiness + update.readiness_delta,
            active=update.active if update.active is not None else entity.active,
            interaction=new_interaction,
            identity=new_identity,
            inventory=new_inventory,
            strategic=new_strategic,
            social=new_social,
            biological=new_biological,
            lifecycle=new_lifecycle,
            attributes=new_attributes,
            combat=new_combat,
            equipment=new_equipment,
            navigation=new_navigation,
            task=new_task,
            group_id=update.group_id_set if update.group_id_set is not None and update.group_id_set != -1 else (None if update.group_id_set == -1 else entity.group_id),
            properties=new_properties
        )
