# Compliance IDs: TOWN-015, TOWN-018, TOWN-019
from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Set, Tuple, List
from dataclasses import replace

from src.core.updates import EntityUpdate, IdentityUpdate, CombatUpdate, BiologicalUpdate
from src.core.enums import Faction

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState
    from src.core.updates import StateUpdate
    from src.engine.cadence import SystemCadence


class TownResolutionSystem:
    """
    Authoritative handler for town territory resolution.
    Optimized v2: Uses spatial indexing and caches to avoid O(N*M) bottlenecks.
    """

    @staticmethod
    def resolve(state: AuthoritativeState, update: StateUpdate, cadence: SystemCadence | None = None) -> StateUpdate:
        """
        Detect entities in town and apply general passive laws (Healing).
        Also handles regional taxation and maintenance.
        """
        from src.engine.cadence import SystemCadence as DefaultCadence
        from src.engine.spatial_query import SpatialQueryService
        from src.core.updates import ResourceTransferIntent, BuildingUpdate
        
        cadence = cadence or DefaultCadence()
        
        refined_entity_updates = dict(update.entity_updates)
        new_resource_updates = dict(update.resource_updates)
        refined_building_updates = dict(update.building_updates)
        
        # 1. Early exits
        has_town = len(state.town_tiles) > 0
        has_regions = len(state.regions) > 0
        
        if not has_town and not has_regions:
            return update

        # 2. Constants & Caches
        PASSIVE_HEAL_AMT = 1
        is_tax_tick = (state.tick % (cadence.town_resolution * 2) == 0)
        
        # Pre-cache faction keys for faster resource lookup
        faction_keys = {f: f"faction_{f.name.lower()}_gold" for f in Faction}
        
        # Pre-filter regions with effects
        regions_with_effects = [r for r in state.regions.values() if r.owner_faction_id is not None or r.suppression_active]
        has_regional_effects = len(regions_with_effects) > 0

        # 3. Entity Loop (Town & Regional Effects)
        # Optimization: Only process entities currently in town OR affected by regions
        # If it's a tax tick, we must check everyone in regions.
        from src.core.dirty import get_relevant_entity_ids
        if not is_tax_tick:
            candidate_ids = get_relevant_entity_ids(state, update, "town")
        else:
            candidate_ids = state.entities.keys()
        
        for e_id in candidate_ids:
            entity = state.entities.get(e_id)
            if not entity or not entity.combat.alive or not entity.lifecycle.active:
                continue

            ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
            pos = entity.navigation.position
            if ent_upd.new_position:
                pos = ent_upd.new_position
            
            # --- Part A: Town Logic (Healing, Services) ---
            tile_pos = (int(pos[0]), int(pos[1]))
            if tile_pos in state.town_tiles:
                # Healing
                if entity.combat.hp < entity.combat.max_hp:
                    cb_upd = ent_upd.combat or CombatUpdate()
                    ent_upd = replace(ent_upd, combat=replace(cb_upd, hp_delta=cb_upd.hp_delta + PASSIVE_HEAL_AMT))
                    refined_entity_updates[e_id] = ent_upd

                # Building Services (Rest, Eat)
                building_type = state.building_tiles.get(tile_pos)
                if building_type and ent_upd.task and ent_upd.task.work_kind_set == "ENTITY_ACT":
                    action = ent_upd.task.payload_set.get("action")
                    if action in ("REST", "EAT", "GATHER_INTEL"):
                        building = SpatialQueryService.get_building_at(state, tile_pos)
                        if building and building.functional:
                            if action == "REST" and building_type in ("inn", "home"):
                                cb_upd = ent_upd.combat or CombatUpdate()
                                bio_upd = ent_upd.biological or BiologicalUpdate()
                                intent = ResourceTransferIntent(source_id=building_type.upper(), source_kind="TOWN_SERVICE", gold_delta=-10, transfer_kind="REST", is_group_required=True)
                                ent_upd = replace(ent_upd,
                                    combat=replace(cb_upd, hp_delta=cb_upd.hp_delta + 5),
                                    readiness_delta=ent_upd.readiness_delta + 10.0,
                                    biological=replace(bio_upd, sleep_debt_delta=bio_upd.sleep_debt_delta - 5.0),
                                    resource_transfers=list(ent_upd.resource_transfers) + [intent]
                                )
                                refined_entity_updates[e_id] = ent_upd
                            elif action == "EAT" and building_type == "tavern":
                                bio_upd = ent_upd.biological or BiologicalUpdate()
                                intent = ResourceTransferIntent(source_id="TAVERN", source_kind="TOWN_SERVICE", gold_delta=-5, transfer_kind="EAT", is_group_required=True)
                                ent_upd = replace(ent_upd,
                                    biological=replace(bio_upd, hunger_delta=bio_upd.hunger_delta - 20.0),
                                    resource_transfers=list(ent_upd.resource_transfers) + [intent]
                                )
                                refined_entity_updates[e_id] = ent_upd

            # --- Part B: Regional Effects (Tax, Suppression) ---
            if has_regional_effects:
                region = SpatialQueryService.get_region_at(state, pos)
                if region:
                    # Taxation
                    if is_tax_tick and region.owner_faction_id is not None:
                        if entity.identity.faction != region.owner_faction_id:
                            tax_to_pay = min(entity.inventory.gold, 2.0)
                            if tax_to_pay > 0:
                                intent = ResourceTransferIntent(source_id=f"tax_{region.id}", source_kind="TAX", gold_delta=-tax_to_pay, transfer_kind="TAX")
                                ent_upd = replace(ent_upd, resource_transfers=list(ent_upd.resource_transfers) + [intent])
                                refined_entity_updates[e_id] = ent_upd
                                
                                f_key = faction_keys[region.owner_faction_id]
                                new_resource_updates[f_key] = new_resource_updates.get(f_key, 0.0) + tax_to_pay

                    # Suppression
                    if region.suppression_active and entity.identity.faction != region.owner_faction_id:
                        cb_upd = ent_upd.combat or CombatUpdate()
                        ent_upd = replace(ent_upd,
                            combat=replace(cb_upd,
                                atk_delta=cb_upd.atk_delta + (entity.combat.atk * -0.2),
                                def_delta=cb_upd.def_delta + (entity.combat.def_stat * -0.2),
                                speed_delta=cb_upd.speed_delta + (entity.combat.speed * -0.1)
                            )
                        )
                        refined_entity_updates[e_id] = ent_upd

        # 4. Building Taxation & Maintenance
        if is_tax_tick:
            # Building Taxes
            for building in state.buildings.values():
                if building.functional:
                    region = SpatialQueryService.get_building_region(state, building.id)
                    if region and region.owner_faction_id is not None:
                        f_key = faction_keys[region.owner_faction_id]
                        new_resource_updates[f_key] = new_resource_updates.get(f_key, 0.0) + 10.0
            
            # Building Maintenance
            MAINTENANCE_COST = 5.0
            faction_maintenance: Dict[Faction, float] = {}
            faction_buildings: Dict[Faction, List[int]] = {}
            
            for b_id, building in state.buildings.items():
                if not building.functional: continue
                region = SpatialQueryService.get_building_region(state, b_id)
                if region and region.owner_faction_id is not None:
                    fid = region.owner_faction_id
                    faction_maintenance[fid] = faction_maintenance.get(fid, 0.0) + MAINTENANCE_COST
                    faction_buildings.setdefault(fid, []).append(b_id)
            
            # Apply Maintenance
            for fid, total_cost in faction_maintenance.items():
                f_key = faction_keys[fid]
                current_vault = state.global_resources.get(f_key, 0.0) + new_resource_updates.get(f_key, 0.0)
                
                if current_vault >= total_cost:
                    new_resource_updates[f_key] = new_resource_updates.get(f_key, 0.0) - total_cost
                else:
                    # Insolvency: Disable buildings
                    for b_id in faction_buildings[fid]:
                        b_upd = refined_building_updates.get(b_id, BuildingUpdate(building_id=b_id))
                        refined_building_updates[b_id] = replace(b_upd, functional_set=False)

        return replace(update, 
            entity_updates=refined_entity_updates,
            resource_updates=new_resource_updates,
            building_updates=refined_building_updates
        )
