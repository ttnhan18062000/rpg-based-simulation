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
    IdentityComponent, AptitudeComponent, EquipmentComponent, SocialComponent, ReadOnlyDict,
    FactionState
)
from src.core.quests import QuestState, QuestStatus
from src.core.models.quests import QuestOpportunity, QuestOpportunityStatus
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
    def _compute_entity_changes(
        entity: EntityState,
        u_ent: Optional[EntityUpdate],
        tick: int,
        cadence: SystemCadence,
        passive: bool,
        has_regions: bool,
        region_list: List[Any],
        prior_state: AuthoritativeState
    ) -> dict:
        changes = {}
        is_bio_due = should_run(tick, None, cadence.biological)
        is_life_due = should_run(tick, None, cadence.lifecycle)
        
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
            if nav.position != entity.navigation.position:
                curr_reg_id = nav.region_id
                is_in_region = False
                if curr_reg_id and curr_reg_id in prior_state.regions:
                    r = prior_state.regions[curr_reg_id]
                    xb = r.bounds
                    if xb[0] <= nav.position[0] <= xb[2] and xb[1] <= nav.position[1] <= xb[3]:
                        is_in_region = True
                if not is_in_region and has_regions:
                    nav = replace(nav, region_id=None)
                    for r in region_list:
                        xb = r.bounds
                        if xb[0] <= nav.position[0] <= xb[2] and xb[1] <= nav.position[1] <= xb[3]:
                            nav = replace(nav, region_id=r.id)
                            break
                    changes["navigation"] = nav
        
        return changes

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
        Milestone 14: Precomputes ApplyPlan and executes state deltas directly.
        """
        tick = next_tick if next_tick is not None else prior_state.tick + 1
        world_time = next_world_time if next_world_time is not None else prior_state.world_time
        cadence = cadence or SystemCadence(strategic_intelligence=1)
        
        # 1. Build Execution Plan
        # ---------------------------------------------------------------------
        from src.engine.apply_plan import ApplyPlanBuilder
        plan = ApplyPlanBuilder.build_plan(prior_state, update, tick, cadence, passive, ApplyPath._compute_entity_changes)
        
        new_groups = plan.world_collection_changes["groups"]
        new_regions = plan.world_collection_changes["regions"]
        new_nodes = plan.world_collection_changes["nodes"]
        new_active_nodes = plan.world_collection_changes["_active_nodes_grid"]
        new_chests = plan.world_collection_changes["chests"]
        new_buildings = plan.world_collection_changes["buildings"]
        new_ground_items = plan.world_collection_changes["ground_items"]
        new_corpses = plan.world_collection_changes["corpses"]
        new_storage = plan.world_collection_changes["home_storage"]
        new_scars = plan.world_collection_changes["scars"]
        new_camps = plan.world_collection_changes["camps"]

        # 2. Reconstruct Modified Entities
        # ---------------------------------------------------------------------
        new_entities = prior_state.entities
        any_entity_changed = False
        if update.entities_remove:
            new_entities = dict(prior_state.entities)
            any_entity_changed = True
            for e_id in update.entities_remove:
                new_entities.pop(e_id, None)

        dirty_builder = DirtySetBuilder()
        if plan.entities_to_replace:
            if not any_entity_changed:
                new_entities = dict(new_entities)
                any_entity_changed = True
            for e_id in plan.entities_to_replace:
                entity = prior_state.entities[e_id]
                changes = plan.entity_component_changes[e_id]
                new_ent = ApplyPath._fast_replace_entity(entity, changes)
                new_entities[e_id] = new_ent

        if plan.new_corpses:
            if "corpses" not in plan.collections_to_copy:
                new_corpses = dict(new_corpses)
                plan.collections_to_copy.add("corpses")
            for corpse in plan.new_corpses:
                new_corpses[corpse.id] = corpse

        for e_id, tags in plan.dirty_tags_by_entity.items():
            dirty_builder.mark_entity(e_id, tags)

        if update.entities_add:
            if not any_entity_changed:
                new_entities = dict(new_entities)
                any_entity_changed = True
            for ent in update.entities_add:
                new_entities[ent.id] = ent

        if audit_dirty_set is not None:
            final_dirty = dirty_builder.build()
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

        grid_invalidated = plan.grid_invalidated
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
        if m_cache is not None and plan.cache_invalidation_hints.invalidate_movement_cache:
            if update.dirty_set is not None:
                m_cache.invalidate_for_dirty(update.dirty_set)

        new_movement_count = sum(1 for u in update.entity_updates.values() if u.moved_this_tick)

        WORLD_EVENT_WINDOW = 500
        prior_events = getattr(prior_state, "recent_world_events", [])
        merged_events = prior_events + update.world_events_add
        new_recent_world_events = merged_events[-WORLD_EVENT_WINDOW:]

        new_quest_registry = dict(getattr(prior_state, "quest_registry", {}))
        for opp in update.quest_registry_add:
            if opp.id not in new_quest_registry:
                new_quest_registry[opp.id] = opp
        for quest_id in update.quest_registry_remove:
            new_quest_registry.pop(quest_id, None)
        for quest_id, new_status in update.quest_status_updates.items():
            existing = new_quest_registry.get(quest_id)
            if existing is not None:
                new_quest_registry[quest_id] = replace(existing, status=new_status)

        # Epic 5.3Aa: Apply faction updates to durable factions dict
        new_factions = dict(getattr(prior_state, "factions", {}))
        for fu in update.faction_updates:
            if fu.is_noop():
                continue
            existing = new_factions.get(fu.faction_id)
            if existing is None:
                existing = FactionState(faction_id=fu.faction_id)
            new_tension = existing.tension_level + fu.tension_delta
            new_ms = fu.military_strength_set if fu.military_strength_set is not None else existing.military_strength
            new_territory = (set(existing.territory) | set(fu.territory_add)) - set(fu.territory_remove)
            new_resources = dict(existing.resources)
            for k, v in fu.resources_delta.items():
                new_resources[k] = new_resources.get(k, 0) + v
            new_relations = {**existing.diplomatic_relations, **fu.diplomatic_relations_set}
            new_doctrines = fu.active_doctrines_set if fu.active_doctrines_set is not None else existing.active_doctrines
            new_factions[fu.faction_id] = replace(existing,
                tension_level=max(0.0, min(1.0, new_tension)),
                military_strength=new_ms,
                territory=tuple(sorted(new_territory)),
                resources=new_resources,
                diplomatic_relations=new_relations,
                active_doctrines=new_doctrines,
            )

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
            movement_count=new_movement_count,
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
            world_indexes=getattr(prior_state, "world_indexes", None),
            _index_hits=getattr(prior_state, "_index_hits", 0),
            _index_misses=getattr(prior_state, "_index_misses", 0),
            _opt_profile=getattr(prior_state, "_opt_profile", None),
            _force_full_scan=getattr(prior_state, "_force_full_scan", False),
            recent_world_events=new_recent_world_events,
            quest_registry=new_quest_registry,
            factions=new_factions,
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
        from src.engine.patches import extract_patches
        patches = extract_patches(entity.id, update)
        for patch in patches:
            patch.apply(entity, changes)

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
        object.__setattr__(res, "self_model", changes.get("self_model", getattr(entity, "self_model", None)))
        object.__setattr__(res, "cognition", changes.get("cognition", getattr(entity, "cognition", None)))

        
        timeline = getattr(entity, "timeline", None)
        if timeline is None:
            from collections import deque
            timeline = deque(maxlen=200)
        object.__setattr__(res, "timeline", timeline)
        
        # Clear transient caches
        object.__setattr__(res, "_readonly_cache", res)
        object.__setattr__(res, "_spatial_grid_cache", None)
        object.__setattr__(res, "_canonical_cache", None)
        return res
