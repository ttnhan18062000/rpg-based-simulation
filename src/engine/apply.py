# Compliance IDs: PERF-017, RES-202
from __future__ import annotations

import logging
# from dataclasses import replace
from typing import Dict, Any, List, Optional

def replace(obj: Any, **changes: Any) -> Any:
    """Fast dataclass replacement bypassing inspect/__init__ overhead."""
    cls = obj.__class__
    res = object.__new__(cls)
    for field_name, field_def in cls.__dataclass_fields__.items():
        if getattr(field_def, "_field_type", None) is not None and "CLASSVAR" in str(field_def._field_type).upper():
            continue
        val = changes[field_name] if field_name in changes else getattr(obj, field_name)
        try:
            object.__setattr__(res, field_name, val)
        except AttributeError:
            continue
    for field_name in cls.__dataclass_fields__:
        if field_name.endswith("_cache"):
            try:
                object.__setattr__(res, field_name, None)
            except AttributeError:
                pass
    return res

from src.core.state import (
    AuthoritativeState, EntityState, InventoryComponent, CorpseState, 
    InteractionComponent, BiologicalComponent, LifecycleComponent, 
    NavigationComponent, TaskComponent, StrategicComponent, StaminaComponent, CombatComponent,
    RegionState, ResourceNodeState, BuildingState, CampState, GroupRecord,
    GroundItemState, ChestState, LocalScarState, IntentResult, AttributeComponent, 
    IdentityComponent, AptitudeComponent, EquipmentComponent, SocialComponent, ReadOnlyDict
)
from src.core.quests import QuestState, QuestStatus
from src.engine.cadence import SystemCadence, should_run
from src.core.inventory import InventoryService
from src.core.enums import EntityRole, Faction, ReasonCode
from src.core.movement_modes import MovementMode
from src.core.updates import StateUpdate, EntityUpdate, SocialUpdate, StrategicUpdate, StaminaUpdate, NavigationUpdate
from src.engine.legality import LegalityServiceV2
from src.engine.rpg_depth import StaminaService, SkillScalingService
from src.systems.social_memory import SocialMemoryService
from src.systems.social_systems.relationships import RelationshipService
from src.progression.leveling import LevelingService
from src.progression.veterancy import VeterancyService
from src.quests.service import QuestService
from src.world.environment import EnvironmentService
from src.world.consequences import RegionalConsequenceService
from src.core.dirty import DirtySet, DirtySetBuilder

logger = logging.getLogger(__name__)

def shallow_freeze(obj: Any) -> Any:
    """Freezes a list to tuple to prevent accidental mutation."""
    if isinstance(obj, list):
        return tuple(obj)
    return obj

