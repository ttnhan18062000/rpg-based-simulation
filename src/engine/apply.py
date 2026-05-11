# Compliance IDs: COMB-039, COMB-040, COMB-282, PROG-065, PROG-066, PROG-067, PROG-068, PROG-069, PROG-070, PROG-071, PROG-072, PROG-087, PROG-088, PROG-089, PROG-090, PROG-091, PROG-092, SOC-043, STRAT-086, STRAT-137, STRAT-138, STRAT-139, TOWN-022, TOWN-031, TOWN-103, TOWN-106, TOWN-107, TOWN-108, TOWN-112, TOWN-114, TOWN-115, TOWN-119, TOWN-120, TOWN-121, TOWN-122, TOWN-123, TOWN-124, TOWN-125, TOWN-129, TOWN-130, TOWN-132, TOWN-136, TOWN-137, WORLD-001, WORLD-002, WORLD-003, WORLD-004
# Compliance IDs: COMB-039, COMB-040, SOC-043, STRAT-086, STRAT-137, STRAT-138, STRAT-139, TOWN-022, TOWN-031
from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Dict, Any

from src.core.state import (
    AuthoritativeState, EntityState, InventoryComponent, CorpseState, 
    InteractionComponent, BiologicalComponent, LifecycleComponent, 
    NavigationComponent, TaskComponent, StrategicComponent, StaminaComponent, CombatComponent
)
from src.engine.cadence import SystemCadence, should_run
from src.core.inventory import InventoryService
from src.core.enums import EntityRole, Faction, ReasonCode
from src.core.updates import StateUpdate, EntityUpdate, SocialUpdate, StrategicUpdate, StaminaUpdate, NavigationUpdate
from src.engine.legality import LegalityServiceV2
from src.engine.rpg_depth import StaminaService, SkillScalingService
from src.systems.social_memory import SocialMemoryService
from src.world.consequences import RegionalConsequenceService
from src.world.influence import FactionInfluenceService
from src.world.regional_sovereignty import RegionalSovereigntyService
from src.progression.leveling import LevelingService
from src.core.quests import QuestState, QuestStatus
from src.quests.service import QuestService
from src.systems.social_systems.relationships import RelationshipService
from src.progression.veterancy import VeterancyService

if TYPE_CHECKING:
    pass


