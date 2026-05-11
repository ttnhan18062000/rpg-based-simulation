# Compliance IDs: TOWN-015, TOWN-018, TOWN-019
from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Set, Tuple
from dataclasses import replace

from src.core.updates import EntityUpdate, IdentityUpdate, CombatUpdate, BiologicalUpdate

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState
    from src.core.updates import StateUpdate
    from src.engine.cadence import SystemCadence


class TownResolutionSystem:
    """
    Authoritative handler for town territory resolution.
    """

    @staticmethod
    def resolve(state: AuthoritativeState, update: StateUpdate, cadence: SystemCadence | None = None) -> StateUpdate:
        """
        Detect entities in town and apply general passive laws (Healing).
        Optimized v2: skip redundant loops if no town/regions exist.
        """
        from src.engine.cadence import SystemCadence as DefaultCadence
        cadence = cadence or DefaultCadence()
        
        refined_entity_updates = dict(update.entity_updates)
        new_resource_updates = dict(update.resource_updates)
        
        # 1. Early exits
        has_town = len(state.town_tiles) > 0
        has_regions = len(state.regions) > 0
        
        if not has_town and not has_regions:
            return update

        # 1. Indexing & Constants
        PASSIVE_HEAL_AMT = 1
        from src.engine.spatial_query import SpatialQueryService
        region_list = list(state.regions.values())
        
        # Only check regions if any have owners or suppression
        regions_with_effects = [r for r in region_list if r.owner_faction_id is not None or r.suppression_active]
        has_regional_effects = len(regions_with_effects) > 0

        # Taxes happen at the town_resolution cadence (or a multiple of it)
        is_tax_tick = (state.tick % (cadence.town_resolution * 2) == 0)

        # 2. Iteration
        # Phase A: Town-specific logic (Passive Healing, Services)
        # Optimization: Only process entities currently in town
        # Logic ID: PERF-006 (Dirty Entity Tracking)
        town_ids = update.dirty_set.town_entities if update.dirty_set else state.entities.keys()
        
        for e_id in town_ids:
            entity = state.entities.get(e_id)
            if not entity or not entity.lifecycle.active:
                continue

            ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
            pos = entity.navigation.position
            if ent_upd.new_position:
                pos = ent_upd.new_position
            
            tile_pos = (int(pos[0]), int(pos[1]))
            
            # --- Part A: Town & Building Logic ---
            if tile_pos in state.town_tiles:
                current_hp = entity.combat.hp
                if current_hp < entity.combat.max_hp:
                    combat_upd = ent_upd.combat or CombatUpdate()
                    refined_entity_updates[e_id] = replace(
                        ent_upd,
                        combat=replace(combat_upd, hp_delta=combat_upd.hp_delta + PASSIVE_HEAL_AMT)
                    )
                    ent_upd = refined_entity_updates[e_id]

                building_type = state.building_tiles.get(tile_pos)
                if building_type and ent_upd and ent_upd.task and ent_upd.task.work_kind_set == "ENTITY_ACT":
                    action = ent_upd.task.payload_set.get("action")
                    
                    if building_type in ("inn", "home") and action == "REST":
                        building = SpatialQueryService.get_building_at(state, tile_pos)
                        if building and building.functional:
                            combat_upd = ent_upd.combat or CombatUpdate()
                            bio_upd = ent_upd.biological or BiologicalUpdate()
                            from src.core.updates import ResourceTransferIntent
                            intent = ResourceTransferIntent(
                                source_id=building_type.upper(),
                                source_kind="TOWN_SERVICE",
                                gold_delta=-10,
                                transfer_kind="REST",
                                is_group_required=True
                            )
                            refined_entity_updates[e_id] = replace(
                                ent_upd,
                                combat=replace(combat_upd, hp_delta=combat_upd.hp_delta + 5),
                                readiness_delta=ent_upd.readiness_delta + 10.0,
                                biological=replace(bio_upd, sleep_debt_delta=bio_upd.sleep_debt_delta - 5.0),
                                resource_transfers=list(ent_upd.resource_transfers) + [intent]
                            )
                            ent_upd = refined_entity_updates[e_id]

                    elif building_type == "tavern" and action == "EAT":
                        building = SpatialQueryService.get_building_at(state, tile_pos)
                        if building and building.functional:
                            bio_upd = ent_upd.biological or BiologicalUpdate()
                            from src.core.updates import ResourceTransferIntent
                            intent = ResourceTransferIntent(
                                source_id="TAVERN",
                                source_kind="TOWN_SERVICE",
                                gold_delta=-5,
                                transfer_kind="EAT",
                                is_group_required=True
                            )
                            refined_entity_updates[e_id] = replace(
                                ent_upd,
                                biological=replace(bio_upd, hunger_delta=bio_upd.hunger_delta - 20.0),
                                resource_transfers=list(ent_upd.resource_transfers) + [intent]
                            )
                            ent_upd = refined_entity_updates[e_id]

                    elif building_type == "guild" and action == "GATHER_INTEL":
                        from src.core.strategic import StrategicLead, LeadKind
                        from src.core.updates import StrategicUpdate
                        new_lead = StrategicLead(
                            id=f"lead_intel_{state.tick}_{e_id}",
                            kind=LeadKind.RESOURCE,
                            subject="Rare Herb Patch",
                            confidence=0.7,
                            location=(50, 50)
                        )
                        strat_upd = ent_upd.strategic or StrategicUpdate()
                        refined_entity_updates[e_id] = replace(
                            ent_upd,
                            strategic=replace(strat_upd, leads_add_or_update=[new_lead])
                        )
                        ent_upd = refined_entity_updates[e_id]
        
        # Phase B: Regional Logic (Taxes, Suppression)
        # Optimization: Only process entities that are dirty (moved or combat-dirty)
        # Since regional effects mostly impact stats or taxes.
        if has_regional_effects:
            # Optimization: Start with dirty entities (movers/combatants)
            regional_candidates = set(update.dirty_set.movement_entities | update.dirty_set.combat_entities if update.dirty_set else state.entities.keys())
            
            # Correction: Passive suppression must apply to everyone in the region,
            # even if they didn't move or fight this tick.
            for region in regions_with_effects:
                if region.suppression_active:
                    regional_candidates.update(SpatialQueryService.get_entities_in_bounds(state, region.bounds))
            
            for e_id in regional_candidates:
                entity = state.entities.get(e_id)
                if not entity or not entity.lifecycle.active:
                    continue
                
                ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
                pos = entity.navigation.position
                if ent_upd.new_position:
                    pos = ent_upd.new_position
                
                region = None
                for r in regions_with_effects:
                    x_min, y_min, x_max, y_max = r.bounds
                    if x_min <= pos[0] <= x_max and y_min <= pos[1] <= y_max:
                        region = r
                        break
                
                if region:
                    if is_tax_tick and region.owner_faction_id is not None:
                        if entity.identity.faction != region.owner_faction_id:
                            tax_to_pay = min(entity.inventory.gold, 2.0)
                            if tax_to_pay > 0:
                                from src.core.updates import ResourceTransferIntent
                                intent = ResourceTransferIntent(
                                    source_id=f"tax_{region.id}",
                                    source_kind="TAX",
                                    gold_delta=-tax_to_pay,
                                    transfer_kind="TAX"
                                )
                                refined_entity_updates[e_id] = replace(ent_upd,
                                    resource_transfers=list(ent_upd.resource_transfers) + [intent]
                                )
                                ent_upd = refined_entity_updates[e_id]
                                
                                f_key = f"faction_{region.owner_faction_id}_gold"
                                new_resource_updates[f_key] = new_resource_updates.get(f_key, 0.0) + tax_to_pay

                    if region.suppression_active and entity.identity.faction != region.owner_faction_id:
                        cb_upd = ent_upd.combat or CombatUpdate()
                        refined_entity_updates[e_id] = replace(ent_upd,
                            combat=replace(cb_upd,
                                atk_delta=cb_upd.atk_delta + (entity.combat.atk * -0.2),
                                def_delta=cb_upd.def_delta + (entity.combat.def_stat * -0.2),
                                speed_delta=cb_upd.speed_delta + (entity.combat.speed * -0.1)
                            )
                        )

        # --- Part C: Building Taxation ---
        if is_tax_tick and has_regional_effects:
            for building in state.buildings.values():
                if building.functional:
                    region = None
                    for r in regions_with_effects:
                        x_min, y_min, x_max, y_max = r.bounds
                        if x_min <= building.position[0] <= x_max and y_min <= building.position[1] <= y_max:
                            region = r
                            break
                    if region and region.owner_faction_id is not None:
                        f_key = f"faction_{region.owner_faction_id}_gold"
                        new_resource_updates[f_key] = new_resource_updates.get(f_key, 0.0) + 10.0

        return replace(update, 
            entity_updates=refined_entity_updates,
            resource_updates=new_resource_updates
        )
