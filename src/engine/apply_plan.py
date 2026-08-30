# Compliance IDs: PERF-014, PERF-015
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, CorpseState, ResourceNodeState, ChestState, GroundItemState, BuildingState, CampState, LocalScarState, GroupRecord
    from src.core.updates import StateUpdate, EntityUpdate
    from src.engine.cadence import SystemCadence

from src.core.enums import ReasonCode
from src.core.state import CorpseState
from src.engine.cadence import should_run
from src.world.environment import EnvironmentService
from src.world.consequences import RegionalConsequenceService

@dataclass(slots=True)
class CacheInvalidationHints:
    invalidate_movement_cache: bool = False
    invalidate_read_model: bool = False
    invalidate_world_indexes: bool = False


@dataclass(slots=True)
class ApplyPlan:
    """
    A precomputed execution plan for applying updates.
    Milestone 14: ApplyPath Structural Redesign.
    Precomputes exactly what state changes need to occur to minimize conditional branching during execution.
    """
    # Core precomputed change dictionaries
    entity_component_changes: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    world_collection_changes: Dict[str, Any] = field(default_factory=dict)
    resource_transfers: List[Any] = field(default_factory=list)
    lifecycle_changes: Dict[int, Any] = field(default_factory=dict)
    transaction_trace_changes: List[str] = field(default_factory=list)
    cache_invalidation_hints: CacheInvalidationHints = field(default_factory=CacheInvalidationHints)
    
    # Execution helper structures for lightning-fast state application
    entities_to_replace: Set[int] = field(default_factory=set)
    components_to_replace: Dict[int, Set[str]] = field(default_factory=dict)
    collections_to_copy: Set[str] = field(default_factory=set)
    new_corpses: List[CorpseState] = field(default_factory=list)
    dirty_tags_by_entity: Dict[int, List[str]] = field(default_factory=dict)
    grid_invalidated: bool = False


