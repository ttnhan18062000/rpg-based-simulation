from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Set, Tuple
from dataclasses import replace

from src.core.updates import EntityUpdate, IdentityUpdate, CombatUpdate, BiologicalUpdate

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState
    from src.core.updates import StateUpdate


class TownResolutionSystem:
    """
    Authoritative handler for town territory resolution.
    """

    @staticmethod
    def resolve(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Detect entities in town and apply general passive laws (Healing).
        """
        refined_entity_updates = dict(update.entity_updates)
        
        # Town Configuration Constants (Parity with config.py)
        PASSIVE_HEAL_AMT = 1 # town_passive_heal
        
        # Phase 9 Fix: Deterministic entity iteration
        for e_id in sorted(list(state.entities.keys())):
            entity = state.entities[e_id]
            pos = entity.navigation.position
            ent_upd = refined_entity_updates.get(e_id)
            if ent_upd and ent_upd.new_position:
                pos = ent_upd.new_position
            
            tile_pos = (int(pos[0]), int(pos[1]))
            building_type = state.building_tiles.get(tile_pos)
            
            # 1. Passive Healing Law (Always active in town)
            # VERIFIED v2: town_return_semantics
            if tile_pos in state.town_tiles:
                current_hp = entity.combat.hp
                max_hp = entity.combat.max_hp
                
                if current_hp < max_hp:
                    existing_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
                    combat_upd = existing_upd.combat or CombatUpdate()
                    new_combat_upd = replace(combat_upd, hp_delta=combat_upd.hp_delta + PASSIVE_HEAL_AMT)
                    
                    refined_entity_updates[e_id] = replace(
                        existing_upd,
                        combat=new_combat_upd
                    )

            # 2. Explicit REST Intent (Only in INN/HOME)
            # VERIFIED v2: inn_visit_semantics
            if building_type in ("inn", "home"):
                ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
                if ent_upd.task and ent_upd.task.work_kind_set == "ENTITY_ACT" and ent_upd.task.payload_set.get("action") == "REST":
                    # REST gives 5x passive heal and restores readiness
                    # Cost: 10 gold (LEG-RPG-001)
                    REST_HEAL_BONUS = 5
                    REST_SLEEP_RECOVERY = -5.0
                    REST_COST = 10
                    
                    # Check building functionality (LEG-RPG-001/006)
                    building = next((b for b in state.buildings.values() if b.position == tile_pos and b.kind == building_type), None)
                    if building and not building.functional:
                        continue

                    combat_upd = ent_upd.combat or CombatUpdate()
                    new_combat_upd = replace(combat_upd, hp_delta=combat_upd.hp_delta + REST_HEAL_BONUS)
                    
                    biological_upd = ent_upd.biological or BiologicalUpdate()
                    new_bio_upd = replace(biological_upd, sleep_debt_delta=biological_upd.sleep_debt_delta + REST_SLEEP_RECOVERY)
                    
                    from src.core.updates import ResourceTransferIntent
                    intent = ResourceTransferIntent(
                        source_id=building_type.upper(),
                        source_kind="TOWN_SERVICE",
                        gold_delta=-REST_COST,
                        transfer_kind="REST",
                        is_group_required=True
                    )
                    
                    refined_entity_updates[e_id] = replace(
                        ent_upd,
                        combat=new_combat_upd,
                        readiness_delta=ent_upd.readiness_delta + 10.0,
                        biological=new_bio_upd,
                        resource_transfers=list(ent_upd.resource_transfers) + [intent]
                    )

            # 3. Explicit EAT Intent (Only in TAVERN)
            if building_type == "tavern":
                ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
                if ent_upd.task and ent_upd.task.work_kind_set == "ENTITY_ACT" and ent_upd.task.payload_set.get("action") == "EAT":
                    # EAT restores hunger
                    # Cost: 5 gold (LEG-RPG-001)
                    EAT_HUNGER_RECOVERY = -20.0
                    EAT_COST = 5
                    
                    # Check building functionality
                    building = next((b for b in state.buildings.values() if b.position == tile_pos and b.kind == "tavern"), None)
                    if building and not building.functional:
                        continue

                    biological_upd = ent_upd.biological or BiologicalUpdate()
                    new_bio_upd = replace(biological_upd, hunger_delta=biological_upd.hunger_delta + EAT_HUNGER_RECOVERY)
                    
                    from src.core.updates import ResourceTransferIntent
                    intent = ResourceTransferIntent(
                        source_id="TAVERN",
                        source_kind="TOWN_SERVICE",
                        gold_delta=-EAT_COST,
                        transfer_kind="EAT",
                        is_group_required=True
                    )
                    
                    refined_entity_updates[e_id] = replace(
                        ent_upd,
                        biological=new_bio_upd,
                        resource_transfers=list(ent_upd.resource_transfers) + [intent]
                    )

            # 4. Explicit GUILD Intent (Intel and Quests)
            # VERIFIED v2: guild_visit_semantics
            if building_type == "guild":
                ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
                if ent_upd.task and ent_upd.task.work_kind_set == "ENTITY_ACT" and ent_upd.task.payload_set.get("action") == "GATHER_INTEL":
                    # Guild visits produce strategic leads
                    from src.core.strategic import StrategicLead, LeadKind
                    from src.core.updates import StrategicUpdate
                    new_lead = StrategicLead(
                        id=f"lead_intel_{state.tick}_{e_id}",
                        kind=LeadKind.RESOURCE,
                        subject="Rare Herb Patch",
                        confidence=0.7,
                        location=(50, 50) # Example location
                    )
                    
                    strat_upd = ent_upd.strategic or StrategicUpdate()
                    refined_entity_updates[e_id] = replace(
                        ent_upd,
                        strategic=replace(strat_upd, leads_add_or_update=[new_lead])
                    )

        # 4. Global Territorial Laws (Taxes and Suppression)
        from src.engine.legality import LegalityServiceV2
        
        new_resource_updates = dict(update.resource_updates)
        
        # Phase 9 Fix: Deterministic entity iteration
        for e_id in sorted(list(state.entities.keys())):
            entity = state.entities[e_id]
            if not entity.lifecycle.active: continue
            
            pos = entity.navigation.position
            ent_upd = refined_entity_updates.get(e_id)
            if ent_upd and ent_upd.new_position:
                pos = ent_upd.new_position
            
            region = LegalityServiceV2.get_region_for_position(pos, state)
            if not region: continue
            
            # A. Territorial Taxes (Milestone 4: Every 10 ticks)
            if state.tick % 10 == 0 and region.owner_faction_id is not None:
                if entity.identity.faction != region.owner_faction_id:
                    TAX_AMT = 2.0
                    # Only tax if they have gold
                    tax_to_pay = min(entity.inventory.gold, TAX_AMT)
                    if tax_to_pay > 0:
                        from src.core.updates import ResourceTransferIntent
                        intent = ResourceTransferIntent(
                            source_id=f"tax_{region.id}",
                            source_kind="TAX",
                            gold_delta=-tax_to_pay,
                            transfer_kind="TAX"
                        )
                        
                        ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
                        refined_entity_updates[e_id] = replace(ent_upd,
                            resource_transfers=list(ent_upd.resource_transfers) + [intent]
                        )
                        
                        # Accumulate in faction gold via resource_updates
                        f_key = f"faction_{region.owner_faction_id}_gold"
                        new_resource_updates[f_key] = new_resource_updates.get(f_key, 0.0) + tax_to_pay

            # B. Regional Suppression Debuffs (Milestone 4)
            if region.suppression_active and entity.identity.faction != region.owner_faction_id:
                ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
                cb_upd = ent_upd.combat or CombatUpdate()
                # 0.8x Atk/Def, 0.9x Speed
                atk_penalty = entity.combat.atk * (0.8 - 1.0)
                def_penalty = entity.combat.def_stat * (0.8 - 1.0)
                spd_penalty = entity.combat.speed * (0.9 - 1.0)
                
                refined_entity_updates[e_id] = replace(ent_upd,
                    combat=replace(cb_upd,
                        atk_delta=cb_upd.atk_delta + atk_penalty,
                        def_delta=cb_upd.def_delta + def_penalty,
                        speed_delta=cb_upd.speed_delta + spd_penalty
                    )
                )

        # C. Building Taxation (Milestone 4: Every 10 ticks)
        if state.tick % 10 == 0:
            for b_id, building in state.buildings.items():
                if building.functional:
                    region = LegalityServiceV2.get_region_for_position(building.position, state)
                    if region and region.owner_faction_id is not None:
                        BUILD_TAX = 10.0
                        f_key = f"faction_{region.owner_faction_id}_gold"
                        new_resource_updates[f_key] = new_resource_updates.get(f_key, 0.0) + BUILD_TAX

        return replace(update, 
            entity_updates=refined_entity_updates,
            resource_updates=new_resource_updates
        )