class ApplyPath:
    """
    The authoritative state application pipeline.
    Optimized v5: Unified Fused Apply with sub-100ms targets.
    """

    @staticmethod
    def apply_generation(
        prior_state: AuthoritativeState,
        update: StateUpdate,
        next_tick: int | None = None,
        next_world_time: int | None = None,
        cadence: SystemCadence | None = None,
        audit_mode: bool = False,
        audit_dirty_set: Any = None,
        passive: bool = True
    ) -> AuthoritativeState:
        """
        The root entry point for advancing the world state.
        Fuses passive advancement and intentional updates into a single pass.
        """
        tick = next_tick if next_tick is not None else prior_state.tick + 1
        world_time = next_world_time if next_world_time is not None else prior_state.world_time
        
        # 1. World Updates (Non-entity)
        # ---------------------------------------------------------------------
        new_groups = dict(prior_state.groups)
        for g_id in update.groups_remove:
            new_groups.pop(g_id, None)
        for g in update.groups_add_or_update:
            new_groups[g.id] = g

        recovered_regions, recovered_scars = RegionalConsequenceService.process_recovery(prior_state)
        new_regions = dict(recovered_regions)
        for r_id, r_upd in update.world_updates.items():
            if r_id in new_regions:
                reg = new_regions[r_id]
                haz = r_upd.hazard_level_set if r_upd.hazard_level_set is not None else reg.hazard_level
                sup = r_upd.suppression_set if r_upd.suppression_set is not None else reg.suppression_active
                cal = r_upd.calamity_intensity_set if r_upd.calamity_intensity_set is not None else reg.calamity_intensity
                tra = r_upd.trauma_score_set if r_upd.trauma_score_set is not None else reg.trauma_score + r_upd.trauma_delta
                ret = r_upd.retaliation_pressure_set if r_upd.retaliation_pressure_set is not None else reg.retaliation_pressure + r_upd.retaliation_pressure_delta
                inf = reg.influence + r_upd.influence_delta
                own = r_upd.owner_faction_id_set if r_upd.owner_faction_id_set is not None else reg.owner_faction_id
                knd = r_upd.kind_set if r_upd.kind_set is not None else reg.kind
                wth = r_upd.weather_set if r_upd.weather_set is not None else reg.weather
                mods = list(set([m for m in reg.active_modifiers if m not in r_upd.modifiers_remove] + r_upd.modifiers_add))
                prc = r_upd.price_modifiers_set if r_upd.price_modifiers_set is not None else reg.price_modifiers
                new_regions[r_id] = replace(reg, hazard_level=haz, suppression_active=sup, calamity_intensity=cal,
                                            trauma_score=tra, retaliation_pressure=ret, influence=inf,
                                            owner_faction_id=own, kind=knd, weather=wth, active_modifiers=mods,
                                            price_modifiers=prc)

        grid_invalidated = bool(update.nodes_add)
        new_active_nodes = getattr(prior_state, "_active_nodes_grid", None)
        if new_active_nodes is not None and not grid_invalidated:
            new_active_nodes = dict(new_active_nodes)
        else:
            new_active_nodes = None

        new_nodes = dict(prior_state.resource_nodes)
        for n_id, n_upd in update.node_updates.items():
            if n_id in new_nodes:
                node = new_nodes[n_id]
                was_active = node.remaining_charges > 0 and node.cooldown_remaining <= 0
                new_charges = node.remaining_charges + n_upd.charges_delta
                new_cd = n_upd.cooldown_set if n_upd.cooldown_set is not None else node.cooldown_remaining
                is_active = new_charges > 0 and new_cd <= 0
                if was_active != is_active and new_active_nodes is not None:
                    bucket = (int(node.position[0] // 20), int(node.position[1] // 20))
                    if not is_active:
                        if bucket in new_active_nodes:
                            new_list = [entry for entry in new_active_nodes[bucket] if entry[2] != str(n_id)]
                            if new_list:
                                new_active_nodes[bucket] = new_list
                            else:
                                new_active_nodes.pop(bucket, None)
                    else:
                        new_list = list(new_active_nodes.get(bucket, []))
                        new_list.append((node.position[0], node.position[1], str(n_id)))
                        new_active_nodes[bucket] = new_list
                new_nodes[n_id] = replace(node, remaining_charges=new_charges, cooldown_remaining=new_cd)
        for n in update.nodes_add:
            new_nodes[n.id] = n

        new_chests = dict(prior_state.chests)
        for c_id, c_upd in update.chest_updates.items():
            if c_id in new_chests:
                chest = new_chests[c_id]
                new_cd = c_upd.cooldown_set if c_upd.cooldown_set is not None else chest.cooldown_remaining
                new_items = c_upd.items_set if c_upd.items_set is not None else chest.items
                new_chests[c_id] = replace(chest, cooldown_remaining=new_cd, items=new_items)
        for c in update.chest_add_or_update:
            new_chests[c.id] = c

        new_buildings = dict(prior_state.buildings)
        for b_id, b_upd in update.building_updates.items():
            if b_id in new_buildings:
                bld = new_buildings[b_id]
                new_hp = max(0, min(bld.max_hp, bld.hp + b_upd.hp_delta))
                new_func = b_upd.functional_set if b_upd.functional_set is not None else bld.functional
                new_inv = bld.inventory
                if b_upd.inventory:
                    new_inv = InventoryService.apply_update(new_inv, b_upd.inventory)
                new_prc = b_upd.price_modifiers_set if b_upd.price_modifiers_set is not None else bld.price_modifiers
                is_death = bld.functional and new_hp == 0
                new_buildings[b_id] = replace(bld, hp=new_hp, functional=False if new_hp == 0 else new_func, inventory=new_inv, price_modifiers=new_prc)
                if is_death:
                    region = LegalityServiceV2.get_region_for_position(bld.position, prior_state)
                    if region and region.id in new_regions:
                        current_r = new_regions[region.id]
                        new_regions[region.id] = replace(current_r, trauma_score=current_r.trauma_score + 2.0)

        new_ground_items = dict(prior_state.ground_items)
        for i_id in update.ground_items_remove:
            new_ground_items.pop(i_id, None)
        for i in update.ground_items_add_or_update:
            new_ground_items[i.id] = i

        new_corpses = dict(prior_state.corpses)
        for c_id, corpse in list(new_corpses.items()):
            if tick >= corpse.decay_tick:
                new_corpses.pop(c_id, None)
        for c_id in update.corpses_remove:
            new_corpses.pop(c_id, None)
        for c in update.corpses_add_or_update:
            new_corpses[c.id] = c

        new_storage = dict(prior_state.home_storage)
        for s_id, s_upd in update.home_storage_updates.items():
            current_inv = new_storage.get(s_id) or InventoryComponent()
            new_storage[s_id] = InventoryService.apply_update(current_inv, s_upd)

        new_scars = dict(recovered_scars)
        for scar in update.scars_add_or_update:
            new_scars[scar.id] = scar
        for scar_id in update.scars_remove:
            new_scars.pop(scar_id, None)

        new_camps = dict(prior_state.camps)
        for c_id, c_upd in update.camp_updates.items():
            if c_id in new_camps:
                camp = new_camps[c_id]
                new_mat = camp.maturity + c_upd.maturity_delta
                new_act = c_upd.active_set if c_upd.active_set is not None else camp.active
                new_raid = c_upd.last_raid_tick_set if c_upd.last_raid_tick_set is not None else camp.last_raid_tick
                new_camps[c_id] = replace(camp, maturity=new_mat, active=new_act, last_raid_tick=new_raid)

        # 2. Fused Entity pass
        # ---------------------------------------------------------------------
        new_entities = prior_state.entities
        any_entity_changed = False
        if update.entities_remove:
            new_entities = dict(prior_state.entities)
            any_entity_changed = True
            for e_id in update.entities_remove:
                new_entities.pop(e_id, None)
        dirty_builder = DirtySetBuilder()
        
        cadence = cadence or SystemCadence(strategic_intelligence=1)
        is_bio_due = should_run(tick, None, cadence.biological)
        is_life_due = should_run(tick, None, cadence.lifecycle)
        
        region_list = list(new_regions.values())
        has_regions = len(region_list) > 0
        
        entity_updates = update.entity_updates

        for e_id, entity in prior_state.entities.items():
            u_ent = entity_updates.get(e_id)
            
            # --- A. Passive Logic ---
            changes = {}
            if passive and (entity.lifecycle.active or is_life_due):
                # Biological
                if is_bio_due:
                    bio = entity.biological
                    changes["biological"] = replace(bio, 
                        hunger=min(100.0, bio.hunger + 0.1 * cadence.biological),
                        sleep_debt=min(100.0, bio.sleep_debt + 0.05 * cadence.biological)
                    )
                
                # Lifecycle / Health Decay
                if is_life_due:
                    life = entity.lifecycle
                    new_age = life.age_ticks + 1
                    bio = changes.get("biological", entity.biological)
                    total_passive_dmg = 0
                    if bio.hunger >= 95.0: total_passive_dmg += 2
                    if bio.sleep_debt >= 98.0: total_passive_dmg += 1
                    
                    if total_passive_dmg > 0 or new_age != life.age_ticks:
                        comb = changes.get("combat", entity.combat)
                        new_hp = max(0, comb.hp - total_passive_dmg)
                        if new_hp != comb.hp:
                            changes["combat"] = replace(comb, hp=new_hp, alive=(new_hp > 0))
                        changes["lifecycle"] = replace(life, 
                            age_ticks=new_age,
                            active=(new_hp > 0 and new_age < life.max_age_ticks)
                        )
                
                # Stamina Regen
                stamina = entity.stamina
                if stamina.current < stamina.max_stamina:
                    is_resting = (entity.navigation.movement_mode == MovementMode.HOLD)
                    stam_regen = StaminaService.tick_regen(stamina, is_resting=is_resting)
                    if stam_regen > 0:
                        new_stam = min(stamina.max_stamina, stamina.current + stam_regen)
                        if new_stam != stamina.current:
                            changes["stamina"] = ApplyPath._fast_replace_stamina(stamina, new_stam)
                
                # --- World Dynamics (Hazard/Environment Impact) ---
                # Milestone 10: Fused hazard application
                region = None
                if has_regions:
                    from src.engine.spatial_query import SpatialQueryService
                    region = SpatialQueryService.get_region_at(prior_state, entity.navigation.position)
                
                if region:
                    nav = changes.get("navigation", entity.navigation)
                    if nav.region_id != region.id:
                        changes["navigation"] = replace(nav, region_id=region.id)

                    
                    # Suppression Readiness Drain
                    if region.suppression_active:
                        comb = changes.get("combat", entity.combat)
                        if comb.readiness > 0:
                            changes["combat"] = replace(comb, readiness=max(0.0, comb.readiness - 5.0))
                            
                    # Environmental Exposure (Fatigue)
                    exposure_mults = EnvironmentService.get_weather_multipliers(region)
                    if exposure_mults.get("stamina_drain", 1.0) > 1.0:
                        bio = changes.get("biological", entity.biological)
                        changes["biological"] = replace(bio, sleep_debt=min(100.0, bio.sleep_debt + 1.0))

                # Boredom
                strat = entity.strategic
                if strat.boredom:
                    new_boredom = {k: v - 0.05 for k, v in strat.boredom.items() if v > 0.051}
                    if len(new_boredom) != len(strat.boredom) or any(new_boredom[k] != strat.boredom[k] for k in new_boredom):
                        changes["strategic"] = replace(strat, boredom=shallow_freeze(new_boredom))
            
            # --- B. Intentional Logic ---
            if u_ent:
                changes = ApplyPath._apply_entity_update_to_dict(entity, u_ent, changes)
            
            # --- C. Region Maintenance (Optimized) ---
            if "navigation" in changes:
                nav = changes["navigation"]
                # Only check if position actually changed
                if nav.position != entity.navigation.position:
                    curr_reg_id = nav.region_id
                    is_in_region = False
                    
                    # 1. Check current region first (Temporal Locality)
                    if curr_reg_id and curr_reg_id in prior_state.regions:
                        r = prior_state.regions[curr_reg_id]
                        xb = r.bounds
                        if xb[0] <= nav.position[0] <= xb[2] and xb[1] <= nav.position[1] <= xb[3]:
                            is_in_region = True
                    
                    # 2. Only scan if we left the current region
                    if not is_in_region and has_regions:
                        # Reset region_id first
                        nav = replace(nav, region_id=None)
                        for r in region_list:
                            xb = r.bounds
                            if xb[0] <= nav.position[0] <= xb[2] and xb[1] <= nav.position[1] <= xb[3]:
                                nav = replace(nav, region_id=r.id)
                                break
                        changes["navigation"] = nav
            
            if not changes:
                continue
                
            # Apply merged changes
            new_ent = ApplyPath._fast_replace_entity(entity, changes)
            if not any_entity_changed:
                new_entities = dict(new_entities)
                any_entity_changed = True
            new_entities[e_id] = new_ent
            
            if entity.combat.alive and not new_ent.combat.alive:
                corpse_id = 1000000 + e_id
                new_corpses[corpse_id] = CorpseState(
                    id=corpse_id,
                    original_entity_id=e_id,
                    position=new_ent.navigation.position,
                    items=list(new_ent.inventory.items),
                    decay_tick=tick + 100,
                    generation=new_ent.lifecycle.generation
                )

            
            # Mark dirty efficiently
            dt = dirty_builder.mark_entity
            tags = []
            if "navigation" in changes: tags.append("movement")
            if "biological" in changes or "stamina" in changes: tags.append("biological")
            if "combat" in changes: tags.append("combat")
            if "strategic" in changes: tags.append("strategic")
            if "social" in changes: tags.append("social")
            if "lifecycle" in changes: tags.append("lifecycle")
            if "inventory" in changes: tags.append("inventory")
            if "attributes" in changes: tags.append("attribute")
            dt(e_id, tags)

        if update.entities_add:
            if not any_entity_changed:
                new_entities = dict(new_entities)
                any_entity_changed = True
            for ent in update.entities_add:
                new_entities[ent.id] = ent

        # Update audit dirty set if provided (Mutable object pattern)
        if audit_dirty_set is not None:
            final_dirty = dirty_builder.build()
            # If it's a list, append. If it's an object with update(), call it.
            if hasattr(audit_dirty_set, "update"):
                audit_dirty_set.update(final_dirty)
            elif isinstance(audit_dirty_set, list):
                audit_dirty_set.append(final_dirty)

        # 3. Final State Reconstruction
        # ---------------------------------------------------------------------
        new_rejections = dict(prior_state.rejection_registry)
        for k, v in update.rejections_delta.items():
            new_rejections[k] = new_rejections.get(k, 0) + v

        new_periodic = dict(prior_state.periodic_due_ticks)
        new_periodic.update(update.periodic_updates)

        new_work_debt = dict(prior_state.work_debt)
        for k, delta in update.work_debt_updates.items():
            new_work_debt[k] = max(0, new_work_debt.get(k, 0) + delta)

        if audit_mode:
            new_trace = list(prior_state.transaction_trace)
            new_trace.extend(update.transaction_trace)
        else:
            new_trace = []

        new_processed = list(prior_state.processed_transaction_ids)
        new_processed.extend(update.processed_transaction_ids)

        new_pressure = update.pressure_signals_set if update.pressure_signals_set is not None else prior_state.pressure_signals
        new_mode = update.current_mode_set if update.current_mode_set is not None else getattr(prior_state, "current_mode", 0)
        new_next_node = update.next_node_id_set if update.next_node_id_set is not None else getattr(prior_state, "next_node_id", 1000)
        new_next_entity = update.next_entity_id_set if update.next_entity_id_set is not None else getattr(prior_state, "next_entity_id", 1)
        new_maturity = update.maturity_set if update.maturity_set is not None else prior_state.maturity
        new_last_calamity = update.last_calamity_tick_set if update.last_calamity_tick_set is not None else prior_state.last_calamity_tick
        new_rng = update.rng_checkpoint if update.rng_checkpoint is not None else prior_state.rng_checkpoint
        new_global_resources = dict(prior_state.global_resources)
        for k, v in update.resource_updates.items():
            new_global_resources[k] = new_global_resources.get(k, 0.0) + v

        if grid_invalidated:
            new_active_nodes = None
        new_bldg_map = getattr(prior_state, "_building_map_cache", None) if not update.building_updates else None

        pass_hostile = getattr(prior_state, "_has_hostiles_or_dead_cache", None)
        if update.entities_add or any(u.combat is not None or (u.identity is not None and u.identity.faction_set is not None) for u in update.entity_updates.values()):
            pass_hostile = None
            
        pass_contracts = getattr(prior_state, "_has_contracts_cache", None)
        if update.entities_add or any(u.strategic is not None and (u.strategic.contracts_add_or_update or u.strategic.contracts_remove) for u in update.entity_updates.values()):
            pass_contracts = None

        m_cache = getattr(prior_state, "movement_cache", None)
        if m_cache is not None and update.dirty_set is not None:
            m_cache.invalidate_for_dirty(update.dirty_set)

        new_state = AuthoritativeState(
            tick=tick,
            seed=prior_state.seed,
            world_time=world_time,
            entities=new_entities,
            groups=new_groups,
            regions=new_regions,
            resource_nodes=new_nodes,
            buildings=new_buildings,
            chests=new_chests,
            ground_items=new_ground_items,
            corpses=new_corpses,
            camps=new_camps,
            local_scars=new_scars,
            global_resources=new_global_resources,
            town_tiles=prior_state.town_tiles,
            building_tiles=prior_state.building_tiles,
            terrain=prior_state.terrain,
            home_storage=new_storage,
            town_center=prior_state.town_center,
            periodic_due_ticks=new_periodic,
            work_debt=new_work_debt,
            movement_count=prior_state.movement_count,
            maturity=new_maturity,
            last_calamity_tick=new_last_calamity,
            blocked_tiles=prior_state.blocked_tiles,
            town_entity_ids=prior_state.town_entity_ids,
            rng_checkpoint=new_rng,
            transaction_trace=new_trace,
            rejection_registry=new_rejections,
            pressure_signals=new_pressure,
            current_mode=new_mode,
            processed_transaction_ids=new_processed,
            next_node_id=new_next_node,
            next_entity_id=new_next_entity,
            _active_nodes_grid=new_active_nodes,
            _building_map_cache=new_bldg_map,
            _has_hostiles_or_dead_cache=pass_hostile,
            _has_contracts_cache=pass_contracts,
            movement_cache=m_cache,
            world_indexes=getattr(prior_state, "world_indexes", None)
        )


        if not any_entity_changed and getattr(prior_state, "_readonly_entities_cache", None) is not None:
            object.__setattr__(new_state, "_readonly_entities_cache", prior_state._readonly_entities_cache)

        if audit_dirty_set is True and update.dirty_set is not None:
            new_state.validate_dirty_set(prior_state, update.dirty_set)

        return new_state

    @staticmethod
    def apply_partial(state: AuthoritativeState, update: StateUpdate, cadence: SystemCadence | None = None) -> AuthoritativeState:
        """Compatibility wrapper for apply_partial."""
        return ApplyPath.apply_generation(state, update, next_tick=state.tick, cadence=cadence, passive=False)

    @staticmethod
    def apply_passive(state: AuthoritativeState, cadence: SystemCadence | None = None) -> AuthoritativeState:
        """Compatibility wrapper for ActionRoutingPhase."""
        from src.core.updates import StateUpdate
        return ApplyPath.apply_generation(state, StateUpdate(), cadence=cadence)

    @staticmethod
    def _apply_entity_update(entity: EntityState, update: EntityUpdate) -> EntityState:
        """Compatibility wrapper for ActionRoutingPhase."""
        changes = ApplyPath._apply_entity_update_to_dict(entity, update, {})
        if not changes:
            return entity
        return ApplyPath._fast_replace_entity(entity, changes)

    @staticmethod
    def _apply_entity_update_to_dict(entity: EntityState, update: EntityUpdate, changes: dict) -> dict:
        """
        Authoritative mapping from EntityUpdate to changes dict.
        Merged v5 logic: handling all components in a single pass.
        """
        # Kind
        if update.kind_set is not None and update.kind_set != entity.kind:
            changes["kind"] = update.kind_set

        # Lifecycle
        new_lifecycle = changes.get("lifecycle", entity.lifecycle)
        if update.active is not None and update.active != new_lifecycle.active:
            new_lifecycle = replace(new_lifecycle, active=update.active)
        if update.lifecycle:
            u_life = update.lifecycle
            new_heirlooms = list(new_lifecycle.heirlooms)
            new_heirlooms.extend(u_life.heirlooms_add)
            new_lifecycle = replace(new_lifecycle,
                age_ticks=new_lifecycle.age_ticks + u_life.age_delta,
                generation=new_lifecycle.generation + u_life.generation_delta,
                is_permadeath=u_life.is_permadeath_set if u_life.is_permadeath_set is not None else new_lifecycle.is_permadeath,
                death_tick=u_life.death_tick_set if u_life.death_tick_set is not None else new_lifecycle.death_tick,
                death_reason=u_life.death_reason_set if u_life.death_reason_set is not None else new_lifecycle.death_reason,
                heir_entity_id=u_life.heir_entity_id_set if u_life.heir_entity_id_set is not None else new_lifecycle.heir_entity_id,
                heirlooms=tuple(new_heirlooms)
            )
        if new_lifecycle is not entity.lifecycle:
            changes["lifecycle"] = new_lifecycle

        # Biological
        if update.biological:
            u_bio = update.biological
            new_bio = changes.get("biological", entity.biological)
            changes["biological"] = replace(new_bio,
                sleep_debt=u_bio.sleep_debt_set if u_bio.sleep_debt_set is not None else max(0.0, min(100.0, new_bio.sleep_debt + u_bio.sleep_debt_delta)),
                hunger=u_bio.hunger_set if u_bio.hunger_set is not None else max(0.0, min(100.0, new_bio.hunger + u_bio.hunger_delta)),
                rest_pressure=new_bio.rest_pressure + u_bio.rest_pressure_delta,
                last_meal_tick=u_bio.last_meal_tick_set if u_bio.last_meal_tick_set is not None else new_bio.last_meal_tick,
                last_sleep_tick=u_bio.last_sleep_tick_set if u_bio.last_sleep_tick_set is not None else new_bio.last_sleep_tick,
                well_rested_until=u_bio.well_rested_until_set if u_bio.well_rested_until_set is not None else new_bio.well_rested_until
            )

        # Interaction
        if update.interaction:
            u_int = update.interaction
            if u_int.reset:
                changes["interaction"] = InteractionComponent()
            else:
                new_int = changes.get("interaction", entity.interaction)
                changes["interaction"] = replace(new_int,
                    target_node_id=u_int.target_node_id if u_int.target_node_id is not None else new_int.target_node_id,
                    progress=new_int.progress + u_int.progress_delta
                )

        # Identity
        if update.identity or update.group_id_set is not None or update.intent_results or update.property_updates:
            new_id = changes.get("identity", entity.identity)
            rl = new_id.role
            fac = new_id.faction
            rec = set(new_id.known_recipes)
            tgt = new_id.craft_target
            lvl = new_id.evolution_level
            ep = new_id.evolution_points
            vp = new_id.veterancy_points
            vrank = new_id.veterancy_rank
            ap = new_id.unspent_ap
            sk = set(new_id.learned_skills)
            tr = set(new_id.traits)
            brk = set(new_id.active_breakthroughs)
            cds = dict(new_id.cooldowns)
            
            if update.identity:
                u_id = update.identity
                if u_id.role_set is not None: rl = u_id.role_set
                if u_id.faction_set is not None: fac = u_id.faction_set
                rec |= set(u_id.recipes_learned)
                if u_id.craft_target is not None: tgt = u_id.craft_target
                if u_id.evolution_level_set is not None: lvl = u_id.evolution_level_set
                ep += u_id.evolution_points_delta
                if u_id.veterancy_points_delta != 0:
                    proc_id = VeterancyService.process_points(new_id, u_id.veterancy_points_delta)
                    vp = proc_id.veterancy_points
                    vrank = proc_id.veterancy_rank
                if u_id.unspent_ap_set is not None: ap = u_id.unspent_ap_set
                else: ap += u_id.unspent_ap_delta
                sk |= set(u_id.learned_skills)
                tr = (tr | set(u_id.traits_add)) - set(u_id.traits_remove)
                brk |= set(u_id.breakthroughs_add)
                cds.update(u_id.cooldown_updates)
                
            gid = new_id.group_id
            if update.group_id_set is not None:
                gid = None if update.group_id_set == -1 else update.group_id_set
            
            props = dict(new_id.properties)
            if update.property_updates:
                props.update(update.property_updates)
                
            intents = tuple(update.intent_results) if update.intent_results else new_id.latest_intent_results
            if not update.identity and update.group_id_set is None and not update.property_updates and update.intent_results:
                changes["identity"] = ApplyPath._fast_replace_identity(new_id, intents)
            else:
                changes["identity"] = replace(new_id, role=rl, faction=fac, known_recipes=frozenset(rec),
                                              craft_target=tgt, evolution_level=lvl, evolution_points=ep,
                                              veterancy_points=vp, veterancy_rank=vrank, unspent_ap=ap, learned_skills=frozenset(sk),
                                              traits=frozenset(tr), active_breakthroughs=frozenset(brk),
                                              cooldowns=ReadOnlyDict(cds), group_id=gid, properties=ReadOnlyDict(props),
                                              latest_intent_results=intents)

        # Navigation
        if update.navigation or update.new_position:
            u_nav = update.navigation
            new_nav = changes.get("navigation", entity.navigation)
            if u_nav:
                new_nav = replace(
                    new_nav,
                    target=u_nav.target_set if u_nav.target_set is not None else (None if u_nav.target_clear else new_nav.target),
                    movement_mode=u_nav.movement_mode_set if u_nav.movement_mode_set is not None else new_nav.movement_mode,
                    path=u_nav.path_set if u_nav.path_set is not None else (None if u_nav.clear_path else new_nav.path),
                    moved_recently=u_nav.moved_recently_set if u_nav.moved_recently_set is not None else new_nav.moved_recently,
                    last_failure_reason=u_nav.failure_reason if u_nav.failure_reason is not None else new_nav.last_failure_reason,
                    region_id=u_nav.region_id_set if u_nav.region_id_set is not None else new_nav.region_id,
                    wait_count=new_nav.wait_count + u_nav.wait_count_delta,
                    oscillation_count=new_nav.oscillation_count + u_nav.oscillation_count_delta,
                    last_position=u_nav.last_position_set if u_nav.last_position_set is not None else new_nav.last_position
                )
            if update.new_position:
                if update.new_position != entity.navigation.position:
                    new_nav = ApplyPath._fast_replace_navigation(new_nav, update.new_position, None)
            
            if new_nav is not entity.navigation:
                changes["navigation"] = new_nav

        # Combat
        u_com = update.combat
        if u_com or update.readiness_delta != 0.0:
            new_combat = changes.get("combat", entity.combat)
            if u_com:
                new_hp = max(0, new_combat.hp + u_com.hp_delta)
                new_combat = replace(new_combat, 
                    hp=new_hp, 
                    max_hp=new_combat.max_hp + u_com.max_hp_delta,
                    alive=(new_hp > 0) if u_com.alive_set is None else u_com.alive_set,
                    atk=new_combat.atk + u_com.atk_delta,
                    def_stat=new_combat.def_stat + u_com.def_delta,
                    speed=new_combat.speed + u_com.speed_delta,
                    latest_result=u_com
                )
            if update.readiness_delta != 0.0:
                new_combat = replace(new_combat, readiness=max(0.0, min(100.0, new_combat.readiness + update.readiness_delta)))
            
            if new_combat is not entity.combat:
                changes["combat"] = new_combat

        # Stamina
        u_stam = update.stamina_update
        if u_stam:
            new_stamina = changes.get("stamina", entity.stamina)
            new_stamina = ApplyPath._fast_replace_stamina(
                new_stamina,
                max(0.0, min(u_stam.max_stamina_set or new_stamina.max_stamina, (u_stam.current_set if u_stam.current_set is not None else new_stamina.current) + u_stam.current_delta)),
                u_stam.max_stamina_set
            )
            if new_stamina is not entity.stamina:
                changes["stamina"] = new_stamina

        # Inventory
        if update.inventory or update.resource_transfers:
            new_inv = changes.get("inventory", entity.inventory)
            if update.inventory:
                new_inv = InventoryService.apply_update(new_inv, update.inventory)
            if update.resource_transfers:
                for transfer in update.resource_transfers:
                    new_inv = InventoryService.apply_transfer(new_inv, transfer)
            
            if new_inv is not entity.inventory:
                changes["inventory"] = new_inv

        # Equipment
        if update.equipment:
            u_eq = update.equipment
            new_eq = changes.get("equipment", entity.equipment)
            new_slots = dict(new_eq.slots)
            new_slots.update(u_eq.slot_updates)
            
            new_durability = dict(new_eq.durability)
            for slot, delta in u_eq.durability_delta.items():
                new_durability[slot] = max(0.0, min(100.0, new_durability.get(slot, 100.0) + delta))
            for slot, val in u_eq.durability_set.items():
                new_durability[slot] = max(0.0, min(100.0, val))
                
            changes["equipment"] = replace(new_eq, slots=ReadOnlyDict(new_slots), durability=ReadOnlyDict(new_durability))

        # Strategic
        if update.strategic:
            u_strat = update.strategic
            new_strat = changes.get("strategic", entity.strategic)
            
            def merge_dict(current_dict, add_list, remove_list):
                if not add_list and not remove_list:
                    return current_dict
                res = dict(current_dict)
                for item in add_list:
                    res[item.id] = item
                for item_id in remove_list:
                    res.pop(item_id, None)
                return res

            nb = merge_dict(new_strat.blockers, u_strat.blockers_add_or_update, u_strat.blockers_remove)
            nl = merge_dict(new_strat.leads, u_strat.leads_add_or_update, u_strat.leads_remove)
            nd = merge_dict(new_strat.directives, u_strat.directives_add_or_update, u_strat.directives_remove)
            np = merge_dict(new_strat.projects, u_strat.projects_add_or_update, u_strat.projects_remove)
            nc = merge_dict(new_strat.concerns, u_strat.concerns_add_or_update, u_strat.concerns_remove)
            ncz = merge_dict(new_strat.candidate_zones, u_strat.candidate_zones_add_or_update, u_strat.candidate_zones_remove)
            nh = merge_dict(new_strat.hypotheses, u_strat.hypotheses_add_or_update, u_strat.hypotheses_remove)
            ncon = merge_dict(new_strat.contracts, u_strat.contracts_add_or_update, u_strat.contracts_remove)
            ntp = list(new_strat.turning_points) + u_strat.turning_points_add
            
            max_tps = getattr(new_strat.profile, "max_turning_points", 20)
            if len(ntp) > max_tps:
                ntp = ntp[-max_tps:]
                
            nbor = new_strat.boredom
            if u_strat.boredom_delta:
                nbor = dict(nbor)
                for k, d in u_strat.boredom_delta.items():
                    nbor[k] = nbor.get(k, 0.0) + d

            ntrust = new_strat.source_trust
            if u_strat.source_trust_updates:
                ntrust = dict(ntrust)
                for entry in u_strat.source_trust_updates:
                    ntrust[entry.entity_id] = entry
                    
            new_strat = replace(new_strat,
                blockers=shallow_freeze(nb), leads=shallow_freeze(nl), directives=shallow_freeze(nd),
                projects=shallow_freeze(np), concerns=shallow_freeze(nc), candidate_zones=shallow_freeze(ncz),
                hypotheses=shallow_freeze(nh), contracts=shallow_freeze(ncon), turning_points=tuple(ntp),
                boredom=shallow_freeze(nbor), source_trust=shallow_freeze(ntrust),
                current_project_id=u_strat.current_project_id_set if u_strat.current_project_id_set is not None else new_strat.current_project_id,
                current_objective_id=u_strat.current_objective_id_set if u_strat.current_objective_id_set is not None else new_strat.current_objective_id
            )
            changes["strategic"] = new_strat

        # Quest
        if update.quest:
            new_strat = changes.get("strategic", entity.strategic)
            np = dict(new_strat.projects)
            q_updates = update.quest.multi_updates if update.quest.multi_updates else [update.quest]
            for qu in q_updates:
                q_id = qu.quest_id
                project = np.get(q_id)
                if project and isinstance(project, QuestState):
                    updated_quest = QuestService.add_progress(project, qu.progress_delta)
                    if qu.status_set is not None:
                        updated_quest = replace(updated_quest, quest_status=qu.status_set)
                    np[q_id] = updated_quest
            changes["strategic"] = replace(new_strat, projects=shallow_freeze(np))

        # Social
        if update.social:
            changes["social"] = RelationshipService.process_update(changes.get("social", entity.social), update.social)

        # Task
        if update.task:
            new_task = replace(entity.task, 
                work_kind=update.task.work_kind_set if update.task.work_kind_set is not None else entity.task.work_kind,
                payload=update.task.payload_set if update.task.payload_set is not None else entity.task.payload
            )
            if new_task != entity.task:
                changes["task"] = new_task

        # Attributes
        if update.attributes:
            u_att = update.attributes
            new_att = changes.get("attributes", entity.attributes)
            changes["attributes"] = replace(new_att,
                strength=min(100, new_att.strength + u_att.strength_delta),
                agility=min(100, new_att.agility + u_att.agility_delta),
                vitality=min(100, new_att.vitality + u_att.vitality_delta),
                endurance=min(100, new_att.endurance + u_att.endurance_delta),
                intelligence=min(100, new_att.intelligence + u_att.intelligence_delta),
                spirit=min(100, new_att.spirit + u_att.spirit_delta),
                wisdom=min(100, new_att.wisdom + u_att.wisdom_delta),
                perception=min(100, new_att.perception + u_att.perception_delta),
                charisma=min(100, new_att.charisma + u_att.charisma_delta)
            )

        # Reward (Leveling)
        if update.reward and update.reward.xp_gain > 0:
            new_id = changes.get("identity", entity.identity)
            prog_upd = LevelingService.process_progression(new_id, update.reward.xp_gain)
            changes["identity"] = replace(new_id,
                evolution_level=prog_upd.evolution_level_set if prog_upd.evolution_level_set is not None else new_id.evolution_level,
                evolution_points=new_id.evolution_points + prog_upd.evolution_points_delta,
                unspent_ap=new_id.unspent_ap + prog_upd.unspent_ap_delta
            )

        # Wounds / Scars
        new_com = changes.get("combat", entity.combat)
        new_wounds = list(new_com.wounds)
        new_scars = list(new_com.scars)
        wounds_dirty = False
        if update.wound_update:
            wounds_dirty = True
            new_wounds.extend(update.wound_update.wounds_add)
            new_scars.extend(update.wound_update.scars_add)
            if update.wound_update.wounds_heal:
                new_wounds = [w if w.id not in update.wound_update.wounds_heal else replace(w, healed=True) for w in new_wounds]

        if wounds_dirty or new_wounds != list(new_com.wounds) or new_scars != list(new_com.scars):
            new_com = replace(new_com, wounds=tuple(new_wounds), scars=tuple(new_scars))
            changes["combat"] = new_com

        # PH8 Derived Stats Re-calc
        curr_id = changes.get("identity", entity.identity)
        stats_dirty = (
            update.attributes is not None or 
            update.equipment is not None or 
            (update.identity is not None and (
                update.identity.learned_skills or 
                update.identity.traits_add or 
                update.identity.traits_remove or
                (update.identity.evolution_level_set is not None and update.identity.evolution_level_set > entity.identity.evolution_level)
            )) or
            (curr_id.evolution_level > entity.identity.evolution_level) or
            update.wound_update is not None
        )

        if stats_dirty:
            new_att = changes.get("attributes", entity.attributes)
            new_eq = changes.get("equipment", entity.equipment)
            new_id = curr_id
            new_com = changes.get("combat", entity.combat)
            
            derived = SkillScalingService.get_effective_stats(
                new_att, new_eq,
                wounds=new_com.wounds, scars=new_com.scars,
                learned_skills=new_id.learned_skills,
                traits=new_id.traits,
                current_role=new_com.tactical_role
            )
            
            new_com = replace(new_com,
                max_hp=derived["max_hp"],
                atk=derived["atk"],
                def_stat=derived["def_stat"],
                evasion=derived["evasion"],
                move_cost=derived.get("move_cost", new_com.move_cost),
                range=derived.get("range", new_com.range),
                tactical_role=derived.get("tactical_role", new_com.tactical_role)
            )
            
            if (update.identity and update.identity.evolution_level_set is not None) or (update.reward and update.reward.xp_gain > 0 and new_id.evolution_level > entity.identity.evolution_level):
                new_com = replace(new_com, hp=derived["max_hp"])
                new_stam = changes.get("stamina", entity.stamina)
                changes["stamina"] = replace(new_stam, current=new_stam.max_stamina)
            else:
                if new_com.hp > new_com.max_hp:
                    new_com = replace(new_com, hp=new_com.max_hp)
            
            changes["combat"] = new_com

        return changes

    @staticmethod
    def _fast_replace_identity(id_comp: IdentityComponent, latest_intent_results: tuple) -> IdentityComponent:
        res = object.__new__(IdentityComponent)
        object.__setattr__(res, "role", id_comp.role)
        object.__setattr__(res, "faction", id_comp.faction)
        object.__setattr__(res, "known_recipes", id_comp.known_recipes)
        object.__setattr__(res, "craft_target", id_comp.craft_target)
        object.__setattr__(res, "evolution_level", id_comp.evolution_level)
        object.__setattr__(res, "evolution_points", id_comp.evolution_points)
        object.__setattr__(res, "veterancy_points", id_comp.veterancy_points)
        object.__setattr__(res, "veterancy_rank", id_comp.veterancy_rank)
        object.__setattr__(res, "unspent_ap", id_comp.unspent_ap)
        object.__setattr__(res, "class_id", id_comp.class_id)
        object.__setattr__(res, "learned_skills", id_comp.learned_skills)
        object.__setattr__(res, "traits", id_comp.traits)
        object.__setattr__(res, "active_breakthroughs", id_comp.active_breakthroughs)
        object.__setattr__(res, "cooldowns", id_comp.cooldowns)
        object.__setattr__(res, "personality", id_comp.personality)
        object.__setattr__(res, "life_stage", id_comp.life_stage)
        object.__setattr__(res, "group_id", id_comp.group_id)
        object.__setattr__(res, "properties", id_comp.properties)
        object.__setattr__(res, "latest_intent_results", latest_intent_results)
        object.__setattr__(res, "_canonical_cache", None)
        return res

    @staticmethod
    def _fast_replace_navigation(nav: NavigationComponent, position: tuple[float, float], region_id: str | None = None) -> NavigationComponent:
        res = object.__new__(NavigationComponent)
        object.__setattr__(res, "position", position)
        object.__setattr__(res, "target", nav.target)
        object.__setattr__(res, "path", nav.path)
        object.__setattr__(res, "moved_recently", nav.moved_recently)
        object.__setattr__(res, "movement_mode", nav.movement_mode)
        object.__setattr__(res, "last_failure_reason", nav.last_failure_reason)
        object.__setattr__(res, "wait_count", nav.wait_count)
        object.__setattr__(res, "oscillation_count", nav.oscillation_count)
        object.__setattr__(res, "last_position", nav.last_position)
        object.__setattr__(res, "home_position", nav.home_position)
        object.__setattr__(res, "leash_radius", nav.leash_radius)
        object.__setattr__(res, "region_id", region_id)
        object.__setattr__(res, "chase_ticks", nav.chase_ticks)
        object.__setattr__(res, "max_chase_ticks", nav.max_chase_ticks)
        object.__setattr__(res, "returning_home", nav.returning_home)
        return res

    @staticmethod
    def _fast_replace_stamina(stam: StaminaComponent, current: float, max_stamina: float | None = None) -> StaminaComponent:
        res = object.__new__(StaminaComponent)
        object.__setattr__(res, "current", current)
        object.__setattr__(res, "max_stamina", max_stamina if max_stamina is not None else stam.max_stamina)
        object.__setattr__(res, "regen_rate", stam.regen_rate)
        object.__setattr__(res, "rest_regen_rate", stam.rest_regen_rate)
        object.__setattr__(res, "exhaustion_threshold", stam.exhaustion_threshold)
        object.__setattr__(res, "exhaustion_penalty", stam.exhaustion_penalty)
        object.__setattr__(res, "_canonical_cache", None)
        return res

    @staticmethod
    def _fast_replace_entity(entity: EntityState, changes: dict) -> EntityState:
        """
        Low-level reconstruction bypasses frozen dataclass __init__ overhead.
        """
        res = object.__new__(EntityState)
        object.__setattr__(res, "id", entity.id)
        object.__setattr__(res, "kind", changes.get("kind", entity.kind))
        object.__setattr__(res, "interaction", changes.get("interaction", entity.interaction))
        object.__setattr__(res, "identity", changes.get("identity", entity.identity))
        object.__setattr__(res, "attributes", changes.get("attributes", entity.attributes))
        object.__setattr__(res, "inventory", changes.get("inventory", entity.inventory))
        object.__setattr__(res, "strategic", changes.get("strategic", entity.strategic))
        object.__setattr__(res, "social", changes.get("social", entity.social))
        object.__setattr__(res, "biological", changes.get("biological", entity.biological))
        object.__setattr__(res, "lifecycle", changes.get("lifecycle", entity.lifecycle))
        object.__setattr__(res, "aptitude", changes.get("aptitude", entity.aptitude))
        object.__setattr__(res, "combat", changes.get("combat", entity.combat))
        object.__setattr__(res, "equipment", changes.get("equipment", entity.equipment))
        object.__setattr__(res, "navigation", changes.get("navigation", entity.navigation))
        object.__setattr__(res, "task", changes.get("task", entity.task))
        object.__setattr__(res, "stamina", changes.get("stamina", entity.stamina))
        
        # Clear transient caches
        object.__setattr__(res, "_readonly_cache", res)
        object.__setattr__(res, "_spatial_grid_cache", None)
        object.__setattr__(res, "_canonical_cache", None)
        return res