class ApplyPlanBuilder:
    """
    Constructs a structured ApplyPlan from an authoritative StateUpdate.
    Pre-evaluates domain changes, collection copies, and cache invalidation policies.
    """

    @staticmethod
    def build_plan(
        prior_state: AuthoritativeState,
        update: StateUpdate,
        next_tick: int,
        cadence: SystemCadence,
        passive: bool,
        compute_entity_changes_fn: Any
    ) -> ApplyPlan:
        """
        Builds the comprehensive execution plan.
        """
        plan = ApplyPlan()
        tick = next_tick
        
        # 1. Determine Cache Invalidation Hints
        plan.cache_invalidation_hints = CacheInvalidationHints(
            invalidate_movement_cache=update.dirty_set is not None,
            invalidate_read_model=update.dirty_set is not None and bool(getattr(update.dirty_set, "all_dirty_entities", set())),
            invalidate_world_indexes=bool(update.entities_add or update.entities_remove or update.nodes_add or update.node_updates)
        )
        
        # 2. Determine Collections to Copy
        cols = plan.collections_to_copy
        if update.groups_remove or update.groups_add_or_update: cols.add("groups")
        if update.world_updates: cols.add("regions")
        if update.node_updates or update.nodes_add: cols.add("nodes")
        if update.chest_updates or update.chest_add_or_update: cols.add("chests")
        if update.building_updates: cols.add("buildings")
        if update.ground_items_remove or update.ground_items_add_or_update: cols.add("ground_items")
        if update.corpses_remove or update.corpses_add_or_update: cols.add("corpses")
        if update.home_storage_updates: cols.add("home_storage")
        if update.scars_add_or_update or update.scars_remove: cols.add("scars")
        if update.camp_updates: cols.add("camps")
        if update.entities_remove or update.entities_add or update.entity_updates: cols.add("entities")
        
        # 3. Precompute Non-Entity World Collection Changes
        # Groups
        new_groups = dict(prior_state.groups) if "groups" in cols else prior_state.groups
        if "groups" in cols:
            for g_id in update.groups_remove:
                new_groups.pop(g_id, None)
            for g in update.groups_add_or_update:
                new_groups[g.id] = g
        plan.world_collection_changes["groups"] = new_groups

        # Regions & Recovery
        recovered_regions, recovered_scars = RegionalConsequenceService.process_recovery(prior_state)
        if recovered_regions != prior_state.regions:
            cols.add("regions")
        if recovered_scars != prior_state.local_scars:
            cols.add("scars")
            
        new_regions = dict(recovered_regions) if "regions" in cols else prior_state.regions
        if "regions" in cols:
            for r_id, r_upd in update.world_updates.items():
                if r_id in new_regions:
                    reg = new_regions[r_id]
                    from src.engine.apply import replace
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
                    pop_cohorts = r_upd.population_cohorts_set if r_upd.population_cohorts_set is not None else reg.population_cohorts
                    # E53Cb: siege mechanics — clamp service_availability, apply siege_state mutations
                    svc_avail = max(0.0, min(1.0, reg.service_availability + r_upd.service_availability_delta))
                    if r_upd.siege_state_clear:
                        siege = None
                    elif r_upd.siege_state_set is not None:
                        siege = r_upd.siege_state_set
                    else:
                        siege = reg.siege_state
                    if siege is not None and r_upd.siege_progress_delta != 0.0:
                        new_progress = max(0.0, min(1.0, siege.siege_progress + r_upd.siege_progress_delta))
                        siege = replace(siege, siege_progress=new_progress)
                    new_regions[r_id] = replace(reg, hazard_level=haz, suppression_active=sup, calamity_intensity=cal,
                                                trauma_score=tra, retaliation_pressure=ret, influence=inf,
                                                owner_faction_id=own, kind=knd, weather=wth, active_modifiers=mods,
                                                price_modifiers=prc, population_cohorts=pop_cohorts,
                                                siege_state=siege, service_availability=svc_avail)
        plan.world_collection_changes["regions"] = new_regions

        # Nodes
        plan.grid_invalidated = bool(update.nodes_add)
        new_nodes = dict(prior_state.resource_nodes) if "nodes" in cols else prior_state.resource_nodes
        new_active_nodes = getattr(prior_state, "_active_nodes_grid", None)
        if new_active_nodes is not None and not plan.grid_invalidated:
            new_active_nodes = dict(new_active_nodes)
        else:
            new_active_nodes = None

        if "nodes" in cols:
            from src.engine.apply import replace
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
        plan.world_collection_changes["nodes"] = new_nodes
        plan.world_collection_changes["_active_nodes_grid"] = new_active_nodes

        # Chests
        new_chests = dict(prior_state.chests) if "chests" in cols else prior_state.chests
        if "chests" in cols:
            from src.engine.apply import replace
            for c_id, c_upd in update.chest_updates.items():
                if c_id in new_chests:
                    chest = new_chests[c_id]
                    new_cd = c_upd.cooldown_set if c_upd.cooldown_set is not None else chest.cooldown_remaining
                    new_items = c_upd.items_set if c_upd.items_set is not None else chest.items
                    new_chests[c_id] = replace(chest, cooldown_remaining=new_cd, items=new_items)
            for c in update.chest_add_or_update:
                new_chests[c.id] = c
        plan.world_collection_changes["chests"] = new_chests

        # Buildings
        new_buildings = dict(prior_state.buildings) if "buildings" in cols else prior_state.buildings
        if "buildings" in cols:
            from src.engine.apply import replace
            from src.core.inventory import InventoryService
            from src.engine.legality import LegalityServiceV2
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
                        cols.add("regions")
                        if plan.world_collection_changes["regions"] is prior_state.regions:
                            plan.world_collection_changes["regions"] = dict(prior_state.regions)
                        region = LegalityServiceV2.get_region_for_position(bld.position, prior_state)
                        if region and region.id in plan.world_collection_changes["regions"]:
                            current_r = plan.world_collection_changes["regions"][region.id]
                            plan.world_collection_changes["regions"][region.id] = replace(current_r, trauma_score=current_r.trauma_score + 2.0)
        plan.world_collection_changes["buildings"] = new_buildings

        # Ground Items
        new_ground_items = dict(prior_state.ground_items) if "ground_items" in cols else prior_state.ground_items
        if "ground_items" in cols:
            for i_id in update.ground_items_remove:
                new_ground_items.pop(i_id, None)
            for i in update.ground_items_add_or_update:
                new_ground_items[i.id] = i
        plan.world_collection_changes["ground_items"] = new_ground_items

        # Corpses & Decay
        new_corpses = dict(prior_state.corpses)
        for c_id, corpse in list(new_corpses.items()):
            if tick >= corpse.decay_tick:
                new_corpses.pop(c_id, None)
                cols.add("corpses")
        if "corpses" in cols or update.corpses_remove or update.corpses_add_or_update:
            cols.add("corpses")
            for c_id in update.corpses_remove:
                new_corpses.pop(c_id, None)
            for c in update.corpses_add_or_update:
                new_corpses[c.id] = c
        plan.world_collection_changes["corpses"] = new_corpses

        # Home Storage
        new_storage = dict(prior_state.home_storage) if "home_storage" in cols else prior_state.home_storage
        if "home_storage" in cols:
            from src.core.inventory import InventoryService
            from src.core.state import InventoryComponent
            for s_id, s_upd in update.home_storage_updates.items():
                current_inv = new_storage.get(s_id) or InventoryComponent()
                new_storage[s_id] = InventoryService.apply_update(current_inv, s_upd)
        plan.world_collection_changes["home_storage"] = new_storage

        # Scars
        new_scars = dict(recovered_scars) if "scars" in cols else prior_state.local_scars
        if "scars" in cols:
            for scar in update.scars_add_or_update:
                new_scars[scar.id] = scar
            for scar_id in update.scars_remove:
                new_scars.pop(scar_id, None)
        plan.world_collection_changes["scars"] = new_scars

        # Camps
        new_camps = dict(prior_state.camps) if "camps" in cols else prior_state.camps
        if "camps" in cols:
            from src.engine.apply import replace
            for c_id, c_upd in update.camp_updates.items():
                if c_id in new_camps:
                    camp = new_camps[c_id]
                    new_mat = camp.maturity + c_upd.maturity_delta
                    new_act = c_upd.active_set if c_upd.active_set is not None else camp.active
                    new_raid = c_upd.last_raid_tick_set if c_upd.last_raid_tick_set is not None else camp.last_raid_tick
                    new_camps[c_id] = replace(camp, maturity=new_mat, active=new_act, last_raid_tick=new_raid)
        plan.world_collection_changes["camps"] = new_camps

        # 4. Precompute Entity Changes
        # Narrow down entity candidates to only those potentially modified
        is_bio_due = should_run(tick, None, cadence.biological)
        is_life_due = should_run(tick, None, cadence.lifecycle)
        region_list = list(plan.world_collection_changes["regions"].values())
        has_regions = len(region_list) > 0
        
        candidates: Set[int] = set(update.entity_updates.keys())
        if passive:
            if is_bio_due or is_life_due:
                candidates.update(prior_state.entities.keys())
            else:
                # Only check entities needing stamina regen or in active hazard regions or with boredom
                hazard_active = False
                if has_regions:
                    hazard_active = any(r.suppression_active or EnvironmentService.get_weather_multipliers(r).get("stamina_drain", 1.0) > 1.0 for r in region_list)
                if hazard_active:
                    candidates.update(prior_state.entities.keys())
                else:
                    for e_id, ent in prior_state.entities.items():
                        if ent.stamina.current < ent.stamina.max_stamina:
                            candidates.add(e_id)
                        elif ent.strategic.boredom and any(v > 0.051 for v in ent.strategic.boredom.values()):
                            candidates.add(e_id)

        entity_updates = update.entity_updates
        for e_id in candidates:
            if e_id not in prior_state.entities:
                continue
            entity = prior_state.entities[e_id]
            u_ent = entity_updates.get(e_id)
            
            changes = compute_entity_changes_fn(entity, u_ent, tick, cadence, passive, has_regions, region_list, prior_state)
            if not changes:
                continue
                
            plan.entities_to_replace.add(e_id)
            plan.entity_component_changes[e_id] = changes
            plan.components_to_replace[e_id] = set(changes.keys())
            cols.add("entities")
            
            # Precompute death corpse creation
            comb = changes.get("combat", entity.combat)
            if entity.combat.alive and not comb.alive:
                corpse_id = 1000000 + e_id
                nav = changes.get("navigation", entity.navigation)
                inv = changes.get("inventory", entity.inventory)
                life = changes.get("lifecycle", entity.lifecycle)
                corpse = CorpseState(
                    id=corpse_id,
                    original_entity_id=e_id,
                    position=nav.position,
                    items=list(inv.items),
                    decay_tick=tick + 100,
                    generation=life.generation
                )
                plan.new_corpses.append(corpse)
                cols.add("corpses")
                
            # Precompute dirty tags
            tags = []
            if "navigation" in changes: tags.append("movement")
            if "biological" in changes or "stamina" in changes: tags.append("biological")
            if "combat" in changes: tags.append("combat")
            if "strategic" in changes: tags.append("strategic")
            if "social" in changes: tags.append("social")
            if "lifecycle" in changes: tags.append("lifecycle")
            if "inventory" in changes: tags.append("inventory")
            if "attributes" in changes: tags.append("attribute")
            if "identity" in changes: tags.append("identity")
            plan.dirty_tags_by_entity[e_id] = tags

        return plan