class ApplyPath:
    """
    The singular authority for state transitions.
    """

    @staticmethod
    def apply_passive(state: AuthoritativeState, cadence: SystemCadence | None = None) -> AuthoritativeState:
        """
        Apply only passive per-tick decay/advancement logic.
        Optimized v2.5: Reduced allocations via staggered updates and identity preservation.
        """
        cadence = cadence or SystemCadence()
        new_regions, new_scars = RegionalConsequenceService.process_recovery(state)
        
        current_corpses = {}
        for c_id, corpse in state.corpses.items():
            if state.tick < corpse.decay_tick:
                current_corpses[c_id] = corpse

        new_entities = {}
        regions = state.regions
        has_regions = len(regions) > 0
        region_list = list(regions.values()) if has_regions else []
        entities_changed = False
        
        for e_id, entity in state.entities.items():
            bio = entity.biological
            life = entity.lifecycle
            
            # Regional lookup (Calculated once per entity per tick)
            # CORE-PERF-014: Use cached region_id if available
            current_region = None
            region_id = entity.navigation.region_id
            if has_regions:
                if region_id and region_id in regions:
                    current_region = regions[region_id]
                else:
                    pos = entity.navigation.position
                    for r in region_list:
                        x_min, y_min, x_max, y_max = r.bounds
                        if x_min <= pos[0] <= x_max and y_min <= pos[1] <= y_max:
                            current_region = r
                            region_id = r.id
                            break
            
            # Regional Hazard & Starvation
            hazard_damage = 0
            if current_region and current_region.hazard_level > 0:
                hazard_damage = int(current_region.hazard_level * 10 * (1.0 + current_region.calamity_intensity))
            
            starvation_damage = 5 if bio.hunger >= 100.0 else 0
            total_damage = hazard_damage + starvation_damage
            
            # Boredom Decay
            strat = entity.strategic
            new_boredom = strat.boredom
            if strat.boredom:
                # Optimized boredom decay
                new_boredom = {k: v - 0.05 for k, v in strat.boredom.items() if v > 0.051}

            # Stamina Passive Regen
            stamina = entity.stamina
            is_resting = entity.task.work_kind in ("REST", "SLEEP")
            stam_regen = StaminaService.tick_regen(stamina, is_resting=is_resting)
            
            # -----------------------------------------------------------------
            # Staggered Passive Check (Optimization: CORE-PERF-012)
            # -----------------------------------------------------------------
            is_bio_due = should_run(state.tick, e_id, cadence.biological)
            is_life_due = should_run(state.tick, e_id, cadence.lifecycle)
            
            # If nothing changed, preserve object identity to allow cache reuse
            if (not is_bio_due and not is_life_due and 
                total_damage == 0 and stam_regen == 0 and 
                new_boredom is strat.boredom and
                region_id == entity.navigation.region_id):
                new_entities[e_id] = entity
                continue

            entities_changed = True
            # Manual Reconstruction (Optimization: Logic ID CORE-PERF-010)
            new_entities[e_id] = EntityState(
                id=entity.id,
                kind=entity.kind,
                identity=entity.identity,
                attributes=entity.attributes,
                inventory=entity.inventory,
                strategic=StrategicComponent(
                    profile=strat.profile,
                    blockers=strat.blockers,
                    leads=strat.leads,
                    directives=strat.directives,
                    projects=strat.projects,
                    concerns=strat.concerns,
                    candidate_zones=strat.candidate_zones,
                    hypotheses=strat.hypotheses,
                    current_project_id=strat.current_project_id,
                    current_objective_id=strat.current_objective_id,
                    boredom=new_boredom,
                    source_trust=strat.source_trust,
                    contracts=strat.contracts,
                    turning_points=strat.turning_points,
                    overload_source=strat.overload_source,
                    overload_tick=strat.overload_tick
                ) if new_boredom is not strat.boredom else strat,
                social=entity.social,
                biological=BiologicalComponent(
                    sleep_debt=min(100.0, bio.sleep_debt + 0.05 * cadence.biological),
                    hunger=min(100.0, bio.hunger + 0.1 * cadence.biological),
                    rest_pressure=bio.rest_pressure,
                    last_meal_tick=bio.last_meal_tick,
                    last_sleep_tick=bio.last_sleep_tick,
                    well_rested_until=bio.well_rested_until
                ) if is_bio_due else bio,
                lifecycle=LifecycleComponent(
                    age_ticks=life.age_ticks + cadence.lifecycle,
                    max_age_ticks=life.max_age_ticks,
                    is_permadeath=life.is_permadeath,
                    death_tick=life.death_tick,
                    death_reason=life.death_reason,
                    generation=life.generation,
                    heir_entity_id=life.heir_entity_id,
                    heirlooms=life.heirlooms,
                    active=life.active
                ) if is_life_due else life,
                aptitude=entity.aptitude,
                combat=CombatComponent(
                    hp=max(0, entity.combat.hp - total_damage),
                    max_hp=entity.combat.max_hp,
                    atk=entity.combat.atk,
                    def_stat=entity.combat.def_stat,
                    speed=entity.combat.speed,
                    range=entity.combat.range,
                    evasion=entity.combat.evasion,
                    move_cost=entity.combat.move_cost,
                    tactical_role=entity.combat.tactical_role,
                    action_style=entity.combat.action_style,
                    alive=entity.combat.alive and (entity.combat.hp - total_damage > 0),
                    readiness=entity.combat.readiness,
                    wounds=entity.combat.wounds,
                    scars=entity.combat.scars,
                    latest_result=entity.combat.latest_result
                ) if total_damage > 0 else entity.combat,
                equipment=entity.equipment,
                navigation=replace(entity.navigation, region_id=region_id) if region_id != entity.navigation.region_id else entity.navigation,
                task=entity.task,
                stamina=StaminaComponent(
                    current=min(stamina.max_stamina, stamina.current + stam_regen),
                    max_stamina=stamina.max_stamina,
                    regen_rate=stamina.regen_rate,
                    rest_regen_rate=stamina.rest_regen_rate,
                    exhaustion_threshold=stamina.exhaustion_threshold,
                    exhaustion_penalty=stamina.exhaustion_penalty
                ) if stam_regen > 0 and stamina.current < stamina.max_stamina else stamina,
                interaction=entity.interaction
            )

        # Optimization: Reuse collections if NO changes occurred
        final_entities = new_entities if entities_changed or len(new_entities) != len(state.entities) else state.entities
        
        # M10 Law: Use identity checks for collection preservation (O(1))
        if (final_entities is state.entities and 
            new_regions is state.regions and 
            new_scars is state.local_scars and 
            current_corpses is state.corpses):
            return state

        return replace(
            state,
            entities=final_entities,
            regions=new_regions,
            local_scars=new_scars,
            corpses=current_corpses
        )

    @staticmethod
    def apply_partial(state: AuthoritativeState, update: StateUpdate) -> AuthoritativeState:
        """
        Apply only the specified updates to an already-passively-advanced state.
        Optimized v2.2: reused regional lookup for social memory.
        """
        # CORE-PERF-016: Lazy dictionary creation
        new_entities = state.entities
        any_changed = False
        
        if update.entities_remove:
            new_entities = dict(state.entities)
            any_changed = True
            for e_id in update.entities_remove:
                new_entities.pop(e_id, None)

        regions = state.regions
        has_regions = len(regions) > 0
        region_list = list(regions.values()) if has_regions else []

        # Apply Entity Updates
        for e_id, ent_upd in update.entity_updates.items():
            if e_id not in new_entities or ent_upd.is_noop():
                continue
            
            # CORE-PERF-016: Deferred clone until first mutation
            if not any_changed:
                new_entities = dict(state.entities)
                any_changed = True
                
            entity = new_entities[e_id]
            
            # Find region once for this entity
            # CORE-PERF-014: O(1) regional lookup via cache
            region_id = entity.navigation.region_id
            if region_id is None and has_regions:
                ex, ey = entity.navigation.position
                for r in region_list:
                    xmin, ymin, xmax, ymax = r.bounds
                    if xmin <= ex <= xmax and ymin <= ey <= ymax:
                        region_id = r.id
                        break

            # Special case: Social Passive Memory depends on update context
            mem_up = SocialMemoryService.tick_place_attachment(entity, state, region_id=region_id)
            nem_up = SocialMemoryService.check_nemesis_promotion(entity)
            
            if mem_up or nem_up:
                merged_social = (ent_upd.social or SocialUpdate())
                if mem_up: merged_social = merged_social.merge(mem_up)
                if nem_up: merged_social = merged_social.merge(nem_up)
                ent_upd = replace(ent_upd, social=merged_social)

            # Strategic Consequences from Combat
            if ent_upd.combat and ent_upd.combat.strategic_upd:
                merged_strategic = ent_upd.strategic
                if merged_strategic:
                    merged_strategic = merged_strategic.merge(ent_upd.combat.strategic_upd)
                else:
                    merged_strategic = ent_upd.combat.strategic_upd
                ent_upd = replace(ent_upd, strategic=merged_strategic)

            final_entity = ApplyPath._apply_entity_update(entity, ent_upd)
            new_entities[e_id] = final_entity

        if not any_changed:
            return state

        return replace(
            state,
            entities=new_entities
        )

    @staticmethod
    def apply_generation(
        prior_state: AuthoritativeState,
        update: StateUpdate,
        next_tick: int | None = None,
        next_world_time: int | None = None,
        cadence: SystemCadence | None = None,
        audit_mode: bool = False
    ) -> AuthoritativeState:
        """
        Produce a new state generation from the prior state and updates.
        Logic ID: TOWN-132 (Source and inventory mutations are atomic)
        """
        # 1. Passive Phase
        # We still call these, but we'll extract the components if they changed
        passive_state = ApplyPath.apply_passive(prior_state, cadence=cadence)
        
        # 1.5 Compact updates
        update = update.compact()
        
        # 2. Update Phase
        final_state = ApplyPath.apply_partial(passive_state, update)

        # 3. Collect all changes for non-entity objects
        # Initialize with values from final_state (which already has passive + partial entity updates)
        changes = {
            "tick": next_tick if next_tick is not None else prior_state.tick,
            "world_time": next_world_time if next_world_time is not None else prior_state.world_time,
            "entities": final_state.entities,
            "regions": final_state.regions,
            "local_scars": final_state.local_scars,
            "corpses": final_state.corpses,
            "ground_items": final_state.ground_items,
            "resource_nodes": final_state.resource_nodes,
            "buildings": final_state.buildings,
            "camps": final_state.camps,
            "groups": final_state.groups,
            "global_resources": final_state.global_resources,
            "periodic_due_ticks": final_state.periodic_due_ticks,
            "work_debt": final_state.work_debt,
            "maturity": update.maturity_set if update.maturity_set is not None else prior_state.maturity,
            "last_calamity_tick": update.last_calamity_tick_set if update.last_calamity_tick_set is not None else prior_state.last_calamity_tick,
            "next_node_id": update.next_node_id_set if update.next_node_id_set is not None else prior_state.next_node_id,
            "next_entity_id": update.next_entity_id_set if update.next_entity_id_set is not None else prior_state.next_entity_id,
            "rng_checkpoint": update.rng_checkpoint or prior_state.rng_checkpoint,
            "pressure_signals": update.pressure_signals_set if update.pressure_signals_set is not None else prior_state.pressure_signals,
            "current_mode": update.current_mode_set if update.current_mode_set is not None else prior_state.current_mode,
            "rejection_registry": prior_state.rejection_registry,
            "town_entity_ids": final_state.town_entity_ids,
            "chests": final_state.chests,
            "home_storage": final_state.home_storage,
            "transaction_trace": prior_state.transaction_trace,
            "processed_transaction_ids": prior_state.processed_transaction_ids
        }

        # 4. Merge non-entity updates into the changes dict
        if update.rejections_delta:
            changes["rejection_registry"] = {k: prior_state.rejection_registry.get(k, 0) + v for k, v in update.rejections_delta.items()}

        if update.node_updates or update.nodes_add:
            new_nodes = dict(changes["resource_nodes"])
            for n_id, node_upd in update.node_updates.items():
                if n_id in new_nodes:
                    node = new_nodes[n_id]
                    new_nodes[n_id] = replace(
                        node,
                        remaining_charges=max(0, node.remaining_charges + node_upd.charges_delta),
                        cooldown_remaining=node_upd.cooldown_set if node_upd.cooldown_set is not None else node.cooldown_remaining
                    )
            for node in update.nodes_add:
                new_nodes[node.id] = node
            changes["resource_nodes"] = new_nodes

        if update.building_updates:
            new_buildings = dict(changes["buildings"])
            new_regions = dict(changes["regions"])
            for b_id, build_upd in update.building_updates.items():
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
                    if is_death:
                        region = LegalityServiceV2.get_region_for_position(building.position, prior_state)
                        if region and region.id in new_regions:
                            current_r = new_regions[region.id]
                            new_regions[region.id] = replace(current_r, trauma_score=current_r.trauma_score + 2.0)
            changes["buildings"] = new_buildings
            changes["regions"] = new_regions

        if update.camp_updates:
            new_camps = dict(changes["camps"])
            for c_id, c_upd in update.camp_updates.items():
                if c_id in new_camps:
                    camp = new_camps[c_id]
                    new_camps[c_id] = replace(
                        camp,
                        maturity=max(0.0, camp.maturity + c_upd.maturity_delta),
                        active=c_upd.active_set if c_upd.active_set is not None else camp.active,
                        last_raid_tick=c_upd.last_raid_tick_set if c_upd.last_raid_tick_set is not None else camp.last_raid_tick
                    )
            changes["camps"] = new_camps

        if update.groups_add_or_update or update.groups_remove:
            new_groups = dict(changes["groups"])
            for g in update.groups_add_or_update:
                new_groups[g.id] = g
            for g_id in update.groups_remove:
                new_groups.pop(g_id, None)
            changes["groups"] = new_groups

        if update.world_updates:
            new_regions = dict(changes["regions"])
            for r_id, world_upd in update.world_updates.items():
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
            changes["regions"] = new_regions

        if update.resource_updates:
            new_resources = dict(changes["global_resources"])
            for r_key, delta in update.resource_updates.items():
                new_resources[r_key] = new_resources.get(r_key, 0.0) + delta
            changes["global_resources"] = new_resources

        if update.periodic_updates:
            new_periodic = dict(changes["periodic_due_ticks"])
            for p_key, val in update.periodic_updates.items():
                new_periodic[p_key] = val
            changes["periodic_due_ticks"] = new_periodic

        if update.work_debt_updates:
            new_debt = dict(changes["work_debt"])
            for d_key, delta in update.work_debt_updates.items():
                new_debt[d_key] = max(0, new_debt.get(d_key, 0) + delta)
            changes["work_debt"] = new_debt

        # Corpse/Ground Item lifecycle
        new_corpses = dict(changes["corpses"])
        corpses_changed = False
        for c_id, corpse in prior_state.corpses.items():
            if prior_state.tick >= corpse.decay_tick:
                new_corpses.pop(c_id, None)
                corpses_changed = True
        
        # New corpses from death
        for e_id, ent_upd in update.entity_updates.items():
            if e_id in changes["entities"]:
                final_entity = changes["entities"][e_id]
                was_alive = prior_state.entities[e_id].combat.alive
                if was_alive and not final_entity.combat.alive:
                    corpse_id = 1000000 + e_id
                    new_corpses[corpse_id] = CorpseState(
                        id=corpse_id,
                        original_entity_id=e_id,
                        position=final_entity.navigation.position,
                        items=list(final_entity.inventory.items),
                        decay_tick=prior_state.tick + 100,
                        generation=final_entity.lifecycle.generation
                    )
                    corpses_changed = True
        
        for corpse in update.corpses_add_or_update:
            new_corpses[corpse.id] = corpse
            corpses_changed = True
        for corpse_id in update.corpses_remove:
            new_corpses.pop(corpse_id, None)
            corpses_changed = True
        if corpses_changed:
            changes["corpses"] = new_corpses

        if update.ground_items_add_or_update or update.ground_items_remove:
            new_ground_items = dict(changes["ground_items"])
            for item in update.ground_items_add_or_update:
                new_ground_items[item.id] = item
            for item_id in update.ground_items_remove:
                new_ground_items.pop(item_id, None)
            changes["ground_items"] = new_ground_items

        if update.chest_add_or_update or update.chest_updates:
            new_chests = dict(changes["chests"])
            for chest in update.chest_add_or_update:
                new_chests[chest.id] = chest
            for c_id, c_upd in update.chest_updates.items():
                if c_id in new_chests:
                    c = new_chests[c_id]
                    new_chests[c_id] = replace(
                        c,
                        cooldown_remaining=c_upd.cooldown_set if c_upd.cooldown_set is not None else c.cooldown_remaining,
                        items=c_upd.items_set if c_upd.items_set is not None else c.items
                    )
            changes["chests"] = new_chests

        if update.home_storage_updates:
            new_storage = dict(changes["home_storage"])
            for s_id, s_upd in update.home_storage_updates.items():
                current_inv = new_storage.get(s_id) or InventoryComponent()
                new_storage[s_id] = InventoryService.apply_update(current_inv, s_upd)
            changes["home_storage"] = new_storage

        if update.scars_add_or_update or update.scars_remove:
            new_scars = dict(changes["local_scars"])
            for scar in update.scars_add_or_update:
                new_scars[scar.id] = scar
            for scar_id in update.scars_remove:
                new_scars.pop(scar_id, None)
            changes["local_scars"] = new_scars

        # Audit/Trace logic
        if audit_mode:
            if update.transaction_trace:
                new_trace = list(prior_state.transaction_trace)
                new_trace.extend(update.transaction_trace)
                if len(new_trace) > prior_state.MAX_TRACE_SIZE:
                    new_trace = new_trace[-prior_state.MAX_TRACE_SIZE:]
                changes["transaction_trace"] = new_trace
                
            if update.processed_transaction_ids:
                new_processed = list(prior_state.processed_transaction_ids)
                for tid in update.processed_transaction_ids:
                    if tid not in new_processed:
                        new_processed.append(tid)
                if len(new_processed) > prior_state.MAX_PROCESSED_IDS:
                    new_processed = new_processed[-prior_state.MAX_PROCESSED_IDS:]
                changes["processed_transaction_ids"] = new_processed
        else:
            if prior_state.transaction_trace or prior_state.processed_transaction_ids:
                changes["transaction_trace"] = []
                changes["processed_transaction_ids"] = []

        # 5. PERFORM SINGLE REPLACE
        # Determine if any changes actually occurred compared to prior_state
        # For efficiency, we could check identity of all components, but replace is safe.
        return replace(prior_state, **changes)

    @staticmethod
    def _apply_entity_update(entity: EntityState, update: EntityUpdate) -> EntityState:
        """
        Apply updates to a single entity, producing a new EntityState instance.
        """
        # Processed via top-level imports
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
                new_interaction = InteractionComponent()
            else:
                new_interaction = replace(
                    entity.interaction,
                    target_node_id=update.interaction.target_node_id if update.interaction.target_node_id is not None else entity.interaction.target_node_id,
                    progress=entity.interaction.progress + update.interaction.progress_delta
                )

        if update.inventory:
            # RPG-RES-202: Atomic inventory application
            # Logic ID: TOWN-132 (Inventory mutation in authoritative apply)
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
                contracts=merge_dict(entity.strategic.contracts, update.strategic.contracts_add_or_update, update.strategic.contracts_remove),
                turning_points=entity.strategic.turning_points + update.strategic.turning_points_add
            )
            
            # Enforce Bandwidth (Rolling limits for history)
            # 1. Turning Points
            max_tps = getattr(entity.strategic.profile, "max_turning_points", 20)
            if len(new_strategic.turning_points) > max_tps:
                # Keep latest ones (history is chronological)
                trimmed_tps = new_strategic.turning_points[-max_tps:]
                new_strategic = replace(new_strategic, turning_points=trimmed_tps)
            
            # 2. Rejection Events (If any on entity - though they are global in AuthoritativeState, 
            # some entities might have local history if we added it. Currently they don't.)
            
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
            # Processed via top-level imports
            new_social = RelationshipService.process_update(entity.social, update.social)

        if update.biological:
            # Processed via top-level imports
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
            # Processed via top-level imports
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
            # Processed via top-level imports
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
            # Processed via top-level imports
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
            # Processed via top-level imports
            
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
            # Processed via top-level imports
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
            # Logic ID: PROG-071 (Effective stats recompute from base + gear + traits)
            # Logic ID: PROG-090 (Gear equip changes effective stats)
            # Processed via top-level imports
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
            # Logic ID: PROG-072 (Effective stats clamp to valid ranges)
            
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

        # ---------------------------------------------------------------------
        # FINAL ASSEMBLY (AOA Compliance)
        # ---------------------------------------------------------------------
        changes = {}
        if update.kind_set is not None and update.kind_set != entity.kind:
            changes["kind"] = update.kind_set
        if new_interaction is not entity.interaction:
            changes["interaction"] = new_interaction
        
        # Identity logic
        if new_identity is not entity.identity or \
           (update.group_id_set is not None and update.group_id_set != entity.identity.group_id) or \
           update.intent_results:
            
            final_group_id = update.group_id_set if update.group_id_set is not None and update.group_id_set != -1 else (None if update.group_id_set == -1 else entity.identity.group_id)
            
            # Sub-replace for identity only if needed
            id_changes = {}
            if new_identity is not entity.identity:
                # We already did replace for new_identity, so we might need to merge these
                # but for simplicity, let's just see if we can avoid the sub-replace
                pass
            
            new_identity = replace(new_identity, 
                group_id=final_group_id,
                properties=new_properties,
                latest_intent_results=update.intent_results
            )
            if new_identity is not entity.identity:
                changes["identity"] = new_identity

        if new_inventory is not entity.inventory:
            changes["inventory"] = new_inventory
        if new_strategic is not entity.strategic:
            changes["strategic"] = new_strategic
        if new_social is not entity.social:
            changes["social"] = new_social
        if new_biological is not entity.biological:
            changes["biological"] = new_biological
        
        if new_lifecycle is not entity.lifecycle or (update.active is not None and update.active != entity.lifecycle.active):
            changes["lifecycle"] = replace(new_lifecycle,
                active=update.active if update.active is not None else entity.lifecycle.active
            )
            
        if new_attributes is not entity.attributes:
            changes["attributes"] = new_attributes

        # Combat final assembly
        if new_combat is not entity.combat or update.readiness_delta != 0 or \
           new_wounds != list(entity.combat.wounds) or new_scars != list(entity.combat.scars) or \
           update.combat is not None:
            
            # Apply readiness delta and clamp
            final_readiness = max(0.0, min(100.0, entity.combat.readiness + update.readiness_delta))
            
            changes["combat"] = replace(new_combat,
                readiness=final_readiness,
                wounds=new_wounds,
                scars=new_scars,
                latest_result=update.combat
            )

        if new_equipment is not entity.equipment:
            changes["equipment"] = new_equipment

        if new_navigation is not entity.navigation or update.new_position is not None:
            # Phase 3 Hardening: Clear region_id cache if position changes
            final_region_id = new_navigation.region_id
            if update.new_position is not None and update.new_position != entity.navigation.position:
                final_region_id = None
                
            changes["navigation"] = replace(new_navigation,
                position=update.new_position if update.new_position is not None else entity.navigation.position,
                region_id=final_region_id
            )

        if new_task is not entity.task:
            changes["task"] = new_task
            
        if new_stamina is not entity.stamina:
            changes["stamina"] = new_stamina
            
        if not changes:
            return entity
            
        return replace(entity, **changes)
